"""Errores del motor, clasificados con un mensaje accionable para el usuario.

El detalle técnico crudo (salida de yt-dlp, tracebacks) nunca llega a la
interfaz: se registra en el log y aquí solo queda una categoría estable más
un mensaje ya traducido a lenguaje humano.

Los mensajes están en inglés a propósito: son texto de producto (la interfaz
es solo en inglés, por decisión del proyecto), a diferencia de las
herramientas de desarrollo como engine/cli.py.
"""

from __future__ import annotations

from enum import Enum

from discargar.log import get_logger

logger = get_logger(__name__)


class ErrorCategory(Enum):
    INVALID_URL = "invalid_url"
    NO_CONNECTION = "no_connection"
    UNAVAILABLE = "unavailable"
    FFMPEG_MISSING = "ffmpeg_missing"
    EXTRACTION_FAILED = "extraction_failed"
    DISK_FULL = "disk_full"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


_MESSAGES = {
    ErrorCategory.INVALID_URL: "That doesn't look like a valid link. Paste the full video URL.",
    ErrorCategory.NO_CONNECTION: "No internet connection. Check your network and try again.",
    ErrorCategory.UNAVAILABLE: "This content isn't available: it may be private, removed, or age-restricted.",
    ErrorCategory.FFMPEG_MISSING: "ffmpeg is missing on this system. Install it with your distribution's package manager.",
    ErrorCategory.EXTRACTION_FAILED: "Couldn't extract the video. The platform may have changed something; try updating the engine.",
    ErrorCategory.DISK_FULL: "Not enough disk space.",
    ErrorCategory.PERMISSION_DENIED: "No write permission for the downloads folder.",
    ErrorCategory.UNKNOWN: "An unexpected error occurred. Check the log for details.",
}


class EngineError(Exception):
    """Error clasificado del motor, con mensaje ya listo para mostrar al usuario."""

    def __init__(self, category: ErrorCategory, detail: str = ""):
        self.category = category
        self.detail = detail
        super().__init__(_MESSAGES[category])
        logger.warning("EngineError(%s): %s", category.value, detail)

    @property
    def user_message(self) -> str:
        return _MESSAGES[self.category]


# Reconocimiento de mejor esfuerzo sobre stderr de yt-dlp para elegir una
# categoría cuando el proceso termina con error. No es el mecanismo principal
# de lectura de progreso (ese es siempre --progress-template, ver progress.py):
# esto solo interpreta el motivo de un fallo ya ocurrido.
_STDERR_PATTERNS: list[tuple[str, ErrorCategory]] = [
    ("private video", ErrorCategory.UNAVAILABLE),
    ("video unavailable", ErrorCategory.UNAVAILABLE),
    ("this video is unavailable", ErrorCategory.UNAVAILABLE),
    ("sign in to confirm your age", ErrorCategory.UNAVAILABLE),
    ("age-restricted", ErrorCategory.UNAVAILABLE),
    ("has been removed", ErrorCategory.UNAVAILABLE),
    ("no space left on device", ErrorCategory.DISK_FULL),
    ("permission denied", ErrorCategory.PERMISSION_DENIED),
    ("temporary failure in name resolution", ErrorCategory.NO_CONNECTION),
    ("network is unreachable", ErrorCategory.NO_CONNECTION),
    ("failed to resolve", ErrorCategory.NO_CONNECTION),
    ("urlopen error", ErrorCategory.NO_CONNECTION),
]


def classify_stderr(stderr: str) -> ErrorCategory:
    lowered = stderr.lower()
    for pattern, category in _STDERR_PATTERNS:
        if pattern in lowered:
            return category
    if "error" in lowered:
        return ErrorCategory.EXTRACTION_FAILED
    return ErrorCategory.UNKNOWN
