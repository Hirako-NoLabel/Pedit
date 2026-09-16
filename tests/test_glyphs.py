import base64
import io
import json

import numpy as np
import pymupdf as fitz
import pytest
from PIL import Image

from pedit import app, scan_revision_visual as srv
from pedit.scan_diff import _expand_same_length_stable_ranges


def pixels(url):
    return np.asarray(Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA'))


def setup_scan(samples, tmp_path):
    raw, regions = samples.scanned_bytes()
    path = tmp_path / 'scan.pdf'
    path.write_bytes(raw)
    srv._PATCH_CACHE.clear()
    return path, raw, regions


def test_scan_import_and_render_without_ocr(api, samples):
    raw, _ = samples.scanned_bytes()
    result = api('/api/open', raw)
    assert result['ok'] and result['pageCount'] == 1
    with fitz.open(stream=raw, filetype='pdf') as doc:
        assert doc[0].get_text() == ''
    assert api(f"/api/page?id={result['id']}&page=0", raw=True).startswith(b'\x89PNG')


def test_glyph_asset_save_load_and_exact_reuse(api, samples, tmp_path):
    path, raw, regions = setup_scan(samples, tmp_path)
    target = {'bbox': regions[0]['chars'][0]['bbox']}
    donor = {'bbox': regions[1]['chars'][0]['bbox'], 'text': '4'}
    asset = srv._same_page_fragment_asset(str(path), 0, donor, 4)
    assert asset['pixelReuse'] == 'fragment-1to1-rgba'
    sid = api('/api/open', raw)['id']
    state = {'schemaVersion': 1, 'glyphLibrary': [['4', {'documentId': sid, 'asset': asset}]],
             'blockLibrary': [], 'edits': []}
    api('/api/save-progress', {'id': sid, 'state': state})
    app.SESSIONS.clear()
    restored = api(f'/api/resume-progress?id={sid}')['progress']
    recovered = restored['glyphLibrary'][0][1]['asset']
    assert recovered == json.loads(json.dumps(asset))
    assert np.array_equal(pixels(recovered['rgbaDataUrl']), pixels(asset['rgbaDataUrl']))
    patch = srv._build_local_patch(str(path), 0, target['bbox'], '1', '4',
                                  glyph_bbox=target['bbox'], glyph_old='1', glyph_new='4',
                                  scale=4, reusable_glyph=recovered)
    metrics = patch['metrics']
    assert metrics['reusedFinishedGlyph'] is True
    assert metrics['reuseResampled'] is False
    assert metrics['reusePlacement'] == 'source-cell-anchor'
    assert np.array_equal(pixels(metrics['reusableGlyph']['rgbaDataUrl']), pixels(asset['rgbaDataUrl']))
    assert metrics['changed_pixel_count'] > 0
    assert metrics['preservationViolationPixels'] == 0


def test_original_glyph_rejects_scale_mismatch(samples, tmp_path):
    path, _, regions = setup_scan(samples, tmp_path)
    asset = srv._same_page_fragment_asset(str(path), 0, regions[1], 4)
    asset['sourceScale'] = 3
    with pytest.raises(ValueError, match='1:1'):
        srv._build_local_patch(str(path), 0, regions[0]['bbox'], '123', '456',
                               scale=4, reusable_glyph=asset)


def test_whole_fragment_patch_preserves_donor_geometry(samples, tmp_path):
    path, _, regions = setup_scan(samples, tmp_path)
    target, donor = regions
    asset = srv._same_page_fragment_asset(str(path), 0, donor, 4)
    patch = srv._build_local_patch(str(path), 0, target['bbox'], '123', '456',
                                  scale=4, reusable_glyph=asset)
    assert patch['metrics']['reuseResampled'] is False
    with fitz.open(path) as doc:
        page = doc[0]
        page.insert_image(fitz.Rect(patch['overlayBbox']), stream=patch['png'])
        rendered = np.frombuffer(page.get_pixmap(matrix=fitz.Matrix(4, 4)).samples,
                                 dtype=np.uint8).reshape(1200, 1680, 3)
    def crop(box):
        x0, y0, x1, y1 = [int(v*4) for v in box]
        return rendered[y0:y1, x0:x1]
    # RGBA assets are exact (tested above); compositing/inpainting the target
    # paper can change low-level RGB. Require identical ink geometry and a
    # small intensity difference rather than falsely claiming identical paper.
    actual, expected = crop(target['bbox']), crop(donor['bbox'])
    assert np.array_equal(actual.mean(axis=2) < 175, expected.mean(axis=2) < 175)
    assert np.abs(actual.astype(int) - expected.astype(int)).mean() < 0.2


def test_scan_replacement_exports_through_http(api, samples, tmp_path):
    path, raw, regions = setup_scan(samples, tmp_path)
    # Geometry refinement tightens the narrow '1'. Use the wider target for
    # this end-to-end success case so original-mode width protection remains on.
    donor, target = regions
    asset = srv._same_page_fragment_asset(str(path), 0, donor, 4)
    sid = api('/api/open', raw)['id']
    edit = {'id': 'test-edit', 'type': 'text', 'engine': 'scan', 'page': 0,
            'bbox': target['bbox'], 'tokenBbox': target['bbox'], 'oldText': '456',
            'newText': '123', 'chars': target['chars'], 'characterGeometry': True,
            'manualSelection': True, 'reusableGlyph': asset}
    output = api('/api/export', {'id': sid, 'edits': [edit]}, raw=True)
    with fitz.open(stream=raw, filetype='pdf') as before, fitz.open(stream=output, filetype='pdf') as after:
        assert after.page_count == before.page_count == 1
        old = np.frombuffer(before[0].get_pixmap(matrix=fitz.Matrix(4, 4)).samples, dtype=np.uint8).reshape(1200, 1680, 3)
        new = np.frombuffer(after[0].get_pixmap(matrix=fitz.Matrix(4, 4)).samples, dtype=np.uint8).reshape(1200, 1680, 3)
        changed = np.any(old != new, axis=2)
        ys, xs = np.where(changed)
        assert len(xs) > 0
        assert xs.min() >= 239*4 and xs.max() <= 298*4
        assert ys.min() >= 143*4 and ys.max() <= 174*4


@pytest.mark.parametrize('old,new,expected', [
    ('123', '456', [(0, 3, 0, 3)]),
    ('123', '123', []),
])
def test_stable_numeric_fragment_policy(old, new, expected):
    assert _expand_same_length_stable_ranges(old, new) == expected
