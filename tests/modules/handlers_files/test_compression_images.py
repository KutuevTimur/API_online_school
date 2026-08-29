import io
from pathlib import Path
import pytest
from fastapi import UploadFile
from PIL import Image

from src.core.config.config import Config
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.exception import InvalidImageFormat


def _create_upload_file(content: bytes, filename: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
    )


@pytest.fixture
def config(tmp_path: Path) -> Config:
    conf = Config()
    conf.paths.temp = tmp_path / "temp"
    conf.paths.temp.mkdir(parents=True, exist_ok=True)
    return conf


@pytest.fixture
def compression_service(config: Config) -> CompressionImages:
    return CompressionImages(config=config)


@pytest.mark.asyncio
async def test_compress_large_webp_to_512(compression_service: CompressionImages, tmp_path: Path):
    # Создаем WebP 1920x1080
    img = Image.new("RGB", (1920, 1080), color="blue")
    input_file = tmp_path / "source.webp"
    img.save(input_file, format="WEBP")

    dest_file = tmp_path / "compressed.webp"
    result_path = await compression_service.compress_webp(input_file, dest=dest_file)

    assert result_path.exists()
    assert result_path == dest_file.resolve()

    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size[0] <= 512
        assert res_img.size[1] <= 512
        # Пропорция 1920x1080 -> 512x288
        assert res_img.size == (512, 288)


@pytest.mark.asyncio
async def test_compress_upload_file_square_webp(compression_service: CompressionImages, tmp_path: Path):
    img = Image.new("RGBA", (1024, 1024), color=(255, 0, 0, 200))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    upload_file = _create_upload_file(buf.getvalue(), "square.webp")

    dest_dir = tmp_path / "output_dir"
    result_path = await compression_service.compress_webp(upload_file, dest=dest_dir)

    assert result_path.exists()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size == (512, 512)
        assert res_img.mode == "RGBA"


@pytest.mark.asyncio
async def test_compress_in_place(compression_service: CompressionImages, tmp_path: Path):
    img = Image.new("RGB", (800, 600), color="green")
    file_path = tmp_path / "inplace.webp"
    img.save(file_path, format="WEBP")

    result_path = await compression_service.compress_webp(file_path, dest=None)

    assert result_path == file_path.resolve()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size == (512, 384)


@pytest.mark.asyncio
async def test_compress_animated_webp(compression_service: CompressionImages, tmp_path: Path):
    f1 = Image.new("RGB", (1000, 1000), color="red")
    f2 = Image.new("RGB", (1000, 1000), color="blue")
    buf = io.BytesIO()
    f1.save(buf, format="WEBP", save_all=True, append_images=[f2], duration=150, loop=0)
    upload_file = _create_upload_file(buf.getvalue(), "anim.webp")

    dest_file = tmp_path / "compressed_anim.webp"
    result_path = await compression_service.compress_webp(upload_file, dest=dest_file)

    assert result_path.exists()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert getattr(res_img, "is_animated", False)
        assert res_img.n_frames == 2
        assert res_img.size == (512, 512)


@pytest.mark.asyncio
async def test_reject_non_webp_extension(compression_service: CompressionImages, tmp_path: Path):
    upload_file = _create_upload_file(b"some content", "image.png")

    with pytest.raises(InvalidImageFormat) as exc_info:
        await compression_service.compress_webp(upload_file, tmp_path)

    assert "поддерживается только формат .webp" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reject_corrupt_webp(compression_service: CompressionImages, tmp_path: Path, config: Config):
    upload_file = _create_upload_file(b"corrupted webp data", "corrupt.webp")

    with pytest.raises(InvalidImageFormat):
        await compression_service.compress_webp(upload_file, tmp_path)

    assert list(config.paths.temp.iterdir()) == []


@pytest.mark.asyncio
async def test_reject_empty_file(compression_service: CompressionImages, tmp_path: Path):
    upload_file = _create_upload_file(b"", "empty.webp")

    with pytest.raises(InvalidImageFormat):
        await compression_service.compress_webp(upload_file, tmp_path)
