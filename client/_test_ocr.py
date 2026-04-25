import sys
import pymupdf
from rapidocr_onnxruntime import RapidOCR

if len(sys.argv) < 2:
    sys.exit("Usage: python _test_ocr.py <pdf_path>")

ocr = RapidOCR()
doc = pymupdf.open(sys.argv[1])

# Test on first page: render to image, then OCR
page = doc[0]
pix = page.get_pixmap(dpi=200)
img_bytes = pix.tobytes("png")

result, elapse = ocr(img_bytes)
if result:
    text = '\n'.join([line[1] for line in result])
    print(f'OCR text length: {len(text)}')
    print(text[:800])
else:
    print('No text found via OCR')
doc.close()
