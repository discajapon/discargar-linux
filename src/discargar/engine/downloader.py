"""Invoca yt-dlp como proceso externo para descargar una URL.

Lee el progreso en formato estructurado (progress.py), permite cancelar
limpiamente sin dejar archivos parciales huérfanos, y traduce cualquier
fallo a un EngineError ya clasificado.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from discargar.engine import ffmpeg_bridge, progress as progress_mod
from discargar.engine.deno import binary_path as deno_binary_path
from discargar.engine.errors import EngineError, ErrorCategory, classify_stderr
from discargar.engine.ytdlp import binary_path as ytdlp_binary_path
from discargar.log import get_logger
from discargar.paths import downloads_dir

logger = get_logger(__name__)

ProgressEvent = progress_mod.DownloadProgress | progress_mod.PostprocessProgress
ProgressCallback = Callable[[ProgressEvent], None]

_MIN_FREE_BYTES = 200 * 1024 * 1024  # margen de seguridad antes de empezar


class DownloadCancelled(Exception):
    """Señala que la descarga terminó porque se activó cancel_event.

    No es un EngineError: no hay nada que mostrarle al usuario como fallo,
    el panel simplemente vuelve a su estado de reposo (requisito 6).
    """


@dataclass(frozen=True)
class DownloadResult:
    output_dir: Path


def _validate_url(url: str) -> None:
    url = url.strip()
    if not url:
        raise EngineError(ErrorCategory.INVALID_URL, "URL vacía")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise EngineError(ErrorCategory.INVALID_URL, f"URL mal formada: {url!r}")


def _check_destination(dest_dir: Path) -> None:
    if not os.access(dest_dir, os.W_OK):
        raise EngineError(ErrorCategory.PERMISSION_DENIED, f"Sin permiso de escritura en {dest_dir}")
    usage = shutil.disk_usage(dest_dir)
    if usage.free < _MIN_FREE_BYTES:
        raise EngineError(ErrorCategory.DISK_FULL, f"Solo quedan {usage.free} bytes libres en {dest_dir}")


def _build_env() -> dict:
    """PATH con el directorio de deno delante, para que yt-dlp-ejs lo encuentre."""
    env = os.environ.copy()
    deno_bin = deno_binary_path()
    if deno_bin.is_file():
        env["PATH"] = f"{deno_bin.parent}{os.pathsep}{env.get('PATH', '')}"
    return env


def _cleanup_partial(tmpfilename: str | None) -> None:
    if not tmpfilename:
        return
    base = Path(tmpfilename)
    candidates = [base] if base.suffix in (".part", ".ytdl") else [
        base.with_name(base.name + ".part"),
        base.with_name(base.name + ".ytdl"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            candidate.unlink(missing_ok=True)
            logger.info("Borrado temporal huérfano: %s", candidate)


def run_download(
    url: str,
    on_progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> DownloadResult:
    """Descarga `url` con la mejor calidad disponible, fusionando a mp4.

    Bloqueante: pensado para ejecutarse en un hilo aparte cuando lo use la
    interfaz. Lanza EngineError (clasificado) o DownloadCancelled.
    """
    _validate_url(url)

    ffmpeg_dir = ffmpeg_bridge.locate_ffmpeg_dir()
    if ffmpeg_dir is None:
        raise EngineError(ErrorCategory.FFMPEG_MISSING, "ffmpeg no disponible (ni en PATH ni, bajo Flatpak, en el host)")

    ytdlp = ytdlp_binary_path()
    if not ytdlp.is_file():
        raise EngineError(ErrorCategory.UNKNOWN, "yt-dlp no está instalado")

    dest_dir = downloads_dir()
    _check_destination(dest_dir)

    argv = [
        str(ytdlp),
        url,
        "--no-playlist",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--ffmpeg-location", str(ffmpeg_dir),
        "-P", str(dest_dir),
        "--newline",
        *progress_mod.progress_template_args(),
    ]
    logger.info("Ejecutando: %s", " ".join(argv))

    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=_build_env(),
    )

    def _watch_cancel() -> None:
        if cancel_event is None:
            return
        cancel_event.wait()
        process.terminate()

    watcher = threading.Thread(target=_watch_cancel, daemon=True)
    watcher.start()

    last_tmpfilename: str | None = None
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.rstrip("\n")
        event = progress_mod.parse_line(line)
        if event is None:
            if line:
                logger.debug("yt-dlp: %s", line)
            continue
        if isinstance(event, progress_mod.DownloadProgress) and event.tmpfilename:
            last_tmpfilename = event.tmpfilename
        if on_progress is not None:
            on_progress(event)

    stderr_output = process.stderr.read() if process.stderr else ""
    process.wait()

    if cancel_event is not None and cancel_event.is_set():
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        _cleanup_partial(last_tmpfilename)
        raise DownloadCancelled()

    if process.returncode != 0:
        logger.error("yt-dlp terminó con código %s. stderr:\n%s", process.returncode, stderr_output)
        raise EngineError(classify_stderr(stderr_output), stderr_output)

    return DownloadResult(output_dir=dest_dir)
