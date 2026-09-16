from __future__ import annotations

import base64
import io
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from .scan_diff import plan_changes, aligned_chars
from .scan_visual_match import fit_source

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

_RENDER_SCALE = 4.0  # fallback only; v2.3.27 resolves native scan scale per page
_PATCH_CACHE: dict[tuple, dict[str, Any]] = {}
_PAGE_CHAR_CACHE: dict[tuple, list[dict[str, Any]]] = {}


def _font_candidates(cjk: bool = False) -> list[str]:
    """Return system fonts only. No font files are bundled with the project."""
    home = str(Path.home())
    windows_fonts = Path(os.environ.get("WINDIR") or (Path.home().anchor + "Windows")) / "Fonts"
    if cjk:
        candidates = [
            str(windows_fonts / "simsun.ttc"),
            str(windows_fonts / "simfang.ttf"),
            str(windows_fonts / "msyh.ttc"),
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
    else:
        candidates = [
            str(windows_fonts / "segoeui.ttf"),
            str(windows_fonts / "arial.ttf"),
            str(windows_fonts / "calibri.ttf"),
            str(windows_fonts / "times.ttf"),
            str(windows_fonts / "timesbd.ttf"),
            str(windows_fonts / "cambria.ttc"),
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        ]
    if os.name == "nt":
        candidates.extend([
            str(Path(home) / "AppData/Local/Microsoft/Windows/Fonts/Times New Roman.ttf"),
        ])
    return [p for p in candidates if p and Path(p).exists()]


def _contains_cjk(text: str) -> bool:
    return any("\u3400" <= c <= "\u9fff" for c in str(text or ""))


def _page_reference_chars(pdf_path: str, page_no: int):
    stat=Path(pdf_path).stat()
    key=(str(Path(pdf_path).resolve()),int(page_no),stat.st_size,stat.st_mtime_ns)
    if key not in _PAGE_CHAR_CACHE:
        from .scan_engine import ocr_page
        _PAGE_CHAR_CACHE[key]=[
            char for line in ocr_page(pdf_path,page_no).get('text',[])
            for char in line.get('chars',[])
        ]
    return _PAGE_CHAR_CACHE[key]




def _digit_sample_metrics(arr, bbox, scale):
    """Measure one scanned digit from visible ink, not OCR cell width."""
    if np is None or cv2 is None or not bbox:
        return None
    x0,y0,x1,y1=[int(round(float(v)*scale)) for v in bbox]
    x0,y0=max(0,x0),max(0,y0);x1,y1=min(arr.shape[1],x1),min(arr.shape[0],y1)
    sample=arr[y0:y1,x0:x1]
    if sample.size==0:
        return None
    gray=cv2.cvtColor(sample,cv2.COLOR_RGB2GRAY).astype(float)
    background=float(np.percentile(gray,90))
    hard=gray<min(185.,background-30.)
    if not np.any(hard):
        return None
    count,labels,stats,_=cv2.connectedComponentsWithStats(hard.astype('uint8'),8)
    comps=[i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>=2]
    if not comps:
        return None
    largest=max(comps,key=lambda i:stats[i,cv2.CC_STAT_AREA])
    lx,ly,lw,lh,_=[int(v) for v in stats[largest]]
    core=np.zeros_like(hard,dtype=bool)
    for i in comps:
        x,y,w,h,area=[int(v) for v in stats[i]]
        if x<=lx+lw+2 and x+w>=lx-2 and y<=ly+lh+2 and y+h>=ly-2:
            core|=labels==i
    bounds=_mask_bbox(core.astype('uint8'))
    if not bounds:
        return None
    dark_vals=gray[core]
    cutoff=float(np.percentile(dark_vals,20))
    dark_core=core & (gray<=cutoff)
    pixels=sample[dark_core]
    rgb=np.median(pixels,axis=0) if len(pixels) else np.repeat(float(np.percentile(dark_vals,5)),3)
    dist=cv2.distanceTransform(core.astype('uint8'),cv2.DIST_L2,3)
    stroke=float(np.mean(dist[core])) if np.any(core) else 0.
    support=cv2.dilate(core.astype('uint8'),np.ones((3,3),np.uint8),iterations=1)>0
    transition=support & ~core & (gray<background-5.)
    softness=float(np.count_nonzero(transition)/max(1,np.count_nonzero(core)))
    bw=max(1,bounds[2]-bounds[0]);bh=max(1,bounds[3]-bounds[1])
    density=float(np.count_nonzero(core)/max(1,bw*bh))
    core_gray=float(np.median(gray[dark_core])) if np.any(dark_core) else float(np.percentile(dark_vals,15))
    contrast=max(0.0,background-core_gray)
    return {
        'inkWidthPx':int(bw),
        'inkHeightPx':int(bh),
        'foregroundRGB':[float(v) for v in rgb],
        'strokeMetric':stroke,
        'edgeSoftnessMetric':softness,
        'inkDensityMetric':density,
        'contrastMetric':contrast,
        'backgroundGray':background,
        'bbox':[float(v) for v in bbox],
    }


def _robust_digit_samples(candidates):
    """Drop obvious OCR/exposure outliers before building a row profile."""
    if len(candidates) <= 2:
        return list(candidates)
    heights=np.array([m['inkHeightPx'] for m in candidates],dtype=float)
    backgrounds=np.array([m['backgroundGray'] for m in candidates],dtype=float)
    mh=float(np.median(heights)); mb=float(np.median(backgrounds))
    kept=[m for m in candidates
          if .78 <= m['inkHeightPx']/max(1.,mh) <= 1.22
          and abs(m['backgroundGray']-mb) <= 28.]
    return kept or list(candidates)


def _line_digit_style_profile(pdf_path, page_no, chars, display_bbox, scale, base_style=None):
    """Build one stable, local digit style for the target row.

    Geometry uses robust same-row medians. Exposure/edge characteristics prefer
    the nearest reliable digits, so a distant field on the same row cannot make
    the replacement suddenly lighter or softer.
    """
    if np is None or cv2 is None:
        return deepcopy(base_style) if base_style else None
    arr,_=_render_page_rgb(pdf_path,page_no,scale)
    target_y=(float(display_bbox[1])+float(display_bbox[3]))/2
    target_x=(float(display_bbox[0])+float(display_bbox[2]))/2
    target_h=max(.1,float(display_bbox[3])-float(display_bbox[1]))
    candidates=[]; seen=set()
    sources=list(chars or [])
    try:
        for c in _page_reference_chars(pdf_path,page_no):
            b=c.get('bbox')
            if not b or not str(c.get('c','')).isdigit():
                continue
            cy=(float(b[1])+float(b[3]))/2
            ch=max(.1,float(b[3])-float(b[1]))
            if abs(cy-target_y) > max(target_h*.55,ch*.55):
                continue
            sources.append(c)
    except Exception:
        pass
    for c in sources:
        if not str(c.get('c','')).isdigit() or c.get('geometry')=='estimated':
            continue
        b=c.get('bbox')
        if not b:
            continue
        key=tuple(round(float(v),2) for v in b)
        if key in seen:
            continue
        seen.add(key)
        m=_digit_sample_metrics(arr,b,scale)
        if m:
            m['character']=str(c.get('c'))
            cx=(float(b[0])+float(b[2]))/2
            cy=(float(b[1])+float(b[3]))/2
            m['distancePx']=abs(cx-target_x)*scale
            m['rowDistancePx']=abs(cy-target_y)*scale
            candidates.append(m)
    if not candidates:
        return deepcopy(base_style) if base_style else None

    candidates=_robust_digit_samples(candidates)
    broad=[m for m in candidates if m['character']!='1'] or candidates
    # Local tone/edge is estimated from the nearest few digits; geometry is a
    # stable median across the row after outlier rejection.
    nearest=sorted(candidates,key=lambda m:(m['distancePx'],m['rowDistancePx']))[:max(1,min(4,len(candidates)))]
    widths_b=np.array([m['inkWidthPx'] for m in broad],dtype=float)
    heights=np.array([m['inkHeightPx'] for m in candidates],dtype=float)
    rgbs=np.array([m['foregroundRGB'] for m in nearest],dtype=float)
    height_spread=float(np.std(heights)/max(1.,np.mean(heights))) if len(heights)>1 else 0.
    confidence=max(0.,min(1.,0.45+0.10*min(4,len(candidates))-0.8*height_spread))

    profile=deepcopy(base_style) if base_style else {}
    profile.update({
        'referenceCharacter':'line-digit-profile',
        'targetInkWidthPx':max(1,int(round(float(np.median(widths_b))))),
        'targetInkHeightPx':max(1,int(round(float(np.median(heights))))),
        'foregroundRGB':[float(v) for v in np.median(rgbs,axis=0)],
        'digitProfileCount':len(candidates),
        'digitProfileCharacters':''.join(m['character'] for m in candidates),
        'digitStrokeMetric':round(float(np.median([m['strokeMetric'] for m in candidates])),3),
        'digitEdgeSoftnessMetric':round(float(np.median([m['edgeSoftnessMetric'] for m in nearest])),3),
        'digitInkDensityMetric':round(float(np.median([m['inkDensityMetric'] for m in candidates])),3),
        'digitContrastMetric':round(float(np.median([m['contrastMetric'] for m in nearest])),3),
        'styleProfile':'same-row robust/local-neighbour digit profile',
        'styleConfidence':round(confidence,3),
    })
    return profile


def _best_same_row_exemplar(pdf_path,page_no,new_char,display_bbox,target_bbox,scale):
    """Return an exemplar only when it is truly on the same row and scale.

    Cross-row exemplars caused v2.3.5 to alternate between transplanted scan
    shapes and font-generated shapes.  Strict gating makes output deterministic
    across repeated fields.
    """
    if not new_char or len(new_char)!=1:
        return None
    ty=(float(target_bbox[1])+float(target_bbox[3]))/2
    th=max(.1,float(target_bbox[3])-float(target_bbox[1]))
    tx=(float(target_bbox[0])+float(target_bbox[2]))/2
    scored=[]
    try:
        refs=_page_reference_chars(pdf_path,page_no)
    except Exception:
        return None
    for c in refs:
        b=c.get('bbox')
        if c.get('c')!=new_char or not b:
            continue
        if not (b[2]<=display_bbox[0] or b[0]>=display_bbox[2] or b[3]<=display_bbox[1] or b[1]>=display_bbox[3]):
            continue
        cy=(float(b[1])+float(b[3]))/2
        ch=max(.1,float(b[3])-float(b[1]))
        ratio=ch/th
        # Same visual row only.  Height match is intentionally tight.
        if abs(cy-ty)>max(th*.55,ch*.55) or not .90<=ratio<=1.10:
            continue
        cx=(float(b[0])+float(b[2]))/2
        score=abs(1-ratio)*10 + abs(cy-ty)/th*4 + abs(cx-tx)/max(th,1)*.05
        scored.append((score,b))
    return min(scored,key=lambda x:x[0])[1] if scored else None



def _sequence_bbox(chars):
    boxes=[c.get('bbox') for c in chars if c.get('bbox') and len(c.get('bbox'))==4]
    if not boxes:
        return None
    return [min(float(b[0]) for b in boxes), min(float(b[1]) for b in boxes),
            max(float(b[2]) for b in boxes), max(float(b[3]) for b in boxes)]


def _best_same_row_fragment_exemplar(pdf_path,page_no,new_text,display_bbox,target_bbox,scale):
    """Return an exact same-row scanned fragment for multi-character reuse.

    Multi-character numeric edits should retain shared fragment geometry.  If the target page already contains the
    full requested fragment on the same visual row, copy that fragment as one
    native-pixel sprite and paste it by cell-relative offset.  This preserves the
    donor fragment's shared row height, baseline and intra-digit spacing.
    """
    new_text=str(new_text or '')
    if len(new_text)<2:
        return None
    try:
        refs=sorted(_page_reference_chars(pdf_path,page_no),key=lambda c:(float((c.get('bbox') or [0,0,0,0])[1]),float((c.get('bbox') or [0,0,0,0])[0])))
    except Exception:
        return None
    target_y=(float(target_bbox[1])+float(target_bbox[3]))/2
    target_h=max(.1,float(target_bbox[3])-float(target_bbox[1]))
    target_x=(float(target_bbox[0])+float(target_bbox[2]))/2
    scored=[]
    n=len(new_text)
    for i in range(0,max(0,len(refs)-n+1)):
        group=refs[i:i+n]
        if ''.join(str(c.get('c','')) for c in group)!=new_text:
            continue
        b=_sequence_bbox(group)
        if not b:
            continue
        # Do not use the target OCR token itself as the donor.
        if not (b[2] <= display_bbox[0] or b[0] >= display_bbox[2] or b[3] <= display_bbox[1] or b[1] >= display_bbox[3]):
            continue
        cy=(b[1]+b[3])/2; ch=max(.1,b[3]-b[1]); cx=(b[0]+b[2])/2
        ratio=ch/target_h
        if abs(cy-target_y)>max(target_h*.72,ch*.72) or not .86<=ratio<=1.16:
            continue
        # Prefer same-row, same-height, nearby fragments.  Full-fragment reuse is
        # still deterministic because ties are resolved by page order.
        score=abs(1-ratio)*12 + abs(cy-target_y)/target_h*5 + abs(cx-target_x)/max(target_h,1)*.03
        scored.append((score,b,group))
    if not scored:
        return None
    _,bbox,group=min(scored,key=lambda x:x[0])
    return {'bbox':bbox,'chars':group,'text':new_text}


def _same_page_fragment_asset(pdf_path,page_no,fragment,scale):
    """Extract a full scanned fragment as a background-free RGBA asset.

    The output follows the same payload contract as reusableGlyph so the local
    patch builder can reuse it without adding another rendering path.
    """
    if not fragment or not fragment.get('bbox') or np is None or cv2 is None:
        return None
    arr,_=_render_page_rgb(pdf_path,page_no,scale)
    bbox=[float(v) for v in fragment['bbox']]
    x0,y0,x1,y1=[int(round(v*scale)) for v in bbox]
    x0,y0=max(0,x0),max(0,y0);x1,y1=min(arr.shape[1],x1),min(arr.shape[0],y1)
    sample=arr[y0:y1,x0:x1]
    if sample.size==0:
        return None
    gray=cv2.cvtColor(sample,cv2.COLOR_RGB2GRAY).astype(float)
    background=float(np.percentile(gray,92))
    dark=gray<min(185.,background-28.)
    if not np.any(dark):
        return None
    count,labels,stats,_=cv2.connectedComponentsWithStats(dark.astype('uint8'),8)
    keep=np.zeros_like(dark,dtype=bool)
    for i in range(1,count):
        x,y,w,h,area=[int(v) for v in stats[i]]
        if area<2:
            continue
        # Remove long table rules but keep separated digits within the fragment.
        if w > sample.shape[1]*.78 and h <= max(3,int(sample.shape[0]*.22)):
            continue
        keep |= labels==i
    if not np.any(keep):
        return None
    support=cv2.dilate(keep.astype('uint8'),np.ones((5,5),np.uint8),iterations=1)>0
    foreground=float(np.percentile(gray[keep],8))
    alpha=np.clip((background-gray)/max(16.,background-foreground),0,1)
    alpha[~support]=0
    alpha_img=Image.fromarray(np.round(alpha*255).astype('uint8'))
    visible=np.asarray(alpha_img)>24
    box=_mask_bbox(visible.astype('uint8'))
    if not box:
        return None
    # Use one shared crop around the whole fragment.  Do not crop each digit.
    alpha_crop=alpha_img.crop(tuple(box))
    rgb_crop=sample[box[1]:box[3],box[0]:box[2],:]
    rgba_arr=np.dstack([rgb_crop,np.asarray(alpha_crop,dtype=np.uint8)])
    alpha_io=io.BytesIO();alpha_crop.save(alpha_io,format='PNG',optimize=True)
    rgba_io=io.BytesIO();Image.fromarray(rgba_arr.astype('uint8'),'RGBA').save(rgba_io,format='PNG',optimize=True)
    core=keep & (gray<=float(np.percentile(gray[keep],20)))
    rgb=np.median(sample[core],axis=0) if np.any(core) else np.median(sample[keep],axis=0)
    return {
        'dataUrl':'data:image/png;base64,'+base64.b64encode(alpha_io.getvalue()).decode('ascii'),
        'rgbaDataUrl':'data:image/png;base64,'+base64.b64encode(rgba_io.getvalue()).decode('ascii'),
        'char':str(fragment.get('text') or ''),'fragmentText':str(fragment.get('text') or ''),
        'inkWidthPx':alpha_crop.width,'inkHeightPx':alpha_crop.height,
        'foregroundRGB':[round(float(v),1) for v in rgb],
        'sourceScale':float(scale),'assetVersion':3,'mode':'original',
        'assetId':f"same-row-fragment:{page_no}:{str(fragment.get('text') or '')}:{round(bbox[0],2)}:{round(bbox[1],2)}",
        'sourceCellWidthPx':round((bbox[2]-bbox[0])*scale,3),
        'sourceCellHeightPx':round((bbox[3]-bbox[1])*scale,3),
        'sourceGlyphLeftOffsetPx':round(float(box[0]),3),
        'sourceGlyphTopOffsetPx':round(float(box[1]),3),
        'sourceBbox':[round(v,3) for v in bbox],
        'pixelReuse':'fragment-1to1-rgba',
    }

def _native_scan_scale(pdf_path: str, page_no: int, fallback: float = _RENDER_SCALE) -> float:
    """Return the dominant full-page scan image pixels-per-PDF-point.

    A 300-DPI scan is ~4.167 px/pt. Editing at this scale means the patch PNG
    maps 1:1 back to the source scan grid instead of being rendered at an
    arbitrary 4x scale and re-sampled during PDF insertion.
    """
    try:
        with fitz.open(pdf_path) as doc:
            page=doc.load_page(int(page_no)); infos=page.get_image_info() or []
            if not infos: return float(fallback)
            best=max(infos,key=lambda im: fitz.Rect(im.get('bbox') or (0,0,0,0)).get_area())
            rect=fitz.Rect(best.get('bbox') or (0,0,0,0))
            if rect.get_area() < page.rect.get_area()*.45: return float(fallback)
            sx=float(best.get('width') or 0)/max(.1,float(rect.width))
            sy=float(best.get('height') or 0)/max(.1,float(rect.height))
            native=min(sx,sy)
            return max(1.0,min(8.0,native)) if native>0 else float(fallback)
    except Exception:
        return float(fallback)

def _actual_sharpness(gray, mask):
    if cv2 is None or np is None or mask is None or not np.any(mask): return 0.0
    lap=np.abs(cv2.Laplacian(gray.astype('float32'),cv2.CV_32F))
    vals=lap[mask]
    return float(np.mean(vals)) if vals.size else 0.0


def _render_page_rgb(pdf_path: str, page_no: int, scale: float = _RENDER_SCALE):
    if np is None:
        raise RuntimeError("缺少 numpy，无法进行扫描文字视觉排版")
    with fitz.open(pdf_path) as doc:
        if page_no < 0 or page_no >= doc.page_count:
            raise ValueError("扫描文字页码无效")
        page = doc.load_page(page_no)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n >= 3:
            return arr[:, :, :3].copy(), page.rotation
        return np.repeat(arr[:, :, :1], 3, axis=2).copy(), page.rotation


def _expand_bbox(bbox, page_w: float, page_h: float, margin_x: float, margin_y: float):
    x0, y0, x1, y1 = [float(v) for v in bbox]
    return [
        max(0.0, x0 - margin_x),
        max(0.0, y0 - margin_y),
        min(page_w, x1 + margin_x),
        min(page_h, y1 + margin_y),
    ]


def _component_filtered_mask(gray, field_px):
    """Build a dark-ink mask while rejecting long table rules.

    The mask is intentionally local to the isolated OCR field. This preserves the
    surrounding scan/background; the exported PDF still carries page-level revision
    marking and a revision summary.
    """
    if np is None:
        raise RuntimeError("缺少 numpy")
    h, w = gray.shape[:2]
    fx0, fy0, fx1, fy1 = [int(round(v)) for v in field_px]
    fx0, fy0 = max(0, fx0), max(0, fy0)
    fx1, fy1 = min(w, fx1), min(h, fy1)
    mask = np.zeros((h, w), dtype=np.uint8)
    if fx1 <= fx0 or fy1 <= fy0:
        return mask
    local = gray[fy0:fy1, fx0:fx1]
    # Scanned black text is usually much darker than grey watermarks.
    threshold = min(175, max(105, int(np.percentile(local, 28)) + 45))
    raw = (local < threshold).astype(np.uint8) * 255
    if cv2 is None:
        mask[fy0:fy1, fx0:fx1] = raw
        return mask
    num, labels, stats, _ = cv2.connectedComponentsWithStats(raw, 8)
    kept = np.zeros_like(raw)
    lh, lw = raw.shape[:2]
    for i in range(1, num):
        x, y, cw, ch, area = [int(v) for v in stats[i]]
        if area < 2:
            continue
        # Ignore long horizontal / vertical table rules and page borders.
        if cw > lw * 0.55 and ch <= max(3, int(lh * 0.20)):
            continue
        # Do not reject a tall narrow component here.  A scanned ``1`` often
        # occupies almost the full OCR character-cell height and was therefore
        # mistaken for a vertical table rule, leaving its stem behind under the
        # replacement.  Real rules are protected below from a much larger page
        # context, where their length can be distinguished from glyph strokes.
        kept[labels == i] = 255
    kept = cv2.morphologyEx(kept, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    # Include anti-aliased edge pixels so old glyph fragments do not show through
    # the replacement. Long table rules have already been excluded above.
    kept = cv2.dilate(kept, np.ones((3, 3), np.uint8), iterations=1)
    mask[fy0:fy1, fx0:fx1] = kept
    return mask


def _mask_bbox(mask):
    if np is None:
        return None
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def _same_page_glyph(arr, bbox, scale, target_w, target_h):
    """Extract glyph ink from a same-page exemplar without copying its background."""
    x0,y0,x1,y1=[int(round(float(v)*scale)) for v in bbox]
    x0,y0=max(0,x0),max(0,y0);x1,y1=min(arr.shape[1],x1),min(arr.shape[0],y1)
    sample=arr[y0:y1,x0:x1]
    if sample.size==0:
        return None
    gray=cv2.cvtColor(sample,cv2.COLOR_RGB2GRAY).astype(float)
    background=float(np.percentile(gray,90))
    hard=gray<min(185.,background-32.)
    if not np.any(hard):
        return None
    count,labels,stats,_=cv2.connectedComponentsWithStats(hard.astype('uint8'),8)
    components=[i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>=2]
    if not components:
        return None
    keep=max(components,key=lambda i:stats[i,cv2.CC_STAT_AREA])
    core=labels==keep
    support=cv2.dilate(core.astype('uint8'),np.ones((5,5),np.uint8),iterations=1)>0
    foreground=float(np.percentile(gray[core],5))
    alpha=np.clip((background-gray)/max(18.,background-foreground),0,1)
    alpha[~support]=0
    mask=Image.fromarray(np.round(alpha*255).astype('uint8'))
    ink=np.asarray(mask)>24
    bounds=_mask_bbox(ink.astype('uint8'))
    if not bounds:
        return None
    mask=mask.crop(tuple(bounds))
    visible=np.asarray(mask)>96
    vb=_mask_bbox(visible.astype('uint8'))
    if vb:
        mask=mask.crop(tuple(vb))
    mask=mask.resize((max(1,int(target_w)),max(1,int(target_h))),Image.Resampling.LANCZOS)
    padded=Image.new('L',(mask.width+6,mask.height+6));padded.paste(mask,(3,3))
    # Use the donor's dark stroke core for foreground colour.  The median of the
    # whole thresholded component is dominated by antialiased edge pixels and
    # made the transplanted glyph visibly grey.
    cutoff=float(np.percentile(gray[core],15))
    dark_core=core & (gray<=cutoff)
    pixels=sample[dark_core]
    rgb=np.median(pixels,axis=0) if len(pixels) else np.repeat(foreground,3)
    return padded,rgb


def _font_metrics(font_path: str, text: str, size: int):
    font = ImageFont.truetype(font_path, max(4, int(size)))
    probe = Image.new("L", (2000, 300), 0)
    draw = ImageDraw.Draw(probe)
    box = draw.textbbox((0, 0), text, font=font)
    return font, box


def _choose_font(text: str, target_h: int, target_w: int):
    paths = _font_candidates(_contains_cjk(text))
    if not paths:
        raise RuntimeError("系统中没有找到可用于扫描修订的字体")
    best = None
    for path in paths:
        # Search a pixel font size that matches ink height first.
        lo, hi = 5, max(12, int(target_h * 2.4))
        chosen = None
        for _ in range(11):
            mid = (lo + hi) // 2
            try:
                font, box = _font_metrics(path, text, mid)
            except Exception:
                break
            h = max(1, box[3] - box[1])
            chosen = (font, box, mid)
            if h < target_h:
                lo = mid + 1
            else:
                hi = mid - 1
        if not chosen:
            continue
        font, box, size = chosen
        h = max(1, box[3] - box[1])
        probe = Image.new("L", (4000, 400), 0)
        draw = ImageDraw.Draw(probe)
        advances = [float(draw.textlength(c, font=font)) for c in text]
        natural = sum(advances)
        # Do not distribute width mismatch over glyph gaps: that produced the
        # conspicuous “L H - K” tracking artifact. Match natural string width.
        spacing = 0.0
        width_err = abs(natural - target_w) / max(1.0, target_w)
        height_err = abs(h - target_h) / max(1.0, target_h)
        score = height_err * 4.0 + width_err * 3.2
        if best is None or score < best[0]:
            best = (score, path, font, size, spacing, box, advances)
    if best is None:
        raise RuntimeError("系统字体无法完成扫描文字排版")
    return best


def _render_text_mask(text: str, font, spacing: float, target_w: int, target_h: int):
    # Generous canvas to retain ascenders/descenders and then crop to actual ink.
    canvas = Image.new("L", (max(target_w * 3, 320), max(target_h * 4, 160)), 0)
    draw = ImageDraw.Draw(canvas)
    x = 20.0
    y = 12.0
    for i, c in enumerate(text):
        draw.text((round(x), round(y)), c, font=font, fill=255)
        x += float(draw.textlength(c, font=font))
        if i < len(text) - 1:
            x += spacing
    bbox = canvas.getbbox()
    if not bbox:
        raise ValueError("新文字无法渲染")
    return canvas.crop(bbox), bbox


def _visual_metrics(old_bbox, new_bbox, target_w: int, target_h: int):
    ow = max(1, old_bbox[2] - old_bbox[0])
    oh = max(1, old_bbox[3] - old_bbox[1])
    nw = max(1, new_bbox[2] - new_bbox[0])
    nh = max(1, new_bbox[3] - new_bbox[1])
    width_err = abs(nw - ow) / max(1.0, ow)
    height_err = abs(nh - oh) / max(1.0, oh)
    # Baseline is intentionally pinned to the old ink bottom during placement.
    baseline_err = abs(new_bbox[3]-old_bbox[3])/max(1.0,oh)
    score = max(0.0, 100.0 - (width_err * 100 * 0.38 + height_err * 100 * 0.42 + baseline_err * 100 * 0.20))
    return {
        "oldInkWidthPx": int(ow),
        "oldInkHeightPx": int(oh),
        "newInkWidthPx": int(nw),
        "newInkHeightPx": int(nh),
        "widthErrorPct": round(width_err * 100, 1),
        "heightErrorPct": round(height_err * 100, 1),
        "baselineErrorPct": round(baseline_err * 100, 1),
        "baselineMeasurement": "ink-bottom displacement; not a typographic baseline measurement",
        "layoutScore": round(score, 1),
    }


def _clamp(value, low, high, default):
    try:
        value = float(value)
    except Exception:
        value = float(default)
    return max(float(low), min(float(high), value))


def _normalise_visual_adjust(value):
    """Normalise optional manual scan tuning without changing the auto defaults.

    All values are intentionally small-range.  The hard page-preservation and
    neighbour-overlap gates still run after these adjustments, so a user cannot
    accidentally turn a visual tweak into a broad page rewrite.
    """
    value = value if isinstance(value, dict) else {}
    font_choice=str(value.get('fontChoice','auto') or 'auto').strip().lower()
    if font_choice not in {'input','auto','times','arial','calibri','cambria','simsun','msyh'}:
        font_choice='auto'
    return {
        'fontChoice': font_choice,
        'sizeScale': _clamp(value.get('sizeScale', 1.0), .50, 1.50, 1.0),
        'widthScale': _clamp(value.get('widthScale', 1.0), .50, 1.50, 1.0),
        'xOffsetPx': _clamp(value.get('xOffsetPx', 0.0), -600.0, 600.0, 0.0),
        'yOffsetPx': _clamp(value.get('yOffsetPx', 0.0), -600.0, 600.0, 0.0),
        'darkness': _clamp(value.get('darkness', 0.0), -100.0, 100.0, 0.0),
        'strokePx': _clamp(value.get('strokePx', 0.0), -6.0, 6.0, 0.0),
        'softenPx': _clamp(value.get('softenPx', 0.0), -4.0, 4.0, 0.0),
        'clarity': _clamp(value.get('clarity', -25.0*float(value.get('softenPx',0.0) or 0.0)), -100.0, 100.0, 0.0),
        'cleanupStrength': _clamp(value.get('cleanupStrength', 50.0), 0.0, 100.0, 50.0),
        'edgeBlend': _clamp(value.get('edgeBlend', 0.0), -100.0, 100.0, 0.0),
    }


def _tune_alpha(alpha: Image.Image, adjust: dict) -> Image.Image:
    """Apply bounded glyph-only tuning to an alpha mask."""
    size = float(adjust['sizeScale'])
    width = float(adjust['widthScale'])
    if abs(size - 1.0) > 1e-4 or abs(width - 1.0) > 1e-4:
        alpha = alpha.resize((
            max(1, int(round(alpha.width * size * width))),
            max(1, int(round(alpha.height * size))),
        ), Image.Resampling.LANCZOS)

    stroke = float(adjust['strokePx'])
    # PIL morphology filters use odd integer kernels.  One bounded step is enough
    # for scan micro-adjustment; repeated application handles the ±2 range.
    if stroke >= .5:
        for _ in range(max(1, min(2, int(round(stroke))))):
            alpha = alpha.filter(ImageFilter.MaxFilter(3))
    elif stroke <= -.5:
        for _ in range(max(1, min(2, int(round(abs(stroke)))))):
            alpha = alpha.filter(ImageFilter.MinFilter(3))

    # v2.3.27 exposes one explicit clarity control. Automatic mode is exactly
    # neutral: no blur and no sharpen. User-requested softening/sharpening is
    # bounded and applied only once to the glyph alpha.
    clarity=float(adjust.get('clarity',0.0))
    if clarity < -0.1:
        alpha=alpha.filter(ImageFilter.GaussianBlur(radius=min(1.2,abs(clarity)/100.0*1.2)))
    elif clarity > 0.1:
        alpha=alpha.filter(ImageFilter.UnsharpMask(radius=.65,percent=int(30+clarity*.9),threshold=1))
    return alpha


def _build_local_patch(
    pdf_path: str,
    page_no: int,
    display_bbox,
    old_text: str,
    new_text: str,
    *,
    glyph_bbox=None,
    glyph_old: str | None = None,
    glyph_new: str | None = None,
    scale: float = _RENDER_SCALE,
    reference_style=None,
    visual_adjust=None,
    reusable_glyph=None,
    stable_fragment: bool = False,
) -> dict[str, Any]:
    """Build a field-local raster revision patch.

    """
    # When reliable character geometry says this is a one-character substitution,
    # preserve the scanned pixels of every other glyph.  Repainting a whole structured
    # field is the source of the obvious "everything changed" trace in v2.3.2.
    glyph_only = glyph_bbox is not None and glyph_old is not None and glyph_new is not None
    active_bbox = glyph_bbox if glyph_only else display_bbox
    active_old = str(glyph_old) if glyph_only else str(old_text)
    active_new = str(glyph_new) if glyph_only else str(new_text)
    adjust = _normalise_visual_adjust(visual_adjust)
    if scale is None:
        scale=_native_scan_scale(pdf_path,page_no)
    key = (
        str(pdf_path), int(page_no), tuple(round(float(v), 3) for v in active_bbox),
        active_old, active_new, bool(glyph_only), float(scale), repr(reference_style), repr(adjust),
        repr((reusable_glyph or {}).get('assetId')), repr((reusable_glyph or {}).get('mode')), bool(stable_fragment),
    )
    cached = _PATCH_CACHE.get(key)
    if cached is not None:
        return dict(cached)
    if np is None:
        raise RuntimeError("缺少 numpy，无法生成扫描修订预览")
    arr, rotation = _render_page_rgb(pdf_path, page_no, scale)
    page_h_px, page_w_px = arr.shape[:2]
    page_w = page_w_px / scale
    page_h = page_h_px / scale
    field = [float(v) for v in active_bbox]
    # Character boxes in the OCR grid can abut (the first ``0`` may start exactly
    # where ``1`` ends).  A horizontal bleed margin would then repaint that intact
    # neighbour.  The verified glyph box already includes its ink bounds, so the
    # one-glyph path deliberately has no horizontal expansion.
    donor_width = None
    if glyph_only:
        donor_width=(reference_style or {}).get('targetInkWidthPx')
        # A tabular ``6`` legitimately extends farther left/right than the ink
        # of ``1`` while keeping the same character centre.  Enlarge the opaque
        # patch just enough to hold that measured neighbour width.  Erasure below
        # remains restricted to ``local_field``, so adjacent glyphs are sampled
        # into the patch unchanged rather than repainted.
        margin_x=max(0.0,((float(donor_width)/scale)-(field[2]-field[0]))/2+0.75) if donor_width else 0.0
    else:
        margin_x=max(0.8, min(1.6, (field[3] - field[1]) * 0.10))
    margin_y = max(0.7, min(1.3, (field[3] - field[1]) * 0.09))
    # Reserve raster room for bounded manual size/position tuning.  This only
    # enlarges the sampled crop; the actual erase mask remains field-local.
    target_px=float(donor_width or max(1.0,(field[2]-field[0])*scale))
    growth=max(0.0,float(adjust['sizeScale'])*float(adjust['widthScale'])-1.0)*target_px/2.0
    manual_room_x=abs(float(adjust['xOffsetPx'])) + growth
    if manual_room_x > .01:
        margin_x += (manual_room_x + 2.0) / scale
    target_h_px=max(1.0,(field[3]-field[1])*scale)
    v_growth=max(0.0,float(adjust['sizeScale'])-1.0)*target_h_px/2.0
    manual_room_y=abs(float(adjust['yOffsetPx'])) + v_growth
    if manual_room_y > .01:
        margin_y += (manual_room_y + 2.0) / scale
    overlay = _expand_bbox(field, page_w, page_h, margin_x, margin_y)
    ox0, oy0, ox1, oy1 = overlay
    px0, py0, px1, py1 = [int(round(v * scale)) for v in overlay]
    px0, py0 = max(0, px0), max(0, py0)
    px1, py1 = min(page_w_px, px1), min(page_h_px, py1)
    overlay = [px0/scale, py0/scale, px1/scale, py1/scale]
    ox0, oy0, ox1, oy1 = overlay
    crop = arr[py0:py1, px0:px1].copy()
    if crop.size == 0:
        raise ValueError("扫描字段裁剪区域为空")
    local_field = [
        (field[0] - ox0) * scale,
        (field[1] - oy0) * scale,
        (field[2] - ox0) * scale,
        (field[3] - oy0) * scale,
    ]
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY) if cv2 is not None else np.mean(crop, axis=2).astype(np.uint8)
    ink_mask = _component_filtered_mask(gray, local_field)
    if glyph_only and active_old in '-_':
        ink_mask = (gray < 175).astype('uint8')*255
    if cv2 is not None:
        # Protect long rules using context outside this tiny cell, including a
        # rule that is connected to glyph ink. Dilation protects antialiased edges.
        ex0,ex1=max(0,px0-100),min(page_w_px,px1+100)
        ey0,ey1=max(0,py0-100),min(page_h_px,py1+100)
        context=cv2.cvtColor(arr[ey0:ey1,ex0:ex1],cv2.COLOR_RGB2GRAY)
        binary=(context<175).astype('uint8')*255
        # A straight '1' stem must never be mistaken for a protected table rule.
        # Require lines substantially longer than this field's glyph height.
        rule_length=max(25,round(scale*15),round((field[3]-field[1])*scale*2))
        lines=cv2.morphologyEx(binary,cv2.MORPH_OPEN,np.ones((1,rule_length),np.uint8))
        lines |= cv2.morphologyEx(binary,cv2.MORPH_OPEN,np.ones((rule_length,1),np.uint8))
        lines=cv2.dilate(lines,np.ones((3,3),np.uint8))
        protected=lines[py0-ey0:py1-ey0,px0-ex0:px1-ex0]>0
        ink_mask[protected]=0
    else:
        protected=np.zeros_like(gray,dtype=bool)

    # Manual “cleanliness” control only changes the old-glyph erase mask inside
    # the verified field.  Protected rules remain protected at every strength.
    cleanup=float(adjust['cleanupStrength'])
    if cv2 is not None and np.any(ink_mask):
        if cleanup > 58:
            iterations = 1 if cleanup < 82 else 2
            ink_mask = cv2.dilate(ink_mask, np.ones((3,3),np.uint8), iterations=iterations)
        elif cleanup < 35:
            ink_mask = cv2.erode(ink_mask, np.ones((3,3),np.uint8), iterations=1)
        # Never let a manual mask expansion escape the selected OCR character cell.
        cell_guard=np.zeros_like(ink_mask,dtype=np.uint8)
        gx0,gy0,gx1,gy1=[int(round(v)) for v in local_field]
        gx0,gy0=max(0,gx0-2),max(0,gy0-2);gx1,gy1=min(ink_mask.shape[1],gx1+2),min(ink_mask.shape[0],gy1+2)
        cell_guard[gy0:gy1,gx0:gx1]=255
        ink_mask=cv2.bitwise_and(ink_mask,cell_guard)
        ink_mask[protected]=0
    # Erasure mask includes soft edges; geometry fitting must use undilated ink.
    old_mask=(gray<175)&~protected
    # The patch may extend into inter-character gaps to hold a naturally wider
    # replacement.  Geometry must still be measured strictly inside the old
    # character cell; otherwise a neighbouring hyphen enters ``old_ink`` and
    # shifts the new digit left until ``-6`` visually touches.
    fx0,fy0,fx1,fy1=[int(round(v)) for v in local_field]
    fx0,fy0=max(0,fx0-1),max(0,fy0-1)
    fx1,fy1=min(old_mask.shape[1],fx1+1),min(old_mask.shape[0],fy1+1)
    restricted=np.zeros_like(old_mask,dtype=bool)
    restricted[fy0:fy1,fx0:fx1]=old_mask[fy0:fy1,fx0:fx1]
    old_ink = _mask_bbox(restricted.astype('uint8'))
    had_real_ink = old_ink is not None
    if old_ink is None:
        # Fallback to OCR geometry when scan contrast is unusually low.
        old_ink = [int(local_field[0]), int(local_field[1]), int(local_field[2]), int(local_field[3])]
    old_w = max(4, old_ink[2] - old_ink[0])
    old_h = max(4, old_ink[3] - old_ink[1])

    # Restore only the old dark text ink.  v2.3.7 enforces an exact
    # preservation invariant: pixels outside the erase mask remain byte-identical
    # in the raster patch before PDF insertion.
    if cv2 is not None:
        bg_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
        radius = max(1.5, min(4.5, 3.0 + (cleanup-50.0)*0.03))
        healed = cv2.inpaint(bg_bgr, ink_mask, radius, cv2.INPAINT_TELEA)
        healed = cv2.cvtColor(healed, cv2.COLOR_BGR2RGB)
        edge_blend=float(adjust['edgeBlend'])
        # v2.3.11 makes edge blending genuinely bidirectional.  Zero is the
        # automatic neutral point with a small scan-like feather; negative values
        # tighten the transition, positive values broaden it.  The preservation
        # gate later still restores every pixel outside the allowed support.
        if edge_blend <= -95:
            feather=(ink_mask.astype(float)/255.0)[:,:,None]
        else:
            base_sigma=.42
            blur_sigma=max(.05, base_sigma + (edge_blend/100.0)*(1.25 if edge_blend>=0 else .37))
            feather=cv2.GaussianBlur((ink_mask.astype(float)/255.0),(0,0),blur_sigma)
            feather=np.clip(feather,0,1)[:,:,None]
        background=np.clip(crop*(1-feather)+healed*feather,0,255).astype('uint8')
        background[ink_mask == 0] = crop[ink_mask == 0]
    else:  # pragma: no cover
        background = crop.copy()
        ys, xs = np.where(ink_mask > 0)
        if len(xs):
            med = np.median(crop.reshape(-1, 3), axis=0).astype(np.uint8)
            background[ys, xs] = med

    reused=False
    reuse_mode=''
    reused_rgba=None
    if reusable_glyph and isinstance(reusable_glyph,dict) and reusable_glyph.get('dataUrl'):
        try:
            payload=str(reusable_glyph.get('dataUrl')).split(',',1)[-1]
            alpha=Image.open(io.BytesIO(base64.b64decode(payload))).convert('L')
            rgb=np.asarray(reusable_glyph.get('foregroundRGB') or [55,55,55],dtype=float)
            mode=str(reusable_glyph.get('mode') or 'original')
            reuse_mode=mode
            rgba_url=reusable_glyph.get('rgbaDataUrl')
            if rgba_url and mode=='original':
                rgba_payload=str(rgba_url).split(',',1)[-1]
                reused_rgba=Image.open(io.BytesIO(base64.b64decode(rgba_payload))).convert('RGBA')
                alpha=reused_rgba.getchannel('A')
            if mode=='original':
                source_scale=float(reusable_glyph.get('sourceScale') or scale)
                if abs(source_scale-float(scale))>0.01:
                    raise ValueError('1:1 原文复用要求源字与目标使用相同渲染倍率；请重新复制成品字，或主动切换“允许缩放适配”')
            if mode=='fit' and reference_style:
                sw=max(1,float(reusable_glyph.get('inkWidthPx') or alpha.width))
                sh=max(1,float(reusable_glyph.get('inkHeightPx') or alpha.height))
                tw_ref=float(reference_style.get('targetInkWidthPx') or sw)
                th_ref=float(reference_style.get('targetInkHeightPx') or sh)
                factor=min(1.35,max(.65,min(tw_ref/sw,th_ref/sh)))
                if abs(factor-1)>0.01:
                    alpha=alpha.resize((max(1,round(alpha.width*factor)),max(1,round(alpha.height*factor))),Image.Resampling.LANCZOS)
            matched={
                'font':'reused finished glyph','manualFontChoice':'reused','referenceCharacter':'finished-glyph:'+active_new,
                'samePageExemplar':False,'reusedFinishedGlyph':True,'reusableAssetId':str(reusable_glyph.get('assetId') or ''),
                'overall_match_score':100.0,'replacement_style_score':100.0,
                'foregroundRGB':[round(float(v),1) for v in rgb],
            }
            reused=True
        except Exception as ex:
            raise ValueError(f'成品字块无法读取：{ex}')
    elif had_real_ink:
        paths=_font_candidates(_contains_cjk(active_old+active_new))
        font_choice=str(adjust.get('fontChoice') or 'input')
        if font_choice!='auto':
            aliases={'input':('segoeui','arial','liberationsans','dejavusans'),'times':('times','liberationserif','freeserif'),'arial':('arial','liberationsans'),
                     'calibri':('calibri',),'cambria':('cambria',),'simsun':('simsun',),'msyh':('msyh',)}
            needles=aliases.get(font_choice,(font_choice,))
            preferred=[p for p in paths if any(n in Path(p).name.lower() for n in needles)]
            if preferred:
                paths=preferred
        alpha, rgb, matched = fit_source(
            active_old, active_new, crop, old_ink, paths, reference_style
        )
        matched['manualFontChoice']=font_choice
    else:
        _, path, font, size, spacing, _, _ = _choose_font(active_new or ' ', old_h, old_w)
        alpha = _render_text_mask(active_new, font, spacing, old_w, old_h)[0] if active_new else Image.new('L',(1,old_h))
        rgb=np.array([55,55,55]);matched={
            'font':Path(path).name,'fontSizePx':size,'trackingPx':0.,
            'overall_match_score':0.,'replacement_style_score':0.,
            'qualityWarning':'视觉匹配质量不足：原区域没有可测量文字'
        }

    exemplar_bbox=(reference_style or {}).get('exemplarBbox')
    if (not reused) and had_real_ink and exemplar_bbox and cv2 is not None and adjust.get('fontChoice')=='auto':
        exemplar=_same_page_glyph(
            arr, exemplar_bbox, scale,
            (reference_style or {}).get('targetInkWidthPx',old_w),
            (reference_style or {}).get('targetInkHeightPx',old_h)
        )
        if exemplar:
            # Same-row exemplar contributes glyph shape and edge only.  Tone still
            # comes from the target row's local profile, preventing exposure drift.
            alpha,_=exemplar
            matched.update({
                'referenceCharacter':'same-page:'+active_new,
                'samePageExemplar':True,
                'font':'same-page scanned glyph',
                'alphaCoreGain':1.0,
                'foregroundRGB':[round(float(v),1) for v in rgb],
            })

    # v2.3.10 manual scan micro-adjustment.  Auto-match remains the zero/default
    # point; every control is applied to the generated glyph only.
    if not reused:
        alpha=_tune_alpha(alpha,adjust)
    if (not reused) and float(adjust['darkness']):
        # Positive means darker.  Work in RGB space before compositing.
        rgb=np.clip(np.asarray(rgb,dtype=float)-float(adjust['darkness']),0,255)
        matched['foregroundRGB']=[round(float(v),1) for v in rgb]

    if not had_real_ink:
        alpha=alpha.resize((min(alpha.width,crop.shape[1]),alpha.height),Image.Resampling.LANCZOS)
    tw, th = alpha.size
    alpha_ink = alpha.getbbox()
    if reused and reuse_mode=='original' and reusable_glyph.get('sourceGlyphLeftOffsetPx') is not None and reusable_glyph.get('sourceGlyphTopOffsetPx') is not None:
        # v2.3.30 true 1:1 reuse: retain the glyph's original bearing/baseline
        # relative to its character cell.  Only X/Y translation is permitted.
        tx0 = round(local_field[0] + float(reusable_glyph['sourceGlyphLeftOffsetPx']) + float(adjust['xOffsetPx']))
        ty = round(local_field[1] + float(reusable_glyph['sourceGlyphTopOffsetPx']) + float(adjust['yOffsetPx']))
        matched['reusePlacement']='source-cell-anchor'
        matched['reuseResampled']=False
    else:
        tx0 = round((local_field[0]+local_field[2]-tw)/2 + float(adjust['xOffsetPx']))
        ty = round(old_ink[3]-th+(3 if had_real_ink else 0) + float(adjust['yOffsetPx']))

    visible_w=(alpha_ink[2]-alpha_ink[0]) if alpha_ink else 0
    available_w=max(1,crop.shape[1]-2)
    if visible_w > available_w:
        factor=available_w/max(1,visible_w)
        if reused and reuse_mode=='original':
            raise ValueError('1:1 原文复用：目标字符槽比源字窄，已阻止自动缩放。请扩大目标框，或主动切换“允许缩放适配”')
        # A stable numeric fragment has its
        # own width policy.  If no whole scanned 600 exemplar exists, do not let
        # the generic v2.3.28 4% WYSIWYG guard abort the edit.  Fit the complete
        # numeric fragment with a *uniform* scale so its aspect ratio stays intact;
        # never horizontally squash just the digits.  This keeps the untouched
        # prefix/suffix pixels while allowing the replacement block to fit.
        if stable_fragment and not reused:
            if factor < .78 and had_real_ink:
                raise ValueError('稳定数字片段超出可靠修改区域，请扩大数字片段范围；系统不会重绘整字段或明显压缩字形')
            new_w=max(1,round(tw*factor)); new_h=max(1,round(th*factor))
            alpha=alpha.resize((new_w,new_h),Image.Resampling.LANCZOS)
            tw,th=alpha.size
            matched['stableFragmentWidthPolicy']='uniform-scale-to-fit'
            matched['stableFragmentUniformScale']=round(factor,3)
            matched['cellWidthConstraint']=round(factor,3)
            # Re-anchor after the uniform resize so the fragment remains on the
            # original scanned baseline and centered in the original numeric block.
            tx0=round((local_field[0]+local_field[2]-tw)/2 + float(adjust['xOffsetPx']))
            ty=round(old_ink[3]-th+(3 if had_real_ink else 0) + float(adjust['yOffsetPx']))
        else:
            # v2.3.28 WYSIWYG input mode must not silently distort the user's chosen
            # glyph shape.  More than 4% horizontal squeezing is surfaced as an
            # actionable field-width warning instead of changing the font proportions.
            if adjust.get('fontChoice') == 'input' and factor < .96:
                raise ValueError('保持输入字形：新文字超出当前字段宽度，请扩大框选范围，或手动调小“大小/宽度”；系统不会自动压扁字形')
            if factor < .70 and had_real_ink:
                raise ValueError('新字符超出可靠修改区域，请扩大所选字段；未重绘整行')
            alpha=alpha.resize((max(1,round(tw*factor)),th),Image.Resampling.LANCZOS)
            tw=alpha.width
            matched['cellWidthConstraint']=round(factor,3)
        # v2.3.8: fitting a glyph a few percent into its OCR cell is normal and
        # must not be treated as a failure.  Only a material squeeze is surfaced
        # as a soft visual warning; severe squeezes are still rejected above.
        if factor < .84:
            matched['qualityWarning']='视觉匹配提醒：新字符存在明显宽度压缩，建议放大检查'
        else:
            matched['widthConstraintNote']='字符已轻微适配当前 OCR 字符单元'

    # Search only a tiny placement neighbourhood.  The OCR character cell remains
    # the anchor, but a candidate that touches an unchanged neighbouring glyph is
    # rejected before composition.  This prevents "-6" or "60" from merging.
    field_mask=np.zeros_like(gray,dtype=bool)
    cfx0,cfy0,cfx1,cfy1=[int(round(v)) for v in local_field]
    cfx0,cfy0=max(0,cfx0),max(0,cfy0);cfx1,cfy1=min(gray.shape[1],cfx1),min(gray.shape[0],cfy1)
    field_mask[cfy0:cfy1,cfx0:cfx1]=True
    neighbour_dark=(gray < 175) & ~field_mask & ~protected
    cell_center=(local_field[0]+local_field[2])/2.0
    placements=[]
    placement_offsets=(0,) if (reused and reuse_mode=='original') else (-2,-1,0,1,2)
    for dx in placement_offsets:
        tx=max(-3,min(tx0+dx,crop.shape[1]-tw+3))
        cand=Image.new('L',(crop.shape[1],crop.shape[0]));cand.paste(alpha,(tx,ty))
        core=np.asarray(cand)>96
        ys,xs=np.where(core)
        center_err=abs(((float(xs.min()+xs.max()+1)/2.0) if len(xs) else cell_center)-cell_center)
        overlap=int(np.count_nonzero(core & neighbour_dark))
        placements.append((overlap*1000.0 + center_err*10.0 + abs(dx), overlap, center_err, tx, cand))
    _, neighbour_overlap, center_error, tx, layer=min(placements,key=lambda x:x[0])
    core_count=max(1,int(np.count_nonzero(np.asarray(layer)>96)))
    overlap_limit=max(2,int(round(core_count*.025)))
    if neighbour_overlap > overlap_limit:
        raise ValueError('新字符与相邻未修改文字发生重叠，已阻止产生字距/粘连伪影')

    # v2.3.27 renders directly on the dominant source scan pixel grid.
    # No downsample->upsample pixelation pass is allowed.
    native_scale=_native_scan_scale(pdf_path,page_no)
    native_step=1
    matched['nativeScalePxPerPt']=round(float(native_scale),4)
    matched['renderScalePxPerPt']=round(float(scale),4)
    matched['nativePixelStep']=1

    a=np.asarray(layer,dtype=float)/255.
    residual=gray.astype(float)-cv2.GaussianBlur(gray.astype(float),(0,0),1) if cv2 is not None else np.zeros_like(gray,dtype=float)
    quiet=(ink_mask==0) & ~protected
    sigma=float(np.std(residual[quiet])) if np.any(quiet) else 0.
    texture=np.clip(residual,-2*sigma,2*sigma)

    # Alpha-compositing a scanned glyph over a bright paper background makes the
    # visible core lighter than the sampled neighbouring text unless the source
    # colour is compensated.  Solve the compositing equation at the median core
    # alpha so the *actual output* blackness matches the local row, not merely the
    # requested foreground parameter.
    desired_rgb=np.asarray(rgb,dtype=float)
    core_for_tone=a>0.55
    compensated_rgb=desired_rgb.copy()
    if np.any(core_for_tone):
        alpha_med=float(np.median(a[core_for_tone]))
        bg_med=np.median(background[core_for_tone],axis=0).astype(float)
        if alpha_med>0.10:
            compensated_rgb=np.clip((desired_rgb-bg_med*(1.0-alpha_med))/alpha_med,0,255)
    if reused_rgba is not None and reuse_mode=='original':
        # Preserve the exact source glyph edge/tone texture.  The RGBA sprite is
        # copied 1:1; only the target paper underneath is different.
        foreground=np.broadcast_to(compensated_rgb[None,None,:],background.shape).astype(float).copy()
        src_rgb=np.asarray(reused_rgba,dtype=np.uint8)[:,:,:3].astype(float)
        sx0=max(0,-tx); sy0=max(0,-ty)
        dx0=max(0,tx); dy0=max(0,ty)
        copy_w=min(src_rgb.shape[1]-sx0, foreground.shape[1]-dx0)
        copy_h=min(src_rgb.shape[0]-sy0, foreground.shape[0]-dy0)
        if copy_w>0 and copy_h>0:
            foreground[dy0:dy0+copy_h,dx0:dx0+copy_w]=src_rgb[sy0:sy0+copy_h,sx0:sx0+copy_w]
        matched['reusePixelMode']='rgba-1to1'
    else:
        foreground=np.clip(compensated_rgb[None,None,:]+texture[:,:,None],0,255)
    raw_composed=np.clip(background*(1-a[:,:,None])+foreground*a[:,:,None],0,255).astype('uint8')
    matched['foregroundCompensationRGB']=[round(float(v),1) for v in compensated_rgb]

    # Hard page-preservation gate.  Only old-ink restoration plus the new glyph
    # are allowed to differ.  Everything else is restored exactly from the source
    # crop, including watermarks, rules, signatures, seals and neighbouring text.
    new_support=a>(4.0/255.0)
    erase_support=ink_mask>0
    allowed=erase_support | new_support
    raw_changed=np.any(raw_composed!=crop,axis=2)
    suppressed_non_target=int(np.count_nonzero(raw_changed & ~allowed))
    composed=raw_composed.copy()
    composed[~allowed]=crop[~allowed]
    composed[protected]=crop[protected]
    changed=np.any(composed!=crop,axis=2)
    preservation_violations=int(np.count_nonzero(changed & ~allowed))

    # A tight opaque patch minimizes re-sampling of unchanged scan pixels.  A
    # one-native-pixel unchanged border keeps the insertion boundary visually calm.
    tight=_mask_bbox(changed.astype('uint8'))
    if not tight:
        raise ValueError('替换没有产生有效像素变化')
    bx0,by0,bx1,by1=tight
    border=max(1,int(native_step))
    bx0=max(0,bx0-border);by0=max(0,by0-border)
    bx1=min(crop.shape[1],bx1+border);by1=min(crop.shape[0],by1+border)
    patch=Image.fromarray(composed[by0:by1,bx0:bx1])
    tight_overlay=[(px0+bx0)/scale,(py0+by0)/scale,(px0+bx1)/scale,(py0+by1)/scale]

    new_bbox=_mask_bbox((np.asarray(layer)>96).astype('uint8')) or old_ink
    metrics=_visual_metrics(old_ink,new_bbox,old_w,old_h)
    metrics.update(matched)
    if matched.get('targetInkWidthPx') and new_bbox:
        expected_w=max(1,int(matched['targetInkWidthPx']))
        expected_h=max(1,int(matched.get('targetInkHeightPx') or old_h))
        actual_w=max(1,new_bbox[2]-new_bbox[0]);actual_h=max(1,new_bbox[3]-new_bbox[1])
        width_error=abs(actual_w-expected_w)/expected_w
        height_error=abs(actual_h-expected_h)/expected_h
        baseline_error=abs(new_bbox[3]-old_ink[3])/max(1,expected_h)
        metrics.update({
            'replacementWidthErrorPct':round(width_error*100,1),
            'replacementHeightErrorPct':round(height_error*100,1),
            'replacementBaselineErrorPct':round(baseline_error*100,1),
            'layoutScore':round(max(0,100-100*(.45*width_error+.35*height_error+.20*baseline_error)),1),
            'layoutScoreBasis':'replacement ink vs local scanned digit profile; baseline uses local ink bottom',
        })

    # Colour is measured on the actual composed core, not merely from the requested
    # RGB parameter.  This catches pale/transparent glyphs that previously passed.
    new_core=np.asarray(layer)>128
    actual_core=composed[new_core]
    target_rgb=np.asarray(matched.get('foregroundRGB') or rgb,dtype=float)
    actual_rgb=np.median(actual_core,axis=0) if len(actual_core) else target_rgb
    color_delta=float(np.mean(np.abs(actual_rgb-target_rgb)))
    color_score=max(0.0,100.0-color_delta/1.25)

    old_core=(restricted>0)
    new_core_mask=np.asarray(layer)>128
    source_sharp=_actual_sharpness(gray,old_core)
    output_gray=cv2.cvtColor(composed,cv2.COLOR_RGB2GRAY) if cv2 is not None else np.mean(composed,axis=2).astype('uint8')
    new_sharp=_actual_sharpness(output_gray,new_core_mask)
    sharp_ratio=(new_sharp/source_sharp) if source_sharp>1e-6 else 1.0
    # Blur is the hard failure we care about. A sharper glyph is handled by the
    # existing edge-softness/style score instead of being mislabeled as blurry.
    actual_sharp_score=max(0.0,min(100.0,sharp_ratio*100.0))
    metrics.update({'sourceSharpness':round(source_sharp,3),'replacementSharpness':round(new_sharp,3),
                    'sharpnessRatio':round(sharp_ratio,3),'actualSharpnessScore':round(actual_sharp_score,1)})

    layout_score=float(metrics.get('layoutScore',100.0))
    style_score=float(metrics.get('replacement_style_score',metrics.get('overall_match_score',0.0)))
    overall=float(metrics.get('overall_match_score',0.0))

    # v2.3.8 splits destructive-risk blocking from visual-quality advice.
    # Hard safety failures still block because they can damage neighbouring page
    # content.  Geometry/colour/style mismatches remain visible to the tester but
    # no longer prevent generating a preview for manual 100%/200% inspection.
    hard_safety_gate=(
        preservation_violations==0 and neighbour_overlap<=overlap_limit
    )
    visual_quality_gate=(
        layout_score>=72.0 and color_score>=78.0 and overall>=70.0 and style_score>=65.0 and actual_sharp_score>=60.0
    )
    quality_gate=hard_safety_gate and visual_quality_gate
    warnings=[]
    if metrics.get('qualityWarning'):
        warnings.append(str(metrics['qualityWarning']))
    if hard_safety_gate and not visual_quality_gate:
        warnings.append('视觉匹配尚未达到建议阈值：已允许生成预览，请在 100%/200% 下确认')
    if actual_sharp_score < 60.0:
        warnings.append('清晰度提醒：替换字边缘锐度与原扫描文字差异较大')

    # Expose the final tuned glyph alpha as a document-local reusable asset.
    # It contains no background pixels, so pasting it elsewhere cannot transplant
    # paper texture / watermarks from the source location.
    if glyph_only and active_new and len(active_new)==1:
        sprite_box=alpha.getbbox()
        if sprite_box:
            sprite=alpha.crop(sprite_box)
            sprite_io=io.BytesIO();sprite.save(sprite_io,format='PNG',optimize=True)
            # Store a background-free RGBA sprite as well as the legacy alpha mask.
            # RGB comes from the actual rendered glyph foreground (including its
            # source scan texture); A is the exact final alpha.  Reusing this asset
            # in original mode therefore needs no font rerender or resampling.
            sx0,sy0,sx1,sy1=sprite_box
            gx0,gy0=tx+sx0,ty+sy0
            gx1,gy1=tx+sx1,ty+sy1
            rgb_sprite=np.clip(foreground[max(0,gy0):max(0,gy1),max(0,gx0):max(0,gx1)],0,255).astype('uint8')
            alpha_arr=np.asarray(sprite,dtype=np.uint8)
            rgba_url=None
            if rgb_sprite.shape[:2]==alpha_arr.shape:
                rgba_arr=np.dstack([rgb_sprite,alpha_arr])
                rgba_img=Image.fromarray(rgba_arr,'RGBA')
                rgba_io=io.BytesIO();rgba_img.save(rgba_io,format='PNG',optimize=True)
                rgba_url='data:image/png;base64,'+base64.b64encode(rgba_io.getvalue()).decode('ascii')
            metrics['reusableGlyph']={
                'dataUrl':'data:image/png;base64,'+base64.b64encode(sprite_io.getvalue()).decode('ascii'),
                'rgbaDataUrl':rgba_url,
                'char':active_new,'inkWidthPx':sprite.width,'inkHeightPx':sprite.height,
                'foregroundRGB':[round(float(v),1) for v in desired_rgb],
                'sourceScale':float(scale),'assetVersion':2,
                'sourceCellWidthPx':round(float(local_field[2]-local_field[0]),3),
                'sourceCellHeightPx':round(float(local_field[3]-local_field[1]),3),
                'sourceGlyphLeftOffsetPx':round(float(gx0-local_field[0]),3),
                'sourceGlyphTopOffsetPx':round(float(gy0-local_field[1]),3),
                'sourceSharpness':round(float(new_sharp),3),
                'pixelReuse':'1to1-rgba',
            }

    metrics.update({
        'glyphOnly':bool(glyph_only),
        'manualVisualAdjust':{k:(round(float(v),3) if isinstance(v,(int,float)) else v) for k,v in adjust.items()},
        'cleanupStrength':round(float(cleanup),1),
        'edgeBlend':round(float(adjust['edgeBlend']),1),
        'changed_pixel_count':int(changed.sum()),
        'changed_bbox':tight,
        'replacementInkBboxPx':new_bbox,
        'characterCellBboxPx':[round(float(v),2) for v in local_field],
        'diff_ratio':round(float(changed.mean()),6),
        'preservationViolationPixels':preservation_violations,
        'suppressedNonTargetChanges':suppressed_non_target,
        'neighbourOverlapPixels':int(neighbour_overlap),
        'neighbourOverlapLimit':int(overlap_limit),
        'placementCenterErrorPx':round(float(center_error),2),
        'tightPatch':True,
        'tightPatchBorderPx':int(border),
        'background_score':None,
        'backgroundScoreNote':'非目标像素强制保持原值；被原字遮挡的背景无法从单张扫描中直接观测',
        'color_score':round(color_score,1),
        'actualForegroundRGB':[round(float(v),1) for v in actual_rgb],
        'hardSafetyPassed':bool(hard_safety_gate),
        'visualQualityPassed':bool(visual_quality_gate),
        'qualityGatePassed':bool(quality_gate),
        'qualityWarning':'；'.join(dict.fromkeys(warnings)),
        'qualityGateBasis':'硬门：页面保护 + 邻字不重叠；软门：几何 + 实际前景色 + 局部扫描风格 + 实际清晰度',
        'renderer':'native-scan-v1',
    })

    out = io.BytesIO()
    patch.save(out, format='PNG', optimize=True)
    result = {
        'png': out.getvalue(),
        'overlayBbox': [round(v, 3) for v in tight_overlay],
        'fieldBbox': [round(v, 3) for v in field],
        'metrics': metrics,
        'rotation': int(rotation or 0),
    }
    _PATCH_CACHE[key] = result
    return dict(result)


def compose_comparison(before_png: bytes, after_png: bytes, labels=("修改前", "修改后")) -> bytes:
    before = Image.open(io.BytesIO(before_png)).convert("RGB")
    after = Image.open(io.BytesIO(after_png)).convert("RGB")
    h = max(before.height, after.height)
    w = max(before.width, after.width)
    top = 30
    gap = 12
    canvas = Image.new("RGB", (w * 2 + gap, h + top), "white")
    canvas.paste(before, (0, top))
    canvas.paste(after, (w + gap, top))
    draw = ImageDraw.Draw(canvas)
    try:
        font_path = _font_candidates(True)[0]
        font = ImageFont.truetype(font_path, 17)
    except Exception:
        font = ImageFont.load_default()
    draw.text((6, 6), labels[0], font=font, fill=(65, 70, 78))
    draw.text((w + gap + 6, 6), labels[1], font=font, fill=(65, 70, 78))
    out = io.BytesIO()
    canvas.save(out, format="PNG", optimize=True)
    return out.getvalue()


def refine_ascii_geometry(pdf_path,page_no,text,chars,scale):
    """Validate ASCII OCR cells against ink projections before erasing.

    Some real OCR cells cut through the left edge of a '1'. Accept pixel-derived
    cells only when there is exactly one separated ink group for every expected
    character and no substantial displacement. Chinese fragments are not guessed.
    """
    mapping=aligned_chars(text,chars);updated=deepcopy(mapping)
    arr,_=_render_page_rgb(pdf_path,page_no,scale)
    for match in re.finditer(r'[A-Za-z0-9][A-Za-z0-9_./-]*',text):
        indices=list(range(match.start(),match.end()))
        if len(indices)<3:continue
        boxes=[mapping[i]['bbox'] for i in indices]
        x0=max(0,round((min(b[0] for b in boxes)-2)*scale));x1=min(arr.shape[1],round((max(b[2] for b in boxes)+2)*scale))
        y0=max(0,round(min(b[1] for b in boxes)*scale));y1=min(arr.shape[0],round(max(b[3] for b in boxes)*scale))
        gray=cv2.cvtColor(arr[y0:y1,x0:x1],cv2.COLOR_RGB2GRAY)
        mask=(gray<175).astype('uint8')
        rules=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((1,max(25,round(15*scale),(y1-y0)*2)),np.uint8))
        mask[rules>0]=0
        columns=np.flatnonzero(np.any(mask,axis=0))
        groups=[]
        for col in columns:
            if not groups or col>groups[-1][-1]+1:groups.append([])
            groups[-1].append(int(col))
        if len(groups)!=len(indices):continue
        glyphs=[]
        for group in groups:
            ys=np.where(mask[:,group[0]:group[-1]+1]>0)[0]
            glyphs.append([group[0]+x0,int(ys.min())+y0,group[-1]+1+x0,int(ys.max())+1+y0])
        tolerance=max(b[3]-b[1] for b in boxes)*scale*.5
        if any(abs((g[0]+g[2])/2-(b[0]+b[2])*scale/2)>tolerance for g,b in zip(glyphs,boxes)):continue
        for j,i in enumerate(indices):
            g=glyphs[j]
            left=(glyphs[j-1][2]+g[0])/2 if j else g[0]-2
            right=(g[2]+glyphs[j+1][0])/2 if j+1<len(glyphs) else g[2]+2
            updated[i]['bbox']=[left/scale,(g[1]-2)/scale,right/scale,(g[3]+2)/scale]
            updated[i]['geometry']='pixel-verified'
    return [updated[i] for i in sorted(updated)]


