"""Punto de entrada de discargar.

Crea la aplicación Qt, registra el tema, la detección de "reducir
movimiento", las licencias y el backend como propiedades de contexto de
QML, y carga la ventana principal.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from discargar.log import get_logger
from discargar.ui.backend import AppBackend
from discargar.ui.licenses import Licenses
from discargar.ui.motion import ReducedMotion
from discargar.ui.theme import Theme

logger = get_logger(__name__)


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("discargar")
    app.setOrganizationName("disca_japon")
    # Debe coincidir con el nombre base del .desktop instalado para que
    # GNOME agrupe la ventana con el icono correcto: "discargar" en la
    # instalación nativa, o el app-id completo bajo Flatpak (FLATPAK_ID lo
    # trae puesto el propio sandbox).
    app.setDesktopFileName(os.environ.get("FLATPAK_ID", "discargar"))

    theme = Theme()
    reduced_motion = ReducedMotion()
    licenses = Licenses()
    backend = AppBackend(theme)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("theme", theme)
    context.setContextProperty("reducedMotion", reduced_motion)
    context.setContextProperty("licenses", licenses)
    context.setContextProperty("backend", backend)

    qml_dir = Path(__file__).parent / "ui" / "qml"
    engine.load(str(qml_dir / "Main.qml"))
    if not engine.rootObjects():
        logger.error("No se pudo cargar Main.qml")
        return 1

    exit_code = app.exec()
    # Destruir el motor QML explícitamente mientras theme/backend/licenses
    # siguen vivos evita que sus bindings se reevalúen contra objetos ya
    # liberados durante el cierre (si no, Qt registra warnings inofensivos
    # pero ruidosos justo al salir).
    del engine
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
