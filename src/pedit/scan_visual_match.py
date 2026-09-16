"""Local scan-style fitting for replacement glyphs.

v2.3.7 goals:
- preserve the proven v2.3.5/v2.3.6 character-diff workflow;
- fit replacement glyphs to a *local line style profile* rather than to one donor;
- score replacement stroke, edge softness, ink density and geometry;
- expose explicit quality metrics instead of treating source-glyph reconstruction as proof.

Only local source pixels and system fonts are used. No font files are bundled.
"""
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def glyph_mask(text, font):
    box = font.getbbox(text)
    im = Image.new('L', (max(1, box[2]-box[0])+12, max(1, box[3]-box[1])+12))
    ImageDraw.Draw(im).text((6-box[0], 6-box[1]), text, font=font, fill=255)
    return im.crop(im.getbbox()) if im.getbbox() else Image.new('L', (1, 1))


def _mask_stats(mask):
    """Measure visible glyph style on a normalized alpha mask."""
    arr = np.asarray(mask, dtype=np.float32) / 255.0
    visible = arr > 0.08
    core = arr > 0.50
    ys, xs = np.where(visible)
    if not len(xs):
        return {
            'width': 1, 'height': 1, 'stroke': 0.0, 'edgeSoftness': 0.0,
            'inkDensity': 0.0, 'coreOpacity': 0.0,
        }
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1
    crop = arr[y0:y1, x0:x1]
    core_crop = crop > 0.50
    if np.any(core_crop):
        dist = cv2.distanceTransform(core_crop.astype('uint8'), cv2.DIST_L2, 3)
        stroke = float(np.mean(dist[core_crop]))
    else:
        stroke = 0.0
    dil = cv2.dilate(core_crop.astype('uint8'), np.ones((3,3), np.uint8), iterations=1) > 0
    transition = dil & ~core_crop & (crop > 0.05)
    softness = float(np.count_nonzero(transition) / max(1, np.count_nonzero(core_crop)))
    density = float(np.count_nonzero(core_crop) / max(1, crop.shape[0] * crop.shape[1]))
    core_opacity = float(np.percentile(crop[core_crop], 90)) if np.any(core_crop) else float(np.max(crop))
    return {
        'width': int(x1-x0), 'height': int(y1-y0), 'stroke': stroke,
        'edgeSoftness': softness, 'inkDensity': density, 'coreOpacity': core_opacity,
    }


def _pct_score(actual, target, floor=1e-6):
    if target is None:
        return 100.0
    target = float(target)
    if abs(target) <= floor:
        return 100.0
    return max(0.0, 100.0 - 100.0 * abs(float(actual)-target) / max(abs(target), floor))


def _render_replacement_candidate(new, font, *, target_w, target_h, stroke, blur=0):
    """Render replacement glyph with one final downsample.

    v2.3.27 deliberately avoids the old resize -> blur -> resize chain.  The
    glyph is rasterised at 4x, optionally morphed at that scale, then reduced
    exactly once to the native target pixel grid.  `blur` is accepted for API
    compatibility but automatic replacement rendering ignores it.
    """
    if not new:
        return Image.new('L', (1, max(1, int(round(target_h)))))
    try:
        path = getattr(font, 'path', None)
        hi_font = ImageFont.truetype(path, max(4, int(round(font.size * 4)))) if path else font
    except Exception:
        hi_font = font
    raw = glyph_mask(new, hi_font)
    shaped = raw
    # Morphology happens in supersampled pixels so the final effect remains
    # subtle instead of creating chunky native-pixel edges.
    if stroke < 0:
        shaped = shaped.filter(ImageFilter.MinFilter(3))
    elif stroke > 0:
        shaped = shaped.filter(ImageFilter.MaxFilter(3))
    arr = np.asarray(shaped)
    ys, xs = np.where(arr > 16)
    if len(xs):
        shaped = shaped.crop((int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1))
    shaped = shaped.resize((max(1, int(round(target_w))), max(1, int(round(target_h)))), Image.Resampling.LANCZOS)
    padded = Image.new('L', (shaped.width+8, shaped.height+8))
    padded.paste(shaped, (4,4))
    return padded


