import io
from typing import Callable, Tuple
import pytest
from fastapi import UploadFile
from PIL import Image


@pytest.fixture
def create_upload_file_fixture() -> Callable[[bytes, str], UploadFile]:
    """Фикстура-генератор UploadFile из байтов"""
    def _create(content: bytes, filename: str) -> UploadFile:
        return UploadFile(
            file=io.BytesIO(content),
            filename=filename,
        )
    return _create


@pytest.fixture
def create_image_bytes_fixture() -> Callable[..., bytes]:
    """Фикстура-генератор байтов тестового изображения"""
    def _create(
        format_: str = "PNG",
        size: Tuple[int, int] = (100, 100),
        color: str = "red",
    ) -> bytes:
        img = Image.new("RGB", size, color=color)
        buf = io.BytesIO()
        img.save(buf, format=format_)
        return buf.getvalue()
    return _create
