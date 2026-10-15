"""Bounded child process. No network, file contents or decoder errors on stdout."""
import json
import resource
import sys
import warnings
from pathlib import Path


def inspect(source: Path, extension: str) -> dict[str, str]:
    if extension == 'pdf':
        from pypdf import PdfReader
        with source.open('rb') as stream:
            if stream.read(5) != b'%PDF-':
                raise ValueError('signature')
            stream.seek(0)
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted or not reader.pages:
                raise ValueError('encrypted/empty PDF')
        return {'mime': 'application/pdf'}
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    Image.MAX_IMAGE_PIXELS = 50_000_000
    warnings.simplefilter('error', Image.DecompressionBombWarning)
    allowed = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'heic': 'HEIF', 'heif': 'HEIF'}
    with Image.open(source) as image:
        if image.format != allowed.get(extension) or image.width * image.height > 50_000_000:
            raise ValueError('format/pixels')
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('animated image')
        image.verify()
    # Decode too: verify() is a no-op for some formats.
    with Image.open(source) as image:
        image.load()
    return {'mime': {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp', 'HEIF': 'image/heif'}[allowed[extension]]}


if __name__ == '__main__':
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (25, 25))
        resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))
        # macOS does not reliably support address-space limits for Python dylibs.
        if sys.platform == 'linux':
            resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
        result = inspect(Path(sys.argv[1]), sys.argv[2])
        if len(sys.argv) >= 4 and sys.argv[2] != 'pdf':
            from src.modules.handlers_files.normalize_photo import normalize_photo
            normalize_photo(Path(sys.argv[1]), Path(sys.argv[3]), max_side=512 if len(sys.argv) == 5 else 2560)
        print(json.dumps(result))
    except Exception:
        sys.exit(2)
