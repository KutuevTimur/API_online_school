import shutil
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
from PIL import Image, ImageSequence, UnidentifiedImageError

from src.core.config import Config
from src.modules.handlers_files.exception import (
    InvalidImageFormat,
    ImageCompressionError,
)


class CompressionImages:

    def __init__(
        self,
        config: Config | None = None,
    ):
        self.config = config

    def _validate_webp_file(self, filename: str | None) -> None:
        """
        Проверяет, что расширение файла действительно .webp.
        :raises InvalidImageFormat: если расширение не .webp или отсутствует.
        """
        if not filename:
            raise InvalidImageFormat("Имя файла не передано.")

        suffix = Path(filename).suffix.lower()
        if suffix != ".webp":
            raise InvalidImageFormat(
                f"Недопустимый формат файла '{suffix}'. Для сжатия поддерживается только формат .webp."
            )

    async def compress_webp(
        self,
        file: Path | UploadFile,
        dest: Path | None = None,
        max_size: Tuple[int, int] = (512, 512),
        quality: int = 80,
        keep_aspect_ratio: bool = True,
        lossless: bool = False,
    ) -> Path:
        """
        Сжимает переданное WebP-изображение до разрешения 512x512 (или указанного max_size).

        :param file: Путь к файлу Path или объект UploadFile с расширением .webp.
        :param dest: Путь для сохранения результата (директория или файл). Если None, перезаписывает исходный файл Path.
        :param max_size: Максимальное разрешение (ширина, высота), по умолчанию (512, 512).
        :param quality: Качество сжатия WebP (1-100), по умолчанию 80.
        :param keep_aspect_ratio: Сохранять ли пропорции (по умолчанию True).
        :param lossless: Использовать ли сжатие без потерь.
        :return: Path к сохраненному сжатому файлу .webp.
        :raises InvalidImageFormat: Если формат файла не .webp или файл поврежден.
        :raises ImageCompressionError: При ошибке во время сжатия/сохранения.
        """
        # Валидация входных данных и имени файла
        if isinstance(file, UploadFile):
            self._validate_webp_file(file.filename)
            filename = file.filename or f"image_{uuid.uuid4().hex}.webp"
        elif isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise InvalidImageFormat(f"Файл '{file_path}' не существует.")
            self._validate_webp_file(file_path.name)
            filename = file_path.name
        else:
            raise InvalidImageFormat(f"Неподдерживаемый тип входных данных: {type(file)}")

        # Определение целевого пути
        if dest is not None:
            dest_path = Path(dest)
            if dest_path.is_dir() or not dest_path.suffix:
                target_path = (dest_path / filename).with_suffix(".webp").resolve()
            else:
                target_path = dest_path.with_suffix(".webp").resolve()
        else:
            if isinstance(file, (str, Path)):
                target_path = Path(file).resolve()
            else:
                if self.config and hasattr(self.config, "paths") and hasattr(self.config.paths, "temp"):
                    target_path = (self.config.paths.temp / f"compressed_{uuid.uuid4().hex}_{filename}").resolve()
                else:
                    target_path = Path(f"compressed_{uuid.uuid4().hex}_{filename}").resolve()

        target_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = self.config.paths.temp if (self.config and hasattr(self.config, "paths") and hasattr(self.config.paths, "temp")) else target_path.parent
        temp_file_path = (temp_dir / f"temp_compress_{uuid.uuid4().hex}.webp").resolve()
        output_temp = (temp_dir / f"out_compress_{uuid.uuid4().hex}.webp").resolve()

        try:
            # Получаем путь к исходному файлу
            if isinstance(file, UploadFile):
                content = await file.read()
                if not content:
                    raise InvalidImageFormat("Файл пуст.")
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(content)
                source_image_path = temp_file_path
            else:
                source_image_path = Path(file)

            try:
                with Image.open(source_image_path) as img:
                    if img.format != "WEBP":
                        raise InvalidImageFormat(f"Файл имеет формат {img.format}, ожидается WEBP.")

                    is_animated = getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1

                    if is_animated:
                        frames = []
                        durations = []
                        for frame in ImageSequence.Iterator(img):
                            f = frame.copy()
                            if keep_aspect_ratio:
                                f.thumbnail(max_size, Image.Resampling.LANCZOS)
                            else:
                                f = f.resize(max_size, Image.Resampling.LANCZOS)
                            frames.append(f)
                            durations.append(frame.info.get("duration", img.info.get("duration", 100)))

                        duration = durations if any(d != durations[0] for d in durations) else durations[0]

                        frames[0].save(
                            output_temp,
                            format="WEBP",
                            save_all=True,
                            append_images=frames[1:],
                            quality=quality,
                            lossless=lossless,
                            loop=img.info.get("loop", 0),
                            duration=duration,
                        )
                    else:
                        img_copy = img.copy()
                        if keep_aspect_ratio:
                            img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
                        else:
                            img_copy = img_copy.resize(max_size, Image.Resampling.LANCZOS)

                        img_copy.save(
                            output_temp,
                            format="WEBP",
                            quality=quality,
                            lossless=lossless,
                        )

                shutil.move(output_temp, target_path)

            except (UnidentifiedImageError, OSError) as e:
                raise InvalidImageFormat(f"Не удалось открыть WebP-изображение или файл поврежден: {e}") from e
            except InvalidImageFormat:
                raise
            except Exception as e:
                raise ImageCompressionError(f"Ошибка при сжатии WebP-изображения: {e}") from e

        finally:
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)
            if output_temp.exists():
                output_temp.unlink(missing_ok=True)
            if isinstance(file, UploadFile):
                await file.seek(0)

        return target_path
