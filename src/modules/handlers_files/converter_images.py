import uuid
from pathlib import Path
from typing import Set

from fastapi import UploadFile
from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
import pillow_heif

from src.core.config import Config
from src.modules.handlers_files.exception import (
    InvalidImageFormat,
    ImageConversionError,
)

# Регистрируем поддержку HEIF/HEIC для Pillow
pillow_heif.register_heif_opener()


class HandlerImages:

    def __init__(
        self,
        config: Config,
    ):
        self.config = config

    def _get_allowed_extensions(self) -> Set[str]:
        """Возвращает нормализованное множество разрешенных расширений без точек в нижнем регистре."""
        return {
            ext.lstrip(".").lower()
            for ext in self.config.allowed_extensions.for_convert_image
        }

    def _validate_extension(self, filename: str | None) -> str:
        """
        Проверяет расширение файла на допустимость.
        :raises InvalidImageFormat: если расширение недопустимо или отсутствует.
        :return: расширение файла в нижнем регистре без точки.
        """
        if not filename:
            raise InvalidImageFormat("Имя файла не передано.")

        suffix = Path(filename).suffix
        if not suffix:
            raise InvalidImageFormat(f"Файл '{filename}' не имеет расширения.")

        ext = suffix.lstrip(".").lower()
        allowed = self._get_allowed_extensions()
        if ext not in allowed:
            raise InvalidImageFormat(
                f"Недопустимый формат файла '{suffix}'. Разрешенные форматы: {', '.join(sorted(allowed))}."
            )
        return ext

    async def convert_to_webp(
        self,
        photo: UploadFile,
        dest: Path,
        quality: int = 80,
        lossless: bool = False,
    ) -> Path:
        """
        Конвертирует переданное изображение в формат .webp и сохраняет по указанному пути dest.

        :param photo: Загружаемый файл UploadFile.
        :param dest: Директория или полный путь к файлу назначения.
        :param quality: Качество сжатия WebP (1-100).
        :param lossless: Использовать ли сжатие без потерь.
        :return: Итоговый путь Path к сохраненному .webp файлу.
        :raises InvalidImageFormat: Если расширение или формат файла недопустимы / повреждены.
        :raises ImageConversionError: При ошибке в процессе конвертации / сохранения.
        """
        self._validate_extension(photo.filename)

        # Определяем итоговый путь сохранения файла
        if dest.is_dir() or not dest.suffix:
            filename_stem = Path(photo.filename).stem if photo.filename else uuid.uuid4().hex
            target_path = (dest / f"{filename_stem}.webp").resolve()
        else:
            target_path = dest.with_suffix(".webp").resolve()

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Временный файл в директории temp из конфига
        temp_filename = f"temp_{uuid.uuid4().hex}_{photo.filename or 'upload'}"
        temp_file_path = (self.config.paths.temp / temp_filename).resolve()

        try:
            # Читаем содержимое загруженного файла и сохраняем во временный файл
            content = await photo.read()
            if not content:
                raise InvalidImageFormat("Файл пуст.")

            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(content)

            # Открываем изображение через Pillow
            try:
                with Image.open(temp_file_path) as image:
                    # Обработка анимированных изображений (например, GIF / animated WebP)
                    is_animated = getattr(image, "is_animated", False) and getattr(image, "n_frames", 1) > 1

                    if is_animated:
                        frames = []
                        durations = []
                        for frame in ImageSequence.Iterator(image):
                            f = ImageOps.exif_transpose(frame) or frame
                            if f.mode in ("RGBA", "LA"):
                                f_conv = f.copy()
                            elif f.mode == "P":
                                if "transparency" in f.info:
                                    f_conv = f.convert("RGBA")
                                else:
                                    f_conv = f.convert("RGB")
                            elif f.mode in ("RGB", "L"):
                                f_conv = f.copy()
                            else:
                                f_conv = f.convert("RGB")

                            frames.append(f_conv)
                            durations.append(frame.info.get("duration", image.info.get("duration", 100)))

                        duration = durations if any(d != durations[0] for d in durations) else durations[0]

                        frames[0].save(
                            target_path,
                            format="WEBP",
                            save_all=True,
                            append_images=frames[1:],
                            quality=quality,
                            lossless=lossless,
                            loop=image.info.get("loop", 0),
                            duration=duration,
                        )
                    else:
                        # Корректируем ориентацию по EXIF (актуально для фото со смартфонов/камер)
                        image = ImageOps.exif_transpose(image) or image

                        # Обработка цветовых режимов для статического изображения
                        if image.mode in ("RGBA", "LA"):
                            converted_img = image
                        elif image.mode == "P":
                            if "transparency" in image.info:
                                converted_img = image.convert("RGBA")
                            else:
                                converted_img = image.convert("RGB")
                        elif image.mode in ("RGB", "L"):
                            converted_img = image
                        else:
                            converted_img = image.convert("RGB")

                        converted_img.save(
                            target_path,
                            format="WEBP",
                            quality=quality,
                            lossless=lossless,
                        )
            except (UnidentifiedImageError, OSError) as e:
                raise InvalidImageFormat(f"Не удалось распознать изображение или файл поврежден: {e}") from e
            except Exception as e:
                raise ImageConversionError(f"Ошибка при конвертации изображения в .webp: {e}") from e

        finally:
            # Удаляем временный файл
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)
            # Возвращаем указатель файла в начало
            await photo.seek(0)

        return target_path
