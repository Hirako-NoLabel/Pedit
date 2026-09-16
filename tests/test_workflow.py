import io
import json
from pathlib import Path
from urllib.error import HTTPError

import numpy as np
import pymupdf as fitz
import pytest
from PIL import Image

from pedit import __version__, app
from pedit.high_fidelity import analyze_edit, apply_stream_edit


def imported(api, samples):
    return api('/api/open', samples.electronic_bytes())['id']


def edit_for(api, sid):
    data = api(f'/api/page-data?id={sid}&page=0')
    item = next(x for x in data['text'] if x['text'] == '123')
    return {**item, 'type': 'text', 'page': 0, 'oldText': '123', 'newText': '456',
            'sameStyle': True, 'engine': 'electronic'}


def test_import_and_static_resources(api, samples):
    result = api('/api/open', samples.electronic_bytes())
    assert result['ok'] and result['pageCount'] == 1
    assert api('/api/health')['version'] == __version__
    assert b'Pedit OSS' in api('/', raw=True)
    assert b'progressPayload' in api('/app.js', raw=True)
    assert len(api('/styles.css', raw=True)) > 100


def test_render_has_expected_size_and_ink(api, samples):
    sid = imported(api, samples)
    image = Image.open(io.BytesIO(api(f'/api/page?id={sid}&page=0&scale=2', raw=True)))
    assert image.size == (840, 600)
    pixels = np.asarray(image)
    assert pixels.min() < 80 and pixels.max() == 255


def test_replacement_preview_export_preserves_other_content(api, samples):
    sid = imported(api, samples)
    edit = edit_for(api, sid)
    before = api(f'/api/page?id={sid}&page=0&scale=2', raw=True)
    preview = api('/api/preview', {'id': sid, 'page': 0, 'scale': 2, 'edits': [edit]}, raw=True)
    output = api('/api/export', {'id': sid, 'edits': [edit]}, raw=True)
    assert preview != before
    with fitz.open(stream=output, filetype='pdf') as doc:
        text = doc[0].get_text()
        assert '\n123\n' not in text
        # Document-glyph reuse can split the PDF text objects. Read the actual
        # target-region characters in spatial order instead of stream order.
        blocks = doc[0].get_text('rawdict', clip=fitz.Rect(edit['bbox']))['blocks']
        chars = [char for block in blocks if 'lines' in block for line in block['lines']
                 for span in line['spans'] for char in span['chars']]
        assert ''.join(c['c'] for c in sorted(chars, key=lambda c: c['bbox'][0])) == '456'
        assert 'TEST-A' in text
        assert doc.page_count == 1
        assert app.render_page(doc, 0, 2) == preview
    a = np.asarray(Image.open(io.BytesIO(before)))
    b = np.asarray(Image.open(io.BytesIO(preview)))
    changed = np.any(a != b, axis=2)
    ys, xs = np.where(changed)
    assert len(xs) > 0
    x0, y0, x1, y1 = edit['bbox']
    assert xs.min() >= int(x0*2)-2 and xs.max() <= int(x1*2)+2
    assert ys.min() >= int(y0*2)-2 and ys.max() <= int(y1*2)+2


def test_stream_replacement_matches_native_pixels():
    with fitz.open() as doc:
        for text in ('123', '456'):
            page = doc.new_page(width=200, height=100)
            page.insert_text((30, 65), text, fontsize=28)
        span = app.page_data(doc, 0)['text'][0]
        edit = {**span, 'type': 'text', 'page': 0, 'oldText': '123', 'newText': '456', 'sameStyle': True}
        assert analyze_edit(doc, edit)['mode'] == 'stream'
        assert apply_stream_edit(doc, edit)[0]
        assert doc[0].get_pixmap().samples == doc[1].get_pixmap().samples


def test_session_survives_memory_reset_and_baseline_commit(api, samples):
    sid = imported(api, samples)
    edit = edit_for(api, sid)
    state = {'schemaVersion': 1, 'currentPage': 0, 'edits': [['edit-1', edit]],
             'pageNumberTemplates': {'A': {'slot': 'A'}}, 'versionHistory': [],
             'pageNumberManualTakeovers': ['0:A'], 'previewQuality': 'high'}
    assert api('/api/save-progress', {'id': sid, 'state': state})['ok']
    stored = json.loads((app.WORKDIR / sid / 'editor_progress.json').read_text(encoding='utf-8'))
    assert stored['version'] == __version__ and stored['state'] == state
    app.SESSIONS.clear()
    assert api(f'/api/resume-progress?id={sid}')['progress'] == state
    committed = api('/api/commit-baseline', {'id': sid, 'edits': [edit]})
    assert committed['baselineId'] == 1
    state['edits'] = []
    state['baselineId'] = 1
    api('/api/save-progress', {'id': sid, 'state': state})
    app.SESSIONS.clear()
    assert api(f'/api/resume-progress?id={sid}')['baselineId'] == 1
    assert Path(app.get_session(sid)['path']).name == 'baseline_1.pdf'
    assert api('/api/baseline/restore', {'id': sid, 'baselineId': 0})['baselineId'] == 0


def test_invalid_pdf_is_rejected(api):
    with pytest.raises(HTTPError) as error:
        api('/api/open', b'not a PDF')
    assert error.value.code == 400


def test_invalid_page_and_session_are_rejected(api, samples):
    sid = imported(api, samples)
    for path in (f'/api/page?id={sid}&page=999', '/api/resume-progress?id=invalid'):
        with pytest.raises(HTTPError) as error:
            api(path)
        assert error.value.code == 404


def test_static_path_cannot_escape_to_sibling(api, tmp_path, monkeypatch):
    static = tmp_path / 'static'
    static.mkdir()
    sibling = tmp_path / 'static-private'
    sibling.mkdir()
    (sibling / 'record.txt').write_text('private synthetic marker')
    monkeypatch.setattr(app, 'STATIC', static)
    with pytest.raises(HTTPError) as error:
        api('/../static-private/record.txt', raw=True)
    assert error.value.code == 404
