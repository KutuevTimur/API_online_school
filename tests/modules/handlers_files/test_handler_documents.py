import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.handlers_files.exception import InvalidDocumentFormat, DocumentConversionError


def test_validate_extension_success(handler_documents_fixture: HandlerDocuments):
    assert handler_documents_fixture._validate_extension("doc.pdf") == "pdf"
    assert handler_documents_fixture._validate_extension("file.DOCX") == "docx"
    assert handler_documents_fixture._validate_extension("image.jpg") == "jpg"


def test_validate_extension_raises_invalid_format(handler_documents_fixture: HandlerDocuments):
    with pytest.raises(InvalidDocumentFormat):
        handler_documents_fixture._validate_extension("no_ext")
        
    with pytest.raises(InvalidDocumentFormat):
        handler_documents_fixture._validate_extension("bad.exe")


@pytest.mark.asyncio
async def test_convert_image_to_pdf(
    handler_documents_fixture: HandlerDocuments,
    tmp_path: Path
):
    img = Image.new("RGB", (100, 100), color="blue")
    source_img = tmp_path / "source.jpg"
    dest_pdf = tmp_path / "dest.pdf"
    
    img.save(source_img, "JPEG")
    
    await handler_documents_fixture._convert_image_to_pdf(source_img, dest_pdf)
    
    assert dest_pdf.exists()
    assert dest_pdf.stat().st_size > 0


@pytest.mark.asyncio
async def test_convert_doc_to_pdf_libreoffice_success(
    handler_documents_fixture: HandlerDocuments,
    tmp_path: Path
):
    source_doc = tmp_path / "document.docx"
    source_doc.write_text("dummy")
    dest_pdf = tmp_path / "document.pdf"
    
    # Мокаем вызов subprocess
    async def mock_communicate():
        dest_pdf.parent.mkdir(parents=True, exist_ok=True)
        dest_pdf.write_text("mocked pdf content")
        return b"success", b""
        
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = mock_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        await handler_documents_fixture._convert_doc_to_pdf_libreoffice(source_doc, dest_pdf)
        
    assert dest_pdf.exists()
    assert dest_pdf.read_text() == "mocked pdf content"


@pytest.mark.asyncio
async def test_save_document_pdf_copies_directly(
    handler_documents_fixture: HandlerDocuments,
    create_upload_file_fixture,
    tmp_path: Path
):
    content = b"fake pdf content"
    upload_file = create_upload_file_fixture(content, "test.pdf")
    
    original_dest = tmp_path / "originals" / "test.pdf"
    pdf_dest = tmp_path / "pdfs" / "test.pdf"
    
    res_orig, res_pdf = await handler_documents_fixture.save_document(upload_file, original_dest, pdf_dest)
    
    assert res_orig == original_dest
    assert res_pdf == pdf_dest
    
    assert original_dest.exists()
    assert pdf_dest.exists()
    assert pdf_dest.read_bytes() == content


@pytest.mark.asyncio
async def test_save_document_image_converts(
    handler_documents_fixture: HandlerDocuments,
    create_upload_file_fixture,
    tmp_path: Path
):
    # Создаем настоящую картинку в памяти, чтобы PIL прожевал
    img = Image.new("RGB", (50, 50), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    
    upload_file = create_upload_file_fixture(buf.getvalue(), "photo.jpg")
    
    original_dest = tmp_path / "originals" / "photo.jpg"
    pdf_dest = tmp_path / "pdfs" / "photo.pdf"
    
    await handler_documents_fixture.save_document(upload_file, original_dest, pdf_dest)
    
    assert original_dest.exists()
    assert pdf_dest.exists()
    
    # Проверяем, что исходник - это jpeg, а получатель - pdf (просто по размеру и существованию)
    assert original_dest.read_bytes() == buf.getvalue()
    assert pdf_dest.stat().st_size > 0


@pytest.mark.asyncio
async def test_save_document_doc_converts_mocked(
    handler_documents_fixture: HandlerDocuments,
    create_upload_file_fixture,
    tmp_path: Path
):
    content = b"fake doc content"
    upload_file = create_upload_file_fixture(content, "document.docx")
    
    original_dest = tmp_path / "originals" / "document.docx"
    pdf_dest = tmp_path / "pdfs" / "document.pdf"
    
    async def mock_communicate():
        pdf_dest.parent.mkdir(parents=True, exist_ok=True)
        pdf_dest.write_text("mocked pdf")
        return b"ok", b""
        
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = mock_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        await handler_documents_fixture.save_document(upload_file, original_dest, pdf_dest)
        
    assert original_dest.exists()
    assert original_dest.read_bytes() == content
    assert pdf_dest.exists()
    assert pdf_dest.read_text() == "mocked pdf"