def _style_optimized_mask(new, font, base_stroke, base_blur, reference_style):
    """Search a small deterministic neighbourhood around the local line profile."""
    target_w = int(reference_style.get('targetInkWidthPx') or max(1, glyph_mask(new, font).width))
    target_h = int(reference_style.get('targetInkHeightPx') or max(1, glyph_mask(new, font).height))
    target_stroke = reference_style.get('digitStrokeMetric')
    target_soft = reference_style.get('digitEdgeSoftnessMetric')
    target_density = reference_style.get('digitInkDensityMetric')

    widths = sorted(set(max(1, int(round(target_w * f))) for f in (0.94, 0.98, 1.0, 1.02, 1.06)))
    heights = sorted(set(max(1, int(round(target_h * f))) for f in (0.97, 1.0, 1.03)))
    strokes = sorted(set(int(x) for x in (base_stroke-1, base_stroke, base_stroke+1) if -1 <= int(x) <= 1))
    # v2.3.27: never search blur for the replacement glyph. Source matching may
    # estimate optical softness, but new text stays sharp on the native scan grid.
    blur_values = (0.0,)

    best = None
    for w in widths:
        for h in heights:
            for stroke in strokes:
                for blur in blur_values:
                    mask = _render_replacement_candidate(new, font, target_w=w, target_h=h, stroke=stroke, blur=blur)
                    stats = _mask_stats(mask)
                    width_score = _pct_score(stats['width'], target_w)
                    height_score = _pct_score(stats['height'], target_h)
                    stroke_score = _pct_score(stats['stroke'], target_stroke)
                    edge_score = _pct_score(stats['edgeSoftness'], target_soft)
                    density_score = _pct_score(stats['inkDensity'], target_density)
                    style_score = (
                        0.24*width_score + 0.20*height_score + 0.22*stroke_score +
                        0.20*edge_score + 0.14*density_score
                    )
                    candidate = (style_score, mask, stats, stroke, blur)
                    if best is None or candidate[0] > best[0]:
                        best = candidate
    return best


