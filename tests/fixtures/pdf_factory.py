"""Generate original, deterministic fixtures without external files or font programs."""
import pymupdf as fitz


def electronic_bytes():
    doc = fitz.open()
    page = doc.new_page(width=420, height=300)
    page.insert_text((32, 42), 'TEST-A', fontsize=18)
    page.insert_text((32, 166), '123', fontsize=28)
    page.insert_text((230, 166), '456', fontsize=28)
    data = doc.tobytes(garbage=4, deflate=True, no_new_id=True)
    doc.close()
    return data


def scanned_bytes():
    # Original seven-segment geometric artwork. No text, font, image or model input.
    vector = fitz.open()
    page = vector.new_page(width=420, height=300)
    page.draw_rect(page.rect, color=None, fill=(0.96, 0.97, 0.98))
    for y in (110, 200):
        page.draw_line((32, y), (388, y), color=(0.5, 0.65, 0.7), width=0.5)
    segments = {
        'a': (3, 2, 13, 5), 'b': (12, 4, 15, 13),
        'c': (12, 14, 15, 23), 'd': (3, 22, 13, 25),
        'e': (1, 14, 4, 23), 'f': (1, 4, 4, 13), 'g': (3, 12, 13, 15),
    }
    active = {'1': 'bc', '2': 'abdeg', '3': 'abcdg',
              '4': 'bcfg', '5': 'acdfg', '6': 'acdefg'}
    boxes = []
    for text, start in [('123', 70), ('456', 240)]:
        chars = []
        for index, char in enumerate(text):
            x, y = start + index * 20, 145
            for segment in active[char]:
                a, b, c, d = segments[segment]
                page.draw_rect((x+a, y+b, x+c, y+d), color=None, fill=(0.15, 0.15, 0.15))
            chars.append({'c': char, 'bbox': [x, y, x+17, y+27], 'geometry': 'character'})
        boxes.append({'text': text, 'bbox': [start, 145, start+57, 172], 'chars': chars})
    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
    scan = fitz.open()
    image_page = scan.new_page(width=420, height=300)
    image_page.insert_image(image_page.rect, stream=pix.tobytes('png'))
    data = scan.tobytes(garbage=4, deflate=True, no_new_id=True)
    scan.close()
    vector.close()
    return data, boxes
