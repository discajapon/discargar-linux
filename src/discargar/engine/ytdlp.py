"""Instalación y actualización de la copia privada de yt-dlp.

Dos canales, en repositorios de GitHub distintos: "nightly" (por defecto,
llega antes a los arreglos ante roturas de YouTube) y "stable".
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from discargar.engine import checksums, github_releases
from discargar.log import get_logger
from discargar.paths import engine_dir

logger = get_logger(__name__)

_REPOS = {
    "nightly": ("yt-dlp", "yt-dlp-nightly-builds"),
    "stable": ("yt-dlp", "yt-dlp"),
}


def _asset_name() -> str:
    machine = platform.machine()
    if machine == "x86_64":
        return "yt-dlp_linux"
    if machine in ("aarch64", "arm64"):
        return "yt-dlp_linux_aarch64"
    raise RuntimeError(f"Arquitectura no soportada por yt-dlp: {machine}")


def binary_path() -> Path:
    return engine_dir() / "yt-dlp"


def _state_path() -> Path:
    return engine_dir() / "yt-dlp.version.json"


def _read_state() -> dict:
    path = _state_path()
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _write_state(channel: str, tag: str) -> None:
    _state_path().write_text(json.dumps({"channel": channel, "tag": tag}), encoding="utf-8")


def _install_from_release(channel: str) -> str:
    """Descarga, verifica e instala la última release del canal. Devuelve el tag."""
    owner, repo = _REPOS[channel]
    release = github_releases.latest_release(owner, repo)
    asset_name = _asset_name()
    asset = release.asset(asset_name)
    if asset is None:
        raise RuntimeError(f"La release {release.tag} de {repo} no tiene el asset {asset_name}")
    sums_asset = release.asset("SHA2-256SUMS")
    if sums_asset is None:
        raise RuntimeError(f"La release {release.tag} de {repo} no publica SHA2-256SUMS")

    dest = binary_path()
    tmp = dest.with_suffix(".tmp")
    github_releases.download_file(asset.download_url, tmp)

    sums_tmp = engine_dir() / "SHA2-256SUMS.tmp"
    github_releases.download_file(sums_asset.download_url, sums_tmp)
    sums = checksums.parse_sha256sums(sums_tmp.read_text(encoding="utf-8"))
    sums_tmp.unlink(missing_ok=True)

    expected = sums.get(asset_name)
    if expected is None or not checksums.verify(tmp, expected):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Verificación de checksum fallida para {asset_name}")

    tmp.replace(dest)
    dest.chmod(dest.stat().st_mode | 0o111)
    _write_state(channel, release.tag)
    logger.info("yt-dlp instalado: canal=%s version=%s", channel, release.tag)
    return release.tag


def ensure_installed(channel: str = "nightly") -> Path:
    """Instala yt-dlp si no está presente todavía. No comprueba actualizaciones."""
    if not binary_path().is_file():
        _install_from_release(channel)
    return binary_path()


def check_and_update(channel: str = "nightly") -> bool:
    """Comprueba si hay una versión más nueva y actualiza si hace falta.

    Si yt-dlp no está instalado, lo instala. Si hay versión nueva, intenta
    primero el auto-actualizador nativo (--update-to); si falla, cae al
    respaldo de descargar e instalar directamente desde la release.
    Devuelve True si se instaló o actualizó algo.
    """
    if not binary_path().is_file():
        _install_from_release(channel)
        return True

    state = _read_state()
    if state.get("channel") != channel:
        _install_from_release(channel)
        return True

    owner, repo = _REPOS[channel]
    latest = github_releases.latest_release(owner, repo)
    if latest.tag == state.get("tag"):
        return False

    try:
        result = subprocess.run(
            [str(binary_path()), "--update-to", channel],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            _write_state(channel, latest.tag)
            logger.info("yt-dlp autoactualizado a %s", latest.tag)
            return True
        logger.warning("Autoactualización de yt-dlp devolvió código %s: %s", result.returncode, result.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("Autoactualización de yt-dlp lanzó una excepción: %s", exc)

    logger.info("Recurriendo a descarga directa para actualizar yt-dlp")
    _install_from_release(channel)
    return True
