import io
from pathlib import Path
import pytest
from fastapi import UploadFile
from PIL import Image

from src.core.config.config import Config
from src.modules.handlers_files.converter_images import HandlerImages
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
def handler_images(config: Config) -> HandlerImages:
    return HandlerImages(config=config)


@pytest.mark.asyncio
async def test_convert_jpg_to_webp(handler_images: HandlerImages, tmp_path: Path, config: Config):
    img = Image.new("RGB", (120, 80), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    upload_file = _create_upload_file(buf.getvalue(), "test_photo.jpg")

    dest_dir = tmp_path / "output"
    dest_dir.mkdir(parents=True, exist_ok=True)

    result_path = await handler_images.convert_to_webp(upload_file, dest_dir)

    assert result_path.exists()
    assert result_path.suffix == ".webp"
    assert result_path.name == "test_photo.webp"

    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert converted_img.size == (120, 80)

    assert list(config.paths.temp.iterdir()) == []


@pytest.mark.asyncio
async def test_convert_case_insensitive_extension(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    upload_file = _create_upload_file(buf.getvalue(), "UPPERCASE_EXTENSION.JPEG")

    dest_file = tmp_path / "result.webp"
    result_path = await handler_images.convert_to_webp(upload_file, dest_file)

    assert result_path.exists()
    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"


@pytest.mark.asyncio
async def test_convert_png_with_alpha_to_webp(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    upload_file = _create_upload_file(buf.getvalue(), "transparent.png")

    dest_file = tmp_path / "custom_name.webp"

    result_path = await handler_images.convert_to_webp(upload_file, dest_file)

    assert result_path.exists()
    assert result_path == dest_file.resolve()

    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert converted_img.size == (50, 50)
        assert converted_img.mode == "RGBA"


@pytest.mark.asyncio
async def test_convert_cmyk_to_webp(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("CMYK", (70, 70), color=(100, 50, 0, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    upload_file = _create_upload_file(buf.getvalue(), "cmyk_image.jpeg")

    dest_file = tmp_path / "cmyk_converted.webp"
    result_path = await handler_images.convert_to_webp(upload_file, dest_file)

    assert result_path.exists()
    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert converted_img.mode == "RGB"


@pytest.mark.asyncio
async def test_convert_grayscale_to_webp(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("L", (80, 80), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    upload_file = _create_upload_file(buf.getvalue(), "grayscale.png")

    dest_file = tmp_path / "grayscale.webp"
    result_path = await handler_images.convert_to_webp(upload_file, dest_file)

    assert result_path.exists()
    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"


@pytest.mark.asyncio
async def test_convert_animated_gif_to_webp(handler_images: HandlerImages, tmp_path: Path):
    frame1 = Image.new("RGB", (60, 60), color="red")
    frame2 = Image.new("RGB", (60, 60), color="green")
    frame3 = Image.new("RGB", (60, 60), color="blue")
    buf = io.BytesIO()
    frame1.save(buf, format="GIF", save_all=True, append_images=[frame2, frame3], duration=100, loop=0)
    upload_file = _create_upload_file(buf.getvalue(), "animation.gif")

    dest_dir = tmp_path / "gifs"

    result_path = await handler_images.convert_to_webp(upload_file, dest_dir)

    assert result_path.exists()
    assert result_path.suffix == ".webp"

    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert getattr(converted_img, "is_animated", False)
        assert converted_img.n_frames == 3


@pytest.mark.asyncio
async def test_convert_heif_to_webp(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("RGB", (80, 80), color="yellow")
    buf = io.BytesIO()
    img.save(buf, format="HEIF")
    upload_file = _create_upload_file(buf.getvalue(), "iphone_photo.heic")

    dest_dir = tmp_path / "heic_out"

    result_path = await handler_images.convert_to_webp(upload_file, dest_dir)

    assert result_path.exists()
    assert result_path.suffix == ".webp"

    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert converted_img.size == (80, 80)


@pytest.mark.asyncio
async def test_convert_webp_to_webp(handler_images: HandlerImages, tmp_path: Path):
    img = Image.new("RGB", (40, 40), color="cyan")
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    upload_file = _create_upload_file(buf.getvalue(), "original.webp")

    dest_file = tmp_path / "nested" / "reencoded.webp"

    result_path = await handler_images.convert_to_webp(upload_file, dest_file)

    assert result_path.exists()
    with Image.open(result_path) as converted_img:
        assert converted_img.format == "WEBP"
        assert converted_img.size == (40, 40)


@pytest.mark.asyncio
async def test_unsupported_extension_raises_exception(handler_images: HandlerImages, tmp_path: Path):
    upload_file = _create_upload_file(b"some content", "document.pdf")

    with pytest.raises(InvalidImageFormat) as exc_info:
        await handler_images.convert_to_webp(upload_file, tmp_path)

    assert "Недопустимый формат" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_extension_raises_exception(handler_images: HandlerImages, tmp_path: Path):
    upload_file = _create_upload_file(b"some content", "noextension")

    with pytest.raises(InvalidImageFormat):
        await handler_images.convert_to_webp(upload_file, tmp_path)


@pytest.mark.asyncio
async def test_corrupt_file_raises_exception_and_cleans_temp(
    handler_images: HandlerImages,
    tmp_path: Path,
    config: Config,
):
    upload_file = _create_upload_file(b"this is not a valid image", "corrupt.jpg")

    with pytest.raises(InvalidImageFormat):
        await handler_images.convert_to_webp(upload_file, tmp_path)

    assert list(config.paths.temp.iterdir()) == []


@pytest.mark.asyncio
async def test_empty_file_raises_exception(handler_images: HandlerImages, tmp_path: Path, config: Config):
    upload_file = _create_upload_file(b"", "empty.png")

    with pytest.raises(InvalidImageFormat):
        await handler_images.convert_to_webp(upload_file, tmp_path)

    assert list(config.paths.temp.iterdir()) == []
