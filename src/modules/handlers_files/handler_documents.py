import os
import shutil
import asyncio
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
    def __init__(self, config: Config):
        self.config = config

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

    async def save_document(
        self,
        document: UploadFile,
        original_dest: Path,
        pdf_dest: Path,
    ) -> tuple[Path, Path]:
        """
        Проверяет расширение файла, сохраняет оригинальный файл и конвертирует его в PDF.
        """
        ext = self._validate_extension(document.filename)

        original_dest.parent.mkdir(parents=True, exist_ok=True)
        pdf_dest.parent.mkdir(parents=True, exist_ok=True)

        content = await document.read()
        
        with open(original_dest, "wb") as f:
            f.write(content)

        if ext == "pdf":
            shutil.copy(original_dest, pdf_dest)
        elif ext in {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"}:
            await self._convert_image_to_pdf(original_dest, pdf_dest)
        elif ext in {"doc", "docx", "odt", "txt"}:
            await self._convert_doc_to_pdf_libreoffice(original_dest, pdf_dest)
        else:
            # На случай, если расширение добавили в список, но конвертер под него не написали - 
            # просто скопируем как есть (считаем, что это будет поддерживаться позже)
            shutil.copy(original_dest, pdf_dest)

        await document.seek(0)
        return original_dest, pdf_dest
