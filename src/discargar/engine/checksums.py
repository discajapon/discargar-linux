"""Verificación de checksums SHA-256.

yt-dlp (SHA2-256SUMS) y deno (*.sha256sum) publican sus sumas en el mismo
formato estándar de `sha256sum`: una línea "<hex>  <nombre-de-archivo>" por
asset.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def parse_sha256sums(text: str) -> dict[str, str]:
    """Convierte el contenido de un archivo de sumas en {nombre: hex}."""
    sums: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, filename = parts
        # sha256sum antepone "*" al nombre en modo binario.
        sums[filename.lstrip("*")] = digest.lower()
    return sums


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected_sha256: str) -> bool:
    return sha256_of(path) == expected_sha256.lower()
