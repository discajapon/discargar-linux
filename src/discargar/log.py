"""Logging a archivo en el directorio de estado del usuario.

El detalle técnico (trazas, salida cruda de yt-dlp, etc.) va siempre aquí,
nunca a la interfaz: la UI solo muestra mensajes ya clasificados.
"""

from __future__ import annotations

import logging

from discargar.paths import state_dir

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        log_file = state_dir() / "discargar.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        _configured = True
    return logging.getLogger(name)