def build_scan_revision_patch(pdf_path, page_no, display_bbox, old_text, new_text, *, chars=None, scale=None, **legacy):
    """Build independent patches on the native scan pixel grid."""
    if scale is None:
        scale=_native_scan_scale(pdf_path,page_no)
    if chars is None:
        return _build_local_patch(pdf_path,page_no,display_bbox,old_text,new_text,scale=scale,**legacy)
    chars=refine_ascii_geometry(pdf_path,page_no,old_text,chars,scale) if cv2 is not None else chars
    changes=plan_changes(old_text,new_text,chars)
    patches=[]
    context_style=None
    # Infer typeface, horizontal scale, stroke and scan softness from the whole
    # unchanged OCR line. A single character can be ambiguous across fonts.
    # Only measured parameters are transferred; the line pixels remain untouched.
    if old_text and not _contains_cjk(old_text):
        arr,_=_render_page_rgb(pdf_path,page_no,scale)
        x0,y0,x1,y1=[round(float(v)*scale) for v in display_bbox]
        x0,y0=max(0,x0),max(0,y0);x1,y1=min(arr.shape[1],x1),min(arr.shape[0],y1)
        sample=arr[y0:y1,x0:x1]
        if sample.size:
            bounds=_mask_bbox((np.mean(sample,axis=2)<175).astype('uint8'))
            if bounds:
                try:
                    _,_,context_style=fit_source(old_text,old_text,sample,bounds,_font_candidates(False))
                    context_style['referenceCharacter']='context:'+old_text
                except (OSError,ValueError):
                    context_style=None
    # Build one target-row digit profile once.  Every numeric replacement in
    # this field shares it, eliminating v2.3.5's first-donor / cross-row drift.
    line_digit_style=_line_digit_style_profile(pdf_path,page_no,chars,display_bbox,scale,context_style)
    for region in changes:
        is_digit_fragment=len(region['new'])>=2 and str(region['new']).isdigit() and str(region['old']).isdigit()
        # A line-digit profile describes one digit.  Use it for single-glyph
        # digit substitutions only; a multi-digit fragment must either reuse a
        # whole scanned fragment or be fitted against the original field context.
        reference_style=deepcopy(context_style if is_digit_fragment else (line_digit_style if str(region['new']).isdigit() else context_style))
        fragment_asset=None
        if is_digit_fragment:
            fragment=_best_same_row_fragment_exemplar(pdf_path,page_no,region['new'],display_bbox,region['bbox'],scale)
            fragment_asset=_same_page_fragment_asset(pdf_path,page_no,fragment,scale) if fragment else None
            if reference_style is None:
                reference_style={}
            if fragment_asset:
                reference_style.update({
                    'referenceCharacter':'same-row-fragment:'+region['new'],
                    'fragmentExemplarPolicy':'whole-fragment-1to1',
                    'targetInkWidthPx':int(fragment_asset.get('inkWidthPx') or 1),
                    'targetInkHeightPx':int(fragment_asset.get('inkHeightPx') or 1),
                    'foregroundRGB':fragment_asset.get('foregroundRGB') or reference_style.get('foregroundRGB',[55,55,55]),
                })
            else:
                reference_style['fragmentExemplarPolicy']='not-found; font fragment with shared row profile'
        elif reference_style is not None and len(region['new'])==1 and region['new'].isdigit():
            exemplar=_best_same_row_exemplar(pdf_path,page_no,region['new'],display_bbox,region['bbox'],scale)
            if exemplar is not None:
                reference_style['exemplarBbox']=exemplar
                reference_style['exemplarPolicy']='strict-same-row'
            else:
                reference_style.pop('exemplarBbox',None)
                reference_style['exemplarPolicy']='font-shape + same-row digit profile'
        reusable_for_region=fragment_asset or legacy.get('reusable_glyph')
        patch=_build_local_patch(pdf_path,page_no,region['bbox'],region['old'],region['new'],
            glyph_bbox=region['bbox'],glyph_old=region['old'],glyph_new=region['new'],scale=scale,reference_style=reference_style,
            visual_adjust=legacy.get('visual_adjust'),reusable_glyph=reusable_for_region,stable_fragment=bool(region.get('stableFragment')))
        if fragment_asset:
            patch['metrics']['reusedWholeFragment']=True
            patch['metrics']['reusedFragmentText']=region['new']
            patch['metrics']['fragmentPixelMode']='same-row-rgba-1to1'
        patch['metrics']['glyphOnly']=len(region['old'])==1 and len(region['new'])==1
        patch['region']={**region,'erase_bbox':region['bbox'],'render_bbox':patch['overlayBbox'],'blend_bbox':patch['overlayBbox']}
        patches.append(patch)
    if not patches:
        raise ValueError('没有需要修改的字符')
    metrics=dict(patches[0]['metrics'])
    metrics.update({'regionCount':len(patches),'changed_char_indices':[i for r in changes for i in r['changed_char_indices']],
        'regions':[p['region'] for p in patches],
        'stableFragment':any(bool(r.get('stableFragment')) for r in changes),
        'replacementFragments':[{'old':r['old'],'new':r['new'],'indices':r.get('replacement_char_indices',[])} for r in changes],
        'changed_pixel_count':sum(p['metrics']['changed_pixel_count'] for p in patches),
        'overall_match_score':min(p['metrics']['overall_match_score'] for p in patches),
        'qualityWarning':next((p['metrics']['qualityWarning'] for p in patches if p['metrics'].get('qualityWarning')),''),
        'glyphOnly':all(p['metrics']['glyphOnly'] for p in patches)})
    return {**patches[0],'patches':patches,'metrics':metrics}
