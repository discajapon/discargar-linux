"""Instalación y actualización de la copia privada del runtime deno.

yt-dlp la necesita como runtime de JavaScript externo desde la 2025.11.12.
No hay canal configurable aquí (solo la app pide una versión reciente): se
reinstala por descarga+verificación cada vez que hay una release más nueva.
"""

from __future__ import annotations

import json
import platform
import zipfile
from pathlib import Path

from discargar.engine import checksums, github_releases
from discargar.log import get_logger
from discargar.paths import engine_dir

logger = get_logger(__name__)

_OWNER, _REPO = "denoland", "deno"


def _asset_name() -> str:
    machine = platform.machine()
    if machine == "x86_64":
        return "deno-x86_64-unknown-linux-gnu.zip"
    if machine in ("aarch64", "arm64"):
        return "deno-aarch64-unknown-linux-gnu.zip"
    raise RuntimeError(f"Arquitectura no soportada por deno: {machine}")


def binary_path() -> Path:
    return engine_dir() / "deno"


def _state_path() -> Path:
    return engine_dir() / "deno.version.json"


def _read_state() -> dict:
    path = _state_path()
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _write_state(tag: str) -> None:
    _state_path().write_text(json.dumps({"tag": tag}), encoding="utf-8")


def _install_from_release() -> str:
    """Descarga, verifica y descomprime la última release. Devuelve el tag."""
    release = github_releases.latest_release(_OWNER, _REPO)
    asset_name = _asset_name()
    asset = release.asset(asset_name)
    if asset is None:
        raise RuntimeError(f"La release {release.tag} de deno no tiene el asset {asset_name}")
    sums_asset = release.asset(f"{asset_name}.sha256sum")
    if sums_asset is None:
        raise RuntimeError(f"La release {release.tag} de deno no publica {asset_name}.sha256sum")

    zip_path = engine_dir() / "deno.zip.tmp"
    github_releases.download_file(asset.download_url, zip_path)

    sums_tmp = engine_dir() / f"{asset_name}.sha256sum.tmp"
    github_releases.download_file(sums_asset.download_url, sums_tmp)
    sums = checksums.parse_sha256sums(sums_tmp.read_text(encoding="utf-8"))
    sums_tmp.unlink(missing_ok=True)

    expected = sums.get(asset_name)
    if expected is None or not checksums.verify(zip_path, expected):
        zip_path.unlink(missing_ok=True)
        raise RuntimeError(f"Verificación de checksum fallida para {asset_name}")

    dest = binary_path()
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("deno") as src, dest.open("wb") as out:
            out.write(src.read())
    zip_path.unlink(missing_ok=True)

    dest.chmod(dest.stat().st_mode | 0o111)
    _write_state(release.tag)
    logger.info("deno instalado: version=%s", release.tag)
    return release.tag


def ensure_installed() -> Path:
    """Instala deno si no está presente todavía. No comprueba actualizaciones."""
    if not binary_path().is_file():
        _install_from_release()
    return binary_path()


def check_and_update() -> bool:
    """Comprueba si hay una versión más nueva de deno y la instala si hace falta."""
    if not binary_path().is_file():
        _install_from_release()
        return True

    state = _read_state()
    latest = github_releases.latest_release(_OWNER, _REPO)
    if latest.tag == state.get("tag"):
        return False

    _install_from_release()
    return True