def fit_source(old, new, crop, ink_box, paths, reference_style=None):
    x0, y0, x1, y1 = ink_box
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY).astype(float)
    region = gray[y0:y1, x0:x1]
    h, w = region.shape
    bg = np.percentile(crop.reshape(-1, 3), 85, axis=0)
    dark = region[region < min(175, np.percentile(region, 80)-35)]
    fg = float(np.percentile(dark, 1)) if dark.size else 55.0
    source = np.clip((float(np.mean(bg))-region) / max(20, float(np.mean(bg))-fg), 0, 1)

    best = None
    for path in paths:
        for size in range(max(5, int(h*1.15)), max(7, int(h*1.85)), max(1, int(h*.09))):
            font = ImageFont.truetype(path, size)
            raw = glyph_mask(old, font)
            sx = (w-2)/max(1, raw.width)
            sy = (h-2)/max(1, raw.height)
            if not .45 < sx/sy < 1.8:
                continue
            base = Image.new('L', (w, h))
            base.paste(raw.resize((max(1, w-2), max(1, h-2)), Image.Resampling.LANCZOS), (1,1))
            for stroke in (-1,0,1):
                shaped = base.filter(ImageFilter.MinFilter(3)) if stroke < 0 else base.filter(ImageFilter.MaxFilter(3)) if stroke > 0 else base
                for blur in (0, .45, .9, 1.4, 2.0):
                    candidate = shaped.filter(ImageFilter.GaussianBlur(blur)) if blur else shaped
                    arr = np.asarray(candidate)/255.0
                    loss = float(np.mean((arr-source)**2))
                    if best is None or loss < best[0]:
                        best = (loss, path, font, sx, sy, stroke, blur, arr)
    if best is None:
        raise ValueError('未找到可匹配源字符的字体候选')

    loss, path, font, sx, sy, stroke, blur, fitted = best
    source_blur_estimate=float(blur)
    if reference_style:
        ref_font_name = reference_style.get('font')
        ref_path = next((p for p in paths if Path(p).name == ref_font_name), None)
        if ref_path:
            path = ref_path
            ref_size = int(reference_style.get('fontSizePx') or font.size)
            font = ImageFont.truetype(path, max(4, ref_size))
        sx = float(reference_style.get('horizontalScale', sx))
        sy = float(reference_style.get('verticalScale', sy))
        stroke = int(reference_style.get('strokeAdjustmentPx', stroke))
        # Keep source reconstruction blur as a diagnostic only; do not carry it
        # into replacement generation.
        source_blur_estimate=float(reference_style.get('blurRadiusPx',source_blur_estimate) or source_blur_estimate)

    # Replacement rendering is always neutral-sharp by default.
    blur=0.0

    # Replacement generation: with a row profile, optimize the new glyph itself
    # against nearby scanned digits.  Without one, keep the legacy fitted path.
    replacement_style_score = None
    replacement_stats = None
    if reference_style and len(str(new)) == 1 and str(new).isdigit() and reference_style.get('targetInkWidthPx'):
        optimized = _style_optimized_mask(str(new), font, stroke, blur, reference_style)
        replacement_style_score, mask, replacement_stats, stroke, blur = optimized
    else:
        raw = glyph_mask(new, font) if new else Image.new('L', (1, h))
        target_w=max(1, round(raw.width*sx)); target_h=max(1, round(raw.height*sy))
        mask = _render_replacement_candidate(new, font, target_w=target_w, target_h=target_h, stroke=stroke, blur=0) if new else raw
        blur = 0.0

    # Match source core opacity without making the whole replacement translucent.
    mask_arr = np.asarray(mask, dtype=float)
    rendered_core = mask_arr[mask_arr > 8]
    source_core = source[source > .05]
    alpha_gain = 1.0
    if rendered_core.size and source_core.size:
        desired = float(np.percentile(source_core, 95))*255.0
        current = float(np.percentile(rendered_core, 95))
        if current > 0:
            alpha_gain = max(.78, min(2.5, desired/current))
            if abs(alpha_gain-1.0) > .01:
                mask = Image.fromarray(np.clip(mask_arr*alpha_gain, 0, 255).astype('uint8'))

    src_stroke = float(np.mean(cv2.distanceTransform((source>.5).astype('uint8'), cv2.DIST_L2, 3)[source>.5])) if np.any(source>.5) else 0.0
    dst_stroke = float(np.mean(cv2.distanceTransform((fitted>.5).astype('uint8'), cv2.DIST_L2, 3)[fitted>.5])) if np.any(fitted>.5) else 0.0
    geom = max(0.0, 100.0*(1-np.sqrt(loss)))
    stroke_score = max(0.0, 100.0-100.0*abs(src_stroke-dst_stroke)/max(1.0, src_stroke))
    sharp = lambda a: float(np.mean(np.abs(cv2.Laplacian(a.astype('float32'), cv2.CV_32F))))
    sharp_score = max(0.0, 100.0-100.0*abs(sharp(source)-sharp(fitted))/max(.01, sharp(source)))
    source_score = round(.60*geom + .20*stroke_score + .20*sharp_score, 1)

    ink_pixels = crop[y0:y1, x0:x1][region < fg+5]
    rgb = np.median(ink_pixels, axis=0) if len(ink_pixels) else np.repeat(fg, 3)
    if reference_style and reference_style.get('foregroundRGB'):
        rgb = np.asarray(reference_style['foregroundRGB'], dtype=float)
    noise = float(np.std(gray-cv2.GaussianBlur(gray, (0,0), 1)))

    if replacement_style_score is None:
        replacement_style_score = source_score
        replacement_stats = _mask_stats(mask)
    overall = round(0.45*source_score + 0.55*float(replacement_style_score), 1)
    warning = '视觉匹配质量不足' if overall < 82 else ''

    return mask, rgb, {
        'font': Path(path).name, 'fontSizePx': font.size,
        'horizontalScale': round(sx, 3), 'verticalScale': round(sy, 3),
        'trackingPx': 0.0, 'strokeAdjustmentPx': int(stroke),
        'blurRadiusPx': 0.0, 'sourceBlurEstimatePx': round(float(source_blur_estimate),2), 'foregroundRGB': [round(float(x),1) for x in rgb],
        'backgroundRGB': [round(float(x),1) for x in bg], 'noiseLevel': round(noise,2),
        'geometry_score': round(geom,1), 'stroke_score': round(stroke_score,1),
        'sharpness_score': round(sharp_score,1), 'source_reconstruction_score': source_score,
        'replacement_style_score': round(float(replacement_style_score),1),
        'replacementStrokeMetric': round(float(replacement_stats.get('stroke',0.0)),3),
        'replacementEdgeSoftnessMetric': round(float(replacement_stats.get('edgeSoftness',0.0)),3),
        'replacementInkDensityMetric': round(float(replacement_stats.get('inkDensity',0.0)),3),
        'overall_match_score': overall,
        'scoreBasis': 'source reconstruction + same-row replacement style profile',
        'qualityWarning': warning,
        'scanSkew': 'not estimated; axis-aligned glyph fitting',
        'referenceCharacter': reference_style.get('referenceCharacter') if reference_style else None,
        'targetInkWidthPx': reference_style.get('targetInkWidthPx') if reference_style else None,
        'targetInkHeightPx': reference_style.get('targetInkHeightPx') if reference_style else None,
        'styleProfile': reference_style.get('styleProfile') if reference_style else None,
        'styleConfidence': reference_style.get('styleConfidence') if reference_style else None,
        'digitProfileCount': reference_style.get('digitProfileCount') if reference_style else None,
        'digitProfileCharacters': reference_style.get('digitProfileCharacters') if reference_style else None,
        'digitStrokeMetric': reference_style.get('digitStrokeMetric') if reference_style else None,
        'digitEdgeSoftnessMetric': reference_style.get('digitEdgeSoftnessMetric') if reference_style else None,
        'digitInkDensityMetric': reference_style.get('digitInkDensityMetric') if reference_style else None,
        'digitContrastMetric': reference_style.get('digitContrastMetric') if reference_style else None,
        'exemplarPolicy': reference_style.get('exemplarPolicy') if reference_style else None,
        'alphaCoreGain': round(alpha_gain,3),
    }
