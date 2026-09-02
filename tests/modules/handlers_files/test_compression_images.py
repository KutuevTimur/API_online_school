import io
from pathlib import Path
import pytest
from PIL import Image

from src.core.config.config import Config
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.exception import InvalidImageFormat


@pytest.mark.asyncio
async def test_compress_large_webp_to_512(
    compression_images_fixture: CompressionImages,
    tmp_path: Path,
):
    # Создаем WebP 1920x1080
    img = Image.new("RGB", (1920, 1080), color="blue")
    input_file = tmp_path / "source.webp"
    img.save(input_file, format="WEBP")

    dest_file = tmp_path / "compressed.webp"
    result_path = await compression_images_fixture.compress_webp(input_file, dest=dest_file)

    assert result_path.exists()
    assert result_path == dest_file.resolve()

    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size[0] <= 512
        assert res_img.size[1] <= 512
        # Пропорция 1920x1080 -> 512x288
        assert res_img.size == (512, 288)


@pytest.mark.asyncio
async def test_compress_upload_file_square_webp(
    compression_images_fixture: CompressionImages,
    create_upload_file_fixture,
    create_image_bytes_fixture,
    tmp_path: Path,
):
    img_bytes = create_image_bytes_fixture(format_="WEBP", size=(1024, 1024), color="red")
    upload_file = create_upload_file_fixture(img_bytes, "square.webp")

    dest_dir = tmp_path / "output_dir"
    result_path = await compression_images_fixture.compress_webp(upload_file, dest=dest_dir)

    assert result_path.exists()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size == (512, 512)


@pytest.mark.asyncio
async def test_compress_in_place(
    compression_images_fixture: CompressionImages,
    tmp_path: Path,
):
    img = Image.new("RGB", (800, 600), color="green")
    file_path = tmp_path / "inplace.webp"
    img.save(file_path, format="WEBP")

    result_path = await compression_images_fixture.compress_webp(file_path, dest=None)

    assert result_path == file_path.resolve()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert res_img.size == (512, 384)


@pytest.mark.asyncio
async def test_compress_animated_webp(
    compression_images_fixture: CompressionImages,
    create_upload_file_fixture,
    tmp_path: Path,
):
    f1 = Image.new("RGB", (1000, 1000), color="red")
    f2 = Image.new("RGB", (1000, 1000), color="blue")
    buf = io.BytesIO()
    f1.save(buf, format="WEBP", save_all=True, append_images=[f2], duration=150, loop=0)
    upload_file = create_upload_file_fixture(buf.getvalue(), "anim.webp")

    dest_file = tmp_path / "compressed_anim.webp"
    result_path = await compression_images_fixture.compress_webp(upload_file, dest=dest_file)

    assert result_path.exists()
    with Image.open(result_path) as res_img:
        assert res_img.format == "WEBP"
        assert getattr(res_img, "is_animated", False)
        assert res_img.n_frames == 2
        assert res_img.size == (512, 512)


@pytest.mark.asyncio
async def test_reject_non_webp_extension(
    compression_images_fixture: CompressionImages,
    create_upload_file_fixture,
    tmp_path: Path,
):
    upload_file = create_upload_file_fixture(b"some content", "image.png")

    with pytest.raises(InvalidImageFormat) as exc_info:
        await compression_images_fixture.compress_webp(upload_file, tmp_path)

    assert "поддерживается только формат .webp" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reject_corrupt_webp(
    compression_images_fixture: CompressionImages,
    create_upload_file_fixture,
    tmp_path: Path,
    config_fix: Config,
):
    upload_file = create_upload_file_fixture(b"corrupted webp data", "corrupt.webp")

    with pytest.raises(InvalidImageFormat):
        await compression_images_fixture.compress_webp(upload_file, tmp_path)

    assert not any(p.name.startswith("temp_") for p in config_fix.paths.temp.iterdir())


@pytest.mark.asyncio
async def test_reject_empty_file(
    compression_images_fixture: CompressionImages,
    create_upload_file_fixture,
    tmp_path: Path,
):
    upload_file = create_upload_file_fixture(b"", "empty.webp")

    with pytest.raises(InvalidImageFormat):
        await compression_images_fixture.compress_webp(upload_file, tmp_path)
