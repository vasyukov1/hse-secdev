import uuid
from pathlib import Path

import magic
from fastapi import UploadFile, status
from sqlalchemy.orm import Session

from . import models
from .errors import ProblemDetailException


class FileSecurity:
    MAX_FILE_SIZE = 5_000_000
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "application/pdf"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}

    @staticmethod
    def sniff_file_type(data: bytes) -> str:
        try:
            mime = magic.from_buffer(data, mime=True)
            return mime
        except Exception:
            raise ValueError("Could not determine file type")

    @staticmethod
    def validate_file_extension(filename: str, mime_type: str):
        extension = Path(filename).suffix.lower()
        expected_extensions = {
            "image/jpeg": {".jpg", ".jpeg"},
            "image/png": {".png"},
            "image/gif": {".gif"},
            "application/pdf": {".pdf"},
        }

        if (
            mime_type in expected_extensions
            and extension not in expected_extensions[mime_type]
        ):
            raise ValueError(
                f"File extension {extension} does not match MIME type {mime_type}"
            )

    @staticmethod
    def secure_save_file(
        file: UploadFile, storage_path: Path, media_id: uuid.UUID, db: Session
    ) -> str:
        try:
            contents = file.file.read()

            if len(contents) > FileSecurity.MAX_FILE_SIZE:
                raise ProblemDetailException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    title="File Too Large",
                    detail=f"File size exceeds {FileSecurity.MAX_FILE_SIZE} bytes limit",
                )

            mime_type = FileSecurity.sniff_file_type(contents)
            if mime_type not in FileSecurity.ALLOWED_MIME_TYPES:
                raise ProblemDetailException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    title="Unsupported File Type",
                    detail=f"File type {mime_type} is not supported",
                )

            FileSecurity.validate_file_extension(file.filename or "", mime_type)

            storage_path = storage_path.resolve()
            storage_path.mkdir(parents=True, exist_ok=True)

            file_extension = Path(file.filename or "").suffix.lower()
            if (
                not file_extension
                or file_extension not in FileSecurity.ALLOWED_EXTENSIONS
            ):
                extension_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "application/pdf": ".pdf",
                }
                file_extension = extension_map.get(mime_type, ".bin")

            filename = f"{uuid.uuid4()}{file_extension}"
            file_path = (storage_path / filename).resolve()

            if not str(file_path).startswith(str(storage_path)):
                raise ProblemDetailException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Invalid File Path",
                    detail="Path traversal attempt detected",
                )

            for parent in file_path.parents:
                if parent.is_symlink():
                    raise ProblemDetailException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        title="Invalid File Path",
                        detail="Symlinks in path are not allowed",
                    )

            file_path.write_bytes(contents)

            media = db.query(models.Media).filter(models.Media.id == media_id).first()
            if media:
                media.attachment_filename = filename
                db.commit()

            return filename

        except ProblemDetailException:
            raise
        except Exception as e:
            raise ProblemDetailException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="File Processing Error",
                detail=str(e),
            )
