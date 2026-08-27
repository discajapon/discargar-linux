"""Localiza ffmpeg y ffprobe, incluso corriendo dentro del sandbox de
Flatpak.

Fuera de Flatpak, yt-dlp encuentra ffmpeg solo con que esté en el PATH del
sistema. Dentro de Flatpak el proceso vive en su propio filesystem: no ve
`/usr/bin/ffmpeg` del host aunque exista, así que hay que pasar por
`flatpak-spawn --host` (ver documentación de Flatpak sobre el sandbox). La
solución: si estamos en Flatpak, generar dos envoltorios diminutos
(`ffmpeg`, `ffprobe`) que reenvían la llamada al host, guardarlos en el
directorio de datos, y decirle a yt-dlp que use esa carpeta con
--ffmpeg-location.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

from discargar.log import get_logger
from discargar.paths import data_dir

logger = get_logger(__name__)

_BRIDGE_DIRNAME = "ffmpeg-host-bridge"
_WRAPPER_TEMPLATE = '#!/bin/sh\nexec flatpak-spawn --host {binary} "$@"\n'


def running_under_flatpak() -> bool:
    return "FLATPAK_ID" in os.environ


def _host_binary_exists(binary: str) -> bool:
    try:
        result = subprocess.run(
            ["flatpak-spawn", "--host", "which", binary],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _ensure_wrapper(path: Path, binary: str) -> None:
    if not path.is_file():
        path.write_text(_WRAPPER_TEMPLATE.format(binary=binary), encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def locate_ffmpeg_dir() -> Path | None:
    """Directorio a pasar como --ffmpeg-location a yt-dlp, o None si no hay
    ffmpeg disponible (ni en el PATH normal, ni en el host bajo Flatpak)."""
    if not running_under_flatpak():
        ffmpeg_path = shutil.which("ffmpeg")
        return Path(ffmpeg_path).parent if ffmpeg_path else None

    if not (_host_binary_exists("ffmpeg") and _host_binary_exists("ffprobe")):
        logger.warning("ffmpeg/ffprobe no encontrados en el host vía flatpak-spawn")
        return None

    bridge_dir = data_dir() / _BRIDGE_DIRNAME
    bridge_dir.mkdir(parents=True, exist_ok=True)
    _ensure_wrapper(bridge_dir / "ffmpeg", "ffmpeg")
    _ensure_wrapper(bridge_dir / "ffprobe", "ffprobe")
    return bridge_dir
