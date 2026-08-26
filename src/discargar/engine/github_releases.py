"""Cliente mínimo de la API de GitHub Releases.

Se usa tanto para yt-dlp (stable y nightly son repos distintos) como para
deno. Sin dependencias externas: solo urllib de la librería estándar.
"""

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "discargar (https://discajapon.com)"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str


@dataclass(frozen=True)
class Release:
    tag: str
    assets: list[ReleaseAsset]

    def asset(self, name: str) -> ReleaseAsset | None:
        for a in self.assets:
            if a.name == name:
                return a
        return None


def latest_release(owner: str, repo: str) -> Release:
    """Consulta la última release publicada de un repositorio de GitHub.

    Lanza urllib.error.URLError/HTTPError si no hay conexión o la API falla;
    quien llama decide cómo clasificar ese error.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)
    assets = [
        ReleaseAsset(name=a["name"], download_url=a["browser_download_url"])
        for a in data["assets"]
    ]
    return Release(tag=data["tag_name"], assets=assets)


def download_file(url: str, destination) -> None:
    """Descarga `url` al Path `destination`, sobrescribiendo si ya existe."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)
