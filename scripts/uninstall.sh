#!/usr/bin/env bash
# Desinstala discargar. Por defecto conserva el tema, los logs y la copia
# gestionada de yt-dlp/deno (config/estado/datos del usuario); con --purge
# también los borra.
set -euo pipefail

PURGE=0
if [ "${1:-}" = "--purge" ]; then
    PURGE=1
fi

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/discargar"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/discargar"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/discargar"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

rm -f "$BIN_DIR/discargar"
rm -f "$APPS_DIR/discargar.desktop"
rm -f "$ICON_DIR/discargar.svg"
rm -rf "$DATA_DIR/venv"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true

echo "discargar desinstalado (lanzador, entrada de menú, icono y entorno virtual)."

if [ "$PURGE" = "1" ]; then
    rm -rf "$DATA_DIR" "$CONFIG_DIR" "$STATE_DIR"
    echo "--purge: también se borraron $DATA_DIR, $CONFIG_DIR y $STATE_DIR"
    echo "(tema, logs, y la copia gestionada de yt-dlp/deno)."
else
    echo "Se conservan: $CONFIG_DIR (tema), $STATE_DIR (logs) y $DATA_DIR (yt-dlp/deno)."
    echo "Para borrarlos también: $0 --purge"
fi
