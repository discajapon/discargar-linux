"""Plantilla de progreso estructurado para yt-dlp y su parser.

yt-dlp acepta --progress-template para emitir una línea propia por cada
evento de progreso, con campos bajo info.* y progress.*. Aquí se define una
plantilla con delimitador y prefijo propios (nunca se parsea la salida
pensada para humanos) y el código que la interpreta de vuelta.
"""

from __future__ import annotations

from dataclasses import dataclass

DL_PREFIX = "DISCARGAR-DL|"
PP_PREFIX = "DISCARGAR-PP|"
_NA = "NA"


@dataclass(frozen=True)
class DownloadProgress:
    status: str
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    tmpfilename: str | None


@dataclass(frozen=True)
class PostprocessProgress:
    status: str


def progress_template_args() -> list[str]:
    download_fields = "|".join(
        [
            "%(progress.status)s",
            "%(progress.downloaded_bytes)s",
            "%(progress.total_bytes,progress.total_bytes_estimate)s",
            "%(progress.speed)s",
            "%(progress.eta)s",
            "%(progress.tmpfilename)s",
        ]
    )
    return [
        "--progress-template",
        f"download:{DL_PREFIX}{download_fields}",
        "--progress-template",
        f"postprocess:{PP_PREFIX}%(progress.status)s",
    ]


def _int_or_none(raw: str) -> int | None:
    if raw in (_NA, ""):
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _float_or_none(raw: str) -> float | None:
    if raw in (_NA, ""):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_line(line: str) -> DownloadProgress | PostprocessProgress | None:
    """Interpreta una línea de stdout de yt-dlp. None si no es progreso nuestro."""
    if line.startswith(DL_PREFIX):
        parts = line[len(DL_PREFIX):].split("|")
        if len(parts) != 6:
            return None
        status, downloaded, total, speed, eta, tmpfilename = parts
        return DownloadProgress(
            status=status,
            downloaded_bytes=_int_or_none(downloaded),
            total_bytes=_int_or_none(total),
            speed=_float_or_none(speed),
            eta=_int_or_none(eta),
            tmpfilename=None if tmpfilename == _NA else tmpfilename,
        )
    if line.startswith(PP_PREFIX):
        return PostprocessProgress(status=line[len(PP_PREFIX):])
    return None
