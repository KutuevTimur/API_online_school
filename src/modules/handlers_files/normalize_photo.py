"""D06 photo candidate; no file deletion or ownership decisions in this module."""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms, ImageOps


def normalize_photo(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        alpha = image.getchannel('A') if 'A' in image.getbands() else None
        if image.mode == 'P' and 'transparency' in image.info:
            image = image.convert('RGBA')
            alpha = image.getchannel('A')
        profile = image.info.get('icc_profile')
        rgb = image.convert('RGB')
        if profile:
            # A malformed profile fails in the bounded worker, rather than silently
            # assigning sRGB to unconverted pixels.
            input_profile = ImageCms.ImageCmsProfile(BytesIO(profile))
            profile_image = image if image.mode in ('RGB', 'CMYK', 'LAB', 'L') else rgb
            rgb = ImageCms.profileToProfile(profile_image, input_profile, ImageCms.createProfile('sRGB'), outputMode='RGB')
        if alpha is not None:
            white = Image.new('RGB', rgb.size, 'white')
            white.paste(rgb, mask=alpha)
            rgb = white
        rgb.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
        # New pixel-only image drops EXIF/GPS/XMP/comments and old ICC blobs.
        clean = Image.new('RGB', rgb.size)
        clean.paste(rgb)
        clean.save(destination, 'WEBP', quality=85, method=6, exif=b'', xmp=b'', icc_profile=b'')
