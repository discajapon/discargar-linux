"""Herramienta de consola para validar el gestor del motor a mano.

No es una función de producto: es la vía que pide el CLAUDE.md para probar
la gestión del motor antes de construir la ventana encima.

Uso:
    python -m discargar.engine.cli install [--channel stable|nightly]
    python -m discargar.engine.cli update [--channel stable|nightly]
    python -m discargar.engine.cli download <url>
"""

from __future__ import annotations

import argparse
import signal
import sys
import threading

from discargar.engine import deno, ytdlp
from discargar.engine.downloader import DownloadCancelled, run_download
from discargar.engine.errors import EngineError
from discargar.engine.progress import DownloadProgress, PostprocessProgress


def _format_bytes(n: float | None) -> str:
    if n is None:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}TB"


def _on_progress(event: DownloadProgress | PostprocessProgress) -> None:
    if isinstance(event, DownloadProgress):
        pct = ""
        if event.downloaded_bytes is not None and event.total_bytes:
            pct = f"{100 * event.downloaded_bytes / event.total_bytes:5.1f}% "
        speed = f" a {_format_bytes(event.speed)}/s" if event.speed else ""
        line = (
            f"{event.status:12s} {pct}"
            f"{_format_bytes(event.downloaded_bytes)}/{_format_bytes(event.total_bytes)}{speed}"
        )
        print(f"\r{line}", end="", flush=True)
    elif isinstance(event, PostprocessProgress):
        print(f"\rprocesando ({event.status})...", end="", flush=True)


def cmd_install(args: argparse.Namespace) -> int:
    print(f"Instalando yt-dlp (canal {args.channel})...")
    ytdlp.ensure_installed(args.channel)
    print("Instalando deno...")
    deno.ensure_installed()
    print("Listo.")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    print(f"Comprobando actualizaciones de yt-dlp (canal {args.channel})...")
    updated = ytdlp.check_and_update(args.channel)
    print("Actualizado." if updated else "Ya estaba al día.")
    print("Comprobando actualizaciones de deno...")
    updated = deno.check_and_update()
    print("Actualizado." if updated else "Ya estaba al día.")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    cancel_event = threading.Event()

    def _handle_sigint(signum, frame) -> None:
        print("\nCancelando...")
        cancel_event.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        result = run_download(args.url, on_progress=_on_progress, cancel_event=cancel_event)
    except DownloadCancelled:
        print("\nDescarga cancelada. Sin archivos parciales huérfanos.")
        return 130
    except EngineError as exc:
        print(f"\nError: {exc.user_message}")
        if exc.detail:
            print(f"(detalle en el log: {exc.detail[:200]})")
        return 1

    print(f"\nListo. Archivo en {result.output_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="discargar-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Instala yt-dlp y deno si faltan")
    install_parser.add_argument("--channel", choices=["nightly", "stable"], default="nightly")
    install_parser.set_defaults(func=cmd_install)

    update_parser = subparsers.add_parser("update", help="Comprueba y aplica actualizaciones")
    update_parser.add_argument("--channel", choices=["nightly", "stable"], default="nightly")
    update_parser.set_defaults(func=cmd_update)

    download_parser = subparsers.add_parser("download", help="Descarga una URL")
    download_parser.add_argument("url")
    download_parser.set_defaults(func=cmd_download)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
