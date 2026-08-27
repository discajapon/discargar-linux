#!/usr/bin/env bash
# Instala discargar para el usuario actual: entorno virtual aislado en
# ~/.local/share/discargar/venv, lanzador en ~/.local/bin, entrada .desktop
# e icono en el menú de aplicaciones. No toca el Python del sistema, así
# que funciona igual en distribuciones con PEP 668 (entorno "externally
# managed"): pip solo se usa dentro del venv, nunca con --break-system-packages.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/discargar"
VENV_DIR="$DATA_DIR/venv"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

echo "Instalando discargar en $DATA_DIR ..."

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Error: 'python3 -m venv' no funciona en este sistema." >&2
    echo "En Debian/Ubuntu el módulo venv va en un paquete aparte:" >&2
    echo "    sudo apt install python3-venv" >&2
    echo "Instálalo y vuelve a ejecutar este script." >&2
    exit 1
fi

mkdir -p "$DATA_DIR" "$BIN_DIR" "$APPS_DIR" "$ICON_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install "$REPO_DIR" --quiet

ln -sf "$VENV_DIR/bin/discargar" "$BIN_DIR/discargar"

cp "$REPO_DIR/data/icons/discargar.svg" "$ICON_DIR/discargar.svg"
cp "$REPO_DIR/data/discargar.desktop" "$APPS_DIR/discargar.desktop"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || true

echo "Listo. Discargar debería aparecer en el menú de aplicaciones."

case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "Aviso: $BIN_DIR no está en tu PATH. Añádelo en tu ~/.bashrc o ~/.profile para poder ejecutar 'discargar' desde la terminal." ;;
esac

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Aviso: no se encontró ffmpeg en el sistema. discargar lo necesita para unir vídeo y audio;"
    echo "instálalo con el gestor de paquetes de tu distribución (p. ej. 'sudo apt install ffmpeg')."
fi
