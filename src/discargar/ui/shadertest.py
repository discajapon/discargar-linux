"""Prueba mínima y aislada del shader de refracción, corriendo en una
ventana real (no offscreen) para validar también la integración con Wayland.

Uso:
    python -m discargar.ui.shadertest [ruta_salida.png]

Muestra la ventana, deja que la animación de fondo corra un momento y
guarda una captura antes de cerrarse sola.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    out_path = Path(argv[1]) if len(argv) > 1 else Path("shader_test.png")
    scene = argv[2] if len(argv) > 2 else "ShaderTest.qml"

    app = QGuiApplication(sys.argv)
    qml_dir = Path(__file__).parent / "qml"
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(qml_dir / scene)))
    if view.status() == QQuickView.Status.Error:
        for error in view.errors():
            print(error.toString(), file=sys.stderr)
        return 1

    view.setResizeMode(QQuickView.ResizeMode.SizeViewToRootObject)
    view.show()

    def grab_and_quit() -> None:
        image = view.grabWindow()
        image.save(str(out_path))
        print(f"Captura guardada en {out_path}")
        app.quit()

    QTimer.singleShot(1200, grab_and_quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
