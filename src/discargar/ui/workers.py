"""Hilos que ejecutan el motor (engine/) sin bloquear la ventana.

Las funciones de engine/ son síncronas a propósito (pensado en la fase de
consola para poder probarlas paso a paso); aquí solo se envuelven en un
QThread cada una y se traduce su resultado a señales Qt.
"""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, QThread, Signal

from discargar.engine import deno, ytdlp
from discargar.engine.downloader import DownloadCancelled, DownloadResult, run_download
from discargar.engine.errors import EngineError
from discargar.engine.progress import DownloadProgress, PostprocessProgress
from discargar.log import get_logger

logger = get_logger(__name__)


class EngineSetupWorker(QThread):
    """Instala/actualiza yt-dlp y deno en segundo plano (arranque y refresco)."""

    statusChanged = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, channel: str, parent: QObject | None = None):
        super().__init__(parent)
        self._channel = channel

    def run(self) -> None:
        try:
            self.statusChanged.emit("Preparing…")
            ytdlp.check_and_update(self._channel)
            deno.check_and_update()
        except Exception as exc:  # noqa: BLE001 — cualquier fallo aquí no debe tumbar la app
            logger.exception("Fallo preparando el motor")
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit()


class DownloadWorker(QThread):
    """Ejecuta una descarga completa en un hilo aparte."""

    progressed = Signal(object)  # DownloadProgress | PostprocessProgress
    succeeded = Signal(object)  # DownloadResult
    cancelled = Signal()
    failed = Signal(str, str)  # user_message, category

    def __init__(self, url: str, parent: QObject | None = None):
        super().__init__(parent)
        self._url = url
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            result: DownloadResult = run_download(
                self._url,
                on_progress=self._on_progress,
                cancel_event=self.cancel_event,
            )
        except DownloadCancelled:
            self.cancelled.emit()
            return
        except EngineError as exc:
            self.failed.emit(exc.user_message, exc.category.value)
            return
        self.succeeded.emit(result)

    def _on_progress(self, event: DownloadProgress | PostprocessProgress) -> None:
        self.progressed.emit(event)
