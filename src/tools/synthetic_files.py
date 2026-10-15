"""Small deterministic valid synthetic PDFs for local tests and HTTP smoke."""
from io import BytesIO
from pypdf import PdfWriter


def pdf_bytes(label: str = 'synthetic') -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({'/Title': label})
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()
