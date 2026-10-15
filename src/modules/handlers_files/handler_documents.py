import os
import shutil
import asyncio
import json
import sys
from uuid import uuid4
from src.modules.storage.service import LocalStorage, LegacyStorage, StorageLimitExceeded, file_io
from typing import Set
from pathlib import Path
from fastapi import UploadFile
from PIL import Image

from src.core.config import Config
from src.modules.handlers_files.exception import (
    InvalidDocumentFormat,
    DocumentConversionError,
)

class HandlerDocuments:
    processing_timeout_seconds = 30
    def __init__(self, config: Config):
        self.config = config
        self.storage = LocalStorage(config.paths)
        self.saved_objects = {}
        self.quota_pending = {}
        self.transient_objects = []
        self.upload_committed = False
        if not hasattr(config, '_file_processing_semaphore'):
            config._file_processing_semaphore = asyncio.Semaphore(1)

    def _get_allowed_extensions(self) -> Set[str]:
        return {
            ext.lstrip(".").lower()
            for ext in self.config.allowed_extensions.for_convert_pdf
        }

    def _validate_extension(self, filename: str | None) -> str:
        if not filename:
            raise InvalidDocumentFormat("Нет имени файла.")

        suffix = Path(filename).suffix
        if not suffix:
            raise InvalidDocumentFormat(f"К '{filename}' нет расширения.")

        ext = suffix.lstrip(".").lower()
        allowed = self._get_allowed_extensions()
        
        if ext not in allowed:
            raise InvalidDocumentFormat(
                f"Некорректный формат '{ext}'. Доступные форматы: {', '.join(sorted(allowed))}."
            )
        return ext

    async def _convert_image_to_pdf(self, source: Path, dest: Path):
        """Конвертирует изображение в PDF с помощью Pillow."""
        try:
            with Image.open(source) as img:
                # Если у картинки есть прозрачность или она в RGBA, конвертируем в RGB
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                    
                img.save(dest, "PDF", resolution=100.0)
        except Exception as e:
            raise DocumentConversionError(f"Ошибка при конвертации изображения в PDF: {e}") from e

    async def _convert_doc_to_pdf_libreoffice(self, source: Path, dest: Path):
        """Конвертирует файлы (doc, docx, odt) в PDF с помощью LibreOffice в headless режиме."""
        # LibreOffice создает PDF-файл в указанной директории с тем же именем.
        output_dir = dest.parent
        
        # Команда кроссплатформенная (soffice работает и на linux, и на windows, если добавлен в PATH).
        # На Windows может потребоваться указать полный путь, но мы надеемся, что он в PATH.
        command = [
            "soffice",
            "--headless",
            "--convert-to", 
            "pdf",
            "--outdir",
            str(output_dir),
            str(source)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DocumentConversionError(f"LibreOffice завершился с ошибкой: {stderr.decode()}")
                
            # Проверим, что файл реально создался
            libreoffice_output_file = output_dir / f"{source.stem}.pdf"
            if libreoffice_output_file != dest and libreoffice_output_file.exists():
                shutil.move(libreoffice_output_file, dest)
                
            if not dest.exists():
                raise DocumentConversionError("PDF файл не был создан LibreOffice.")
                
        except FileNotFoundError as e:
            raise DocumentConversionError("Для конвертации документов (docx/doc) требуется установленный LibreOffice (soffice) в системе.") from e
        except Exception as e:
            raise DocumentConversionError(f"Ошибка конвертации документа: {e}") from e

    async def inspect_document(self, source: Path, extension: str, output: Path | None = None) -> str:
        async with self.config._file_processing_semaphore:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'src.modules.handlers_files.inspect_document',
                str(source), extension, *([str(output)] if output else []), stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=self.processing_timeout_seconds)
            except BaseException as exc:
                if process.returncode is None:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                await process.communicate()
                if isinstance(exc, TimeoutError):
                    raise InvalidDocumentFormat("File processing exceeded 30 seconds") from None
                raise
            if process.returncode != 0:
                raise InvalidDocumentFormat("Invalid, damaged, encrypted or unsupported file")
            return json.loads(stdout)['mime']

    async def save_document(
        self, document: UploadFile, original_dest: Path, pdf_dest: Path,
    ) -> tuple[Path, Path]:
        """Bounded immutable upload. Never remove a previously stored object.

        D06 parameters accepted; photo originals remain byte-for-byte intact
        until the separate visual acceptance and post-commit deletion switch.
        """
        extension = self._validate_extension(document.filename)
        if extension not in {'pdf', 'jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'}:
            raise InvalidDocumentFormat("MVP supports PDF and static JPEG/PNG/WebP/HEIC only")
        legacy = LegacyStorage(self.config.paths)
        original_key, pdf_key = legacy.key(original_dest), legacy.key(pdf_dest)
        if extension != 'pdf':
            pdf_dest = pdf_dest.with_suffix('.webp')
            pdf_key = legacy.key(pdf_dest)
        temp_key = 'temp/' + uuid4().hex
        self.transient_objects.append(self.config.paths.media / temp_key)
        created = []
        try:
            result = await self.storage.put(document, temp_key, max_bytes=20 * 1024 * 1024)
            if result.size == 0:
                raise InvalidDocumentFormat("Empty file")
            source = self.config.paths.media / temp_key
            converted_key = 'temp/' + uuid4().hex + '.webp' if extension != 'pdf' else None
            converted = self.config.paths.media / converted_key if converted_key else None
            if converted:
                self.transient_objects.append(converted)
            mime = await self.inspect_document(source, extension, converted)
            async with self.storage.open(temp_key) as stream:
                class Source:
                    async def read(self, size: int = -1) -> bytes:
                        return await file_io(stream.read, size)
                original_info = await self.storage.put(Source(), original_key, max_bytes=20 * 1024 * 1024)
            created.append(original_key)
            self.saved_objects[original_dest] = (original_info, mime)
            if extension == 'pdf':
                # One immutable PDF object, both legacy columns refer to it.
                return original_dest, original_dest
            # Keep the original until DB commit and explicit visual acceptance.
            try:
                async with self.storage.open(converted_key) as stream:
                    class ConvertedSource:
                        async def read(self, size: int = -1) -> bytes:
                            return await file_io(stream.read, size)
                    pdf_info = await self.storage.put(ConvertedSource(), pdf_key, max_bytes=100 * 1024 * 1024)
                created.append(pdf_key)
                self.saved_objects[pdf_dest] = (pdf_info, "image/webp")
            finally:
                await self.storage.delete(converted_key)
            return original_dest, pdf_dest
        except StorageLimitExceeded as exc:
            for key in created:
                await self.storage.delete(key)
            from src.modules.handlers_files.exception import FileTooLarge
            raise FileTooLarge("File exceeds 20 MiB") from exc
        except BaseException:
            for key in created:
                await self.storage.delete(key)
            raise
        finally:
            await self.storage.delete(temp_key)
            if 'converted_key' in locals() and converted_key:
                await self.storage.delete(converted_key)
            await document.seek(0)
