"""Créditos y licencias de terceros para la pantalla de ajustes.

Los textos completos viven en discargar/licenses/ (descargados verbatim de
las fuentes oficiales, nunca escritos a mano) y se sirven tal cual.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, Slot

_LICENSES_DIR = Path(__file__).parent.parent / "licenses"

_ENTRIES = [
    {"name": "discargar", "spdx": "GPL-3.0-or-later", "file": "discargar-GPL-3.0-or-later.txt"},
    {"name": "PySide6 / Qt", "spdx": "LGPL-3.0", "file": "PySide6-Qt-LGPL-3.0.txt"},
    {"name": "yt-dlp", "spdx": "Unlicense", "file": "yt-dlp-UNLICENSE.txt"},
    {"name": "deno", "spdx": "MIT", "file": "deno-MIT.txt"},
]


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
