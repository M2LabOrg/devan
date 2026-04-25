import sys
from docling.document_converter import DocumentConverter

if len(sys.argv) < 2:
    sys.exit("Usage: python _test_docling.py <pdf_path>")

converter = DocumentConverter()
result = converter.convert(sys.argv[1])
md = result.document.export_to_markdown()
print(f'Content length: {len(md)}')
print(md[:1000])
