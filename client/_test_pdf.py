import sys
import pymupdf

if len(sys.argv) < 2:
    sys.exit("Usage: python _test_pdf.py <pdf_path>")

doc = pymupdf.open(sys.argv[1])
page = doc[0]
blocks = page.get_text('dict')['blocks']
print(f'Total blocks: {len(blocks)}')
for i, b in enumerate(blocks[:10]):
    btype = b['type']
    if btype == 0:
        texts = []
        for line in b.get('lines', []):
            for span in line.get('spans', []):
                texts.append(span['text'])
        print(f'  Block {i}: TEXT "{" ".join(texts)[:100]}"')
    else:
        print(f'  Block {i}: IMAGE {b.get("width","?")}x{b.get("height","?")}')
doc.close()
