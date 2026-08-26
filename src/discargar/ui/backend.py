"""Backend expuesto a QML: estado de la descarga y acciones del usuario.

Traduce las señales de los workers (el motor ejecutándose en otro hilo) a
propiedades Qt que la interfaz puede enlazar directamente, y los eventos de
progreso tipados de engine/progress.py a los textos de estado del
requisito 5 (preparando, actualizando el motor, descargando con porcentaje y
velocidad, procesando, listo, o el error).
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QClipboard, QDesktopServices, QGuiApplication

from discargar.engine.downloader import DownloadResult
from discargar.engine.progress import DownloadProgress, PostprocessProgress
from discargar.log import get_logger
from discargar.ui.theme import Theme
from discargar.ui.workers import DownloadWorker, EngineSetupWorker

logger = get_logger(__name__)


def _format_speed(bytes_per_sec: float | None) -> str:
    if not bytes_per_sec:
        return ""
    value = bytes_per_sec
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == "B/s" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB/s"


class AppBackend(QObject):
    statusTextChanged = Signal()
    isDownloadingChanged = Signal()
    isEngineReadyChanged = Signal()
    progressFractionChanged = Signal()
    downloadFinished = Signal()  # éxito, error o cancelación: el panel vuelve a reposo

    def __init__(self, theme: Theme, parent: QObject | None = None):
        super().__init__(parent)
        self._theme = theme
        self._status_text = ""
        self._is_downloading = False
        self._is_engine_ready = False
        self._progress_fraction = -1.0  # -1 = indeterminado
        self._download_worker: DownloadWorker | None = None
        self._setup_worker: EngineSetupWorker | None = None

        self._start_engine_setup()

    # --- arranque: instala/actualiza el motor sin bloquear la ventana ---

    def _start_engine_setup(self) -> None:
        self._set_status("Preparing…")
        worker = EngineSetupWorker(self._theme.engineChannel, self)
        worker.statusChanged.connect(self._set_status)
        worker.finished_ok.connect(self._on_engine_ready)
        worker.failed.connect(self._on_engine_setup_failed)
        self._setup_worker = worker
        worker.start()

    def _on_engine_ready(self) -> None:
        self._is_engine_ready = True
        self.isEngineReadyChanged.emit()
        self._set_status("")

    def _on_engine_setup_failed(self, detail: str) -> None:
        logger.error("No se pudo preparar el motor: %s", detail)
        self._set_status("Couldn't prepare the download engine. Check your connection and restart the app.")

    # --- propiedades expuestas a QML ---

    def _get_status_text(self) -> str:
        return self._status_text

    statusText = Property(str, fget=_get_status_text, notify=statusTextChanged)  # type: ignore[arg-type]

    def _get_is_downloading(self) -> bool:
        return self._is_downloading

    isDownloading = Property(bool, fget=_get_is_downloading, notify=isDownloadingChanged)  # type: ignore[arg-type]

    def _get_is_engine_ready(self) -> bool:
        return self._is_engine_ready

    isEngineReady = Property(bool, fget=_get_is_engine_ready, notify=isEngineReadyChanged)  # type: ignore[arg-type]

    def _get_progress_fraction(self) -> float:
        return self._progress_fraction

    progressFraction = Property(float, fget=_get_progress_fraction, notify=progressFractionChanged)  # type: ignore[arg-type]

    # --- acciones que llama la interfaz ---

    @Slot(result=str)
    def pasteFromClipboard(self) -> str:
        return QGuiApplication.clipboard().text(QClipboard.Mode.Clipboard).strip()

    @Slot(str)
    def startDownload(self, url: str) -> None:
        if self._is_downloading or not self._is_engine_ready:
            return
        self._is_downloading = True
        self.isDownloadingChanged.emit()
        self._set_progress(-1.0)
        self._set_status("Preparing…")

        worker = DownloadWorker(url, self)
        worker.progressed.connect(self._on_progress)
        worker.succeeded.connect(self._on_succeeded)
        worker.cancelled.connect(self._on_cancelled)
        worker.failed.connect(self._on_failed)
        self._download_worker = worker
        worker.start()

    @Slot()
    def cancelDownload(self) -> None:
        if self._download_worker is not None:
            self._download_worker.cancel_event.set()

    # --- eventos del worker de descarga ---

    def _on_progress(self, event: DownloadProgress | PostprocessProgress) -> None:
        if isinstance(event, DownloadProgress):
            speed = _format_speed(event.speed)
            if event.total_bytes:
                fraction = (event.downloaded_bytes or 0) / event.total_bytes
                self._set_progress(fraction)
                pct = int(fraction * 100)
                self._set_status(f"Downloading… {pct}%" + (f" · {speed}" if speed else ""))
            else:
                self._set_progress(-1.0)
                self._set_status("Downloading…" + (f" · {speed}" if speed else ""))
        elif isinstance(event, PostprocessProgress):
            self._set_progress(-1.0)
            self._set_status("Processing…")

    def _on_succeeded(self, result: DownloadResult) -> None:
        self._finish_download("Done")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_dir)))

    def _on_cancelled(self) -> None:
        self._finish_download("")

    def _on_failed(self, message: str, _category: str) -> None:
        self._finish_download(message)

    def _finish_download(self, status: str) -> None:
        self._is_downloading = False
        self.isDownloadingChanged.emit()
        self._set_progress(-1.0)
        self._set_status(status)
        self._download_worker = None
        self.downloadFinished.emit()

    # --- helpers internos ---

    def _set_status(self, text: str) -> None:
        if text != self._status_text:
            self._status_text = text
            self.statusTextChanged.emit()

    def _set_progress(self, fraction: float) -> None:
        if fraction != self._progress_fraction:
            self._progress_fraction = fraction
            self.progressFractionChanged.emit()
