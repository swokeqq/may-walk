"""Хеширование файлов."""

import hashlib
from pathlib import Path


def file_sha256(file_path: Path) -> str:
    """Посчитать SHA-256 файла потоковым чтением."""
    digest = hashlib.sha256()
    with file_path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
