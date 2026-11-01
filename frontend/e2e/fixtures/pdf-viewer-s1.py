"""Build local HTTP fixtures for pdf-viewer-s1.spec.ts; never connects to API/DB."""
from pathlib import Path
from pypdf import PdfReader, PdfWriter

frontend = Path(__file__).resolve().parents[2]
target = frontend / '.artifacts' / 's1-pdf'
target.mkdir(parents=True, exist_ok=True)
source = PdfReader(frontend / 'e2e' / 'fixtures' / 'math.pdf')
for count in (1, 20, 100):
    writer = PdfWriter()
    for page in range(count):
        writer.add_page(source.pages[page % len(source.pages)])
    writer.write(target / f'{count}.pdf')
writer = PdfWriter()
writer.add_page(source.pages[0])
writer.encrypt('s1-fixture-password')
writer.write(target / 'password.pdf')
print('Created S1 local PDF fixtures; no API/DB writes')
