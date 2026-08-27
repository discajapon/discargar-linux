"""Localiza ffmpeg y ffprobe: empaquetado junto a la app, en el PATH del
sistema, o en el host cuando se corre dentro del sandbox de Flatpak.

Orden de búsqueda:

1. `paths.bundled_ffmpeg_dir()` — un ffmpeg incluido con la app. En Linux
   siempre es None; en el repo de Windows devuelve la carpeta del ffmpeg
   que trae el instalador.
2. Fuera de Flatpak: `ffmpeg` en el PATH del sistema.
3. Dentro de Flatpak el proceso vive en su propio filesystem y no ve
   `/usr/bin/ffmpeg` del host aunque exista, así que hay que pasar por
   `flatpak-spawn --host` (ver documentación de Flatpak sobre el sandbox):
   se generan dos envoltorios diminutos (`ffmpeg`, `ffprobe`) que reenvían
   la llamada al host y se le dice a yt-dlp que use esa carpeta con
   --ffmpeg-location.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

from discargar.log import get_logger
from discargar.paths import bundled_ffmpeg_dir, data_dir

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
    ffmpeg disponible por ninguna vía (empaquetado, PATH, o host bajo
    Flatpak)."""
    bundled = bundled_ffmpeg_dir()
    if bundled is not None:
        return bundled

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
