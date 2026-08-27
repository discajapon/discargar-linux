"""Rutas del directorio de datos, configuración, estado y descargas del
usuario, según la especificación XDG Base Directory.

Cada función crea el directorio si no existe y lo devuelve como Path.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

APP_NAME = "discargar"


def _xdg_dir(env_var: str, default: str) -> Path:
    value = os.environ.get(env_var)
    base = Path(value) if value else Path.home() / default
    return base


def data_dir() -> Path:
    """Directorio de datos: binarios de yt-dlp y deno gestionados por la app."""
    path = _xdg_dir("XDG_DATA_HOME", ".local/share") / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    """Directorio de configuración: archivo de tema editable por el usuario."""
    path = _xdg_dir("XDG_CONFIG_HOME", ".config") / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path:
    """Directorio de estado: logs con el detalle técnico de errores."""
    path = _xdg_dir("XDG_STATE_HOME", ".local/state") / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def engine_dir() -> Path:
    """Subdirectorio de datos donde viven los ejecutables del motor."""
    path = data_dir() / "engine"
    path.mkdir(parents=True, exist_ok=True)
    return path


def downloads_dir() -> Path:
    """Carpeta de descargas del usuario, leída de ~/.config/user-dirs.dirs.

    Ese archivo lo mantiene xdg-user-dirs (estándar en GNOME/Ubuntu). Si no
    existe o no define XDG_DOWNLOAD_DIR, se usa ~/Downloads como respaldo.
    """
    user_dirs_file = _xdg_dir("XDG_CONFIG_HOME", ".config") / "user-dirs.dirs"
    if user_dirs_file.is_file():
        text = user_dirs_file.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'^XDG_DOWNLOAD_DIR="(.+)"$', text, re.MULTILINE)
        if match:
            raw = match.group(1).replace("$HOME", str(Path.home()))
            path = Path(raw)
            path.mkdir(parents=True, exist_ok=True)
            return path
    path = Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundled_ffmpeg_dir() -> Path | None:
    """Directorio con un ffmpeg/ffprobe empaquetado junto a la app, o None.

    En Linux siempre es None: se usa el ffmpeg del sistema (o, bajo Flatpak,
    el del host). Existe para que `engine/ffmpeg_bridge.py` sea común con el
    repo de Windows, donde ffmpeg va incluido en el instalador y esta
    función devuelve su ruta.
    """
    return None
