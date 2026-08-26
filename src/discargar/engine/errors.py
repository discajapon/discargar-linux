"""Errores del motor, clasificados con un mensaje accionable para el usuario.

El detalle técnico crudo (salida de yt-dlp, tracebacks) nunca llega a la
interfaz: se registra en el log y aquí solo queda una categoría estable más
un mensaje ya traducido a lenguaje humano.
"""

from __future__ import annotations

from enum import Enum


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
    ErrorCategory.INVALID_URL: "Eso no parece un enlace válido. Pega la URL completa del vídeo.",
    ErrorCategory.NO_CONNECTION: "No hay conexión a internet. Comprueba tu red e inténtalo de nuevo.",
    ErrorCategory.UNAVAILABLE: "Este contenido no está disponible: puede ser privado, haberse eliminado o tener restricción de edad.",
    ErrorCategory.FFMPEG_MISSING: "Falta ffmpeg en el sistema. Instálalo con el gestor de paquetes de tu distribución.",
    ErrorCategory.EXTRACTION_FAILED: "No se ha podido extraer el vídeo. La plataforma puede haber cambiado algo; prueba a actualizar el motor.",
    ErrorCategory.DISK_FULL: "No hay espacio suficiente en el disco.",
    ErrorCategory.PERMISSION_DENIED: "No hay permisos de escritura en la carpeta de descargas.",
    ErrorCategory.UNKNOWN: "Ha ocurrido un error inesperado. Revisa el registro para más detalle.",
}


class EngineError(Exception):
    """Error clasificado del motor, con mensaje ya listo para mostrar al usuario."""

    def __init__(self, category: ErrorCategory, detail: str = ""):
        self.category = category
        self.detail = detail
        super().__init__(_MESSAGES[category])

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
