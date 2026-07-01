from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


class StorageService:
    """
    Handles physical file storage.

    Responsibilities
    ----------------
    - Create upload directories
    - Save uploaded files
    - Compute SHA-256
    - Delete files
    """

    def __init__(self) -> None:
        self.root = Path(settings.UPLOAD_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        user_id: int,
        file: UploadFile,
    ) -> tuple[str, str, str]:
        """
        Returns

        (
            stored_filename,
            storage_path,
            sha256,
        )
        """

        user_dir = self.root / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(file.filename).suffix

        stored_filename = f"{uuid.uuid4().hex}{extension}"

        storage_path = user_dir / stored_filename

        sha256 = hashlib.sha256()

        with storage_path.open("wb") as buffer:

            while chunk := file.file.read(1024 * 1024):
                sha256.update(chunk)
                buffer.write(chunk)

        file.file.seek(0)

        return (
            stored_filename,
            str(storage_path),
            sha256.hexdigest(),
        )

    def delete(
        self,
        storage_path: str,
    ) -> None:

        path = Path(storage_path)

        if path.exists():
            path.unlink()

    def exists(
        self,
        storage_path: str,
    ) -> bool:

        return Path(storage_path).exists()