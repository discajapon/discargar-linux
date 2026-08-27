"""Créditos y licencias de terceros para la pantalla de ajustes.

Los textos completos viven en discargar/licenses/ (descargados verbatim de
las fuentes oficiales, nunca escritos a mano) y se sirven tal cual.

La lista de entradas se lee de discargar/licenses/manifest.toml. Ese archivo
NO se sincroniza entre plataformas: cada repo declara sus propios terceros
(Windows añade ffmpeg, que va empaquetado). Si el manifiesto falta, se usa
una lista mínima por defecto para no dejar la pantalla vacía.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from PySide6.QtCore import Property, QObject, Slot

from discargar.log import get_logger

logger = get_logger(__name__)

_LICENSES_DIR = Path(__file__).parent.parent / "licenses"
_MANIFEST = _LICENSES_DIR / "manifest.toml"

_DEFAULT_ENTRIES = [
    {"name": "discargar", "spdx": "GPL-3.0-or-later", "file": "discargar-GPL-3.0-or-later.txt"},
    {"name": "PySide6 / Qt", "spdx": "LGPL-3.0", "file": "PySide6-Qt-LGPL-3.0.txt"},
    {"name": "yt-dlp", "spdx": "Unlicense", "file": "yt-dlp-UNLICENSE.txt"},
    {"name": "deno", "spdx": "MIT", "file": "deno-MIT.txt"},
]


def _load_entries() -> list[dict]:
    if not _MANIFEST.is_file():
        logger.info("Sin licenses/manifest.toml; se usa la lista de licencias por defecto")
        return _DEFAULT_ENTRIES
    try:
        data = tomllib.loads(_MANIFEST.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        # Solo se aceptan entradas bien formadas y con su archivo presente.
        clean = [
            {"name": e["name"], "spdx": e["spdx"], "file": e["file"]}
            for e in entries
            if {"name", "spdx", "file"} <= e.keys() and (_LICENSES_DIR / e["file"]).is_file()
        ]
        return clean or _DEFAULT_ENTRIES
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        logger.warning("licenses/manifest.toml inválido (%s); se usa la lista por defecto", exc)
        return _DEFAULT_ENTRIES


_ENTRIES = _load_entries()


class Licenses(QObject):
    def _get_entries(self) -> list[dict]:
        return _ENTRIES

    entries = Property("QVariantList", fget=_get_entries, constant=True)  # type: ignore[arg-type]

    @Slot(str, result=str)
    def text(self, filename: str) -> str:
        path = _LICENSES_DIR / filename
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")
