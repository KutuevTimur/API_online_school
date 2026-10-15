from pathlib import Path

from PIL import Image

from src.modules.handlers_files.normalize_photo import normalize_photo


def test_orientation_transparency_metadata_no_upscale(tmp_path: Path):
    source, dest = tmp_path/'source.png', tmp_path/'photo.webp'
    image = Image.new('RGBA',(80,120),(0,0,0,0))
    exif = Image.Exif(); exif[274] = 6; exif[270] = 'private description'
    image.save(source, exif=exif)
    normalize_photo(source,dest)
    with Image.open(dest) as result:
        assert result.size == (120,80) and result.format == 'WEBP'
        assert result.getexif() == {} and not result.info.get('icc_profile') and not result.info.get('xmp')
        assert min(result.getpixel((20,20))) > 250


def test_long_side_and_aspect_ratio(tmp_path: Path):
    source, dest = tmp_path/'source.png', tmp_path/'photo.webp'
    Image.new('RGB',(4000,3000),'white').save(source)
    normalize_photo(source,dest)
    with Image.open(dest) as result:
        assert result.size == (2560,1920)
