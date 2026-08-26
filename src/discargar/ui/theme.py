"""Tema editable de la app: colores, cristal, sombra, tipografía y
movimiento, en un archivo TOML legible en el directorio de configuración.
Se lee al arrancar y se recarga en caliente al detectar cambios.

También vive aquí el canal de actualización del motor (nightly/stable): el
propio CLAUDE.md lo describe como configurable "en el archivo de
tema/config", el mismo archivo.

Valores inválidos o fuera de rango se ignoran (con aviso en el log) y se usa
el valor por defecto de ese campo concreto — nunca se descarta el resto del
archivo por un solo campo mal escrito.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, Signal

from discargar.log import get_logger
from discargar.paths import config_dir

logger = get_logger(__name__)

THEME_FILENAME = "theme.toml"


def _is_color(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("#") and len(value) in (7, 9)


def _in_range(lo: float, hi: float) -> Callable[[Any], bool]:
    return lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi


def _is_choice(*choices: str) -> Callable[[Any], bool]:
    return lambda v: v in choices


@dataclass(frozen=True)
class _Field:
    section: str
    key: str
    qml_name: str
    default: Any
    validate: Callable[[Any], bool]


# Esta tabla ES el esquema del tema: cada fila es una clave del TOML, su
# nombre como propiedad de QML, su valor por defecto y su rango válido.
_FIELDS: list[_Field] = [
    _Field("gradient", "top", "gradientTop", "#e9ebee", _is_color),
    _Field("gradient", "bottom", "gradientBottom", "#fdfdfd", _is_color),
    _Field("glass", "opacity_decorative", "glassOpacityDecorative", 0.28, _in_range(0.0, 1.0)),
    _Field("glass", "opacity_content", "glassOpacityContent", 0.62, _in_range(0.0, 1.0)),
    _Field("glass", "refraction_strength", "glassRefractionStrength", 34.0, _in_range(0.0, 100.0)),
    _Field("glass", "refraction_reach", "glassRefractionReach", 40.0, _in_range(0.0, 150.0)),
    _Field("glass", "corner_radius", "glassCornerRadius", 24.0, _in_range(0.0, 60.0)),
    _Field("glass", "border_width", "glassBorderWidth", 1.0, _in_range(0.0, 6.0)),
    _Field("glass", "border_color", "glassBorderColor", "#40ffffff", _is_color),
    _Field("glass", "tint_color", "glassTintColor", "#3355aa", _is_color),
    _Field("glass", "tint_strength", "glassTintStrength", 0.06, _in_range(0.0, 0.5)),
    _Field("glass", "top_highlight_strength", "glassTopHighlightStrength", 0.35, _in_range(0.0, 1.0)),
    _Field("shadow", "color", "shadowColor", "#33223344", _is_color),
    _Field("shadow", "blur", "shadowBlur", 0.9, _in_range(0.0, 1.0)),
    _Field("shadow", "vertical_offset", "shadowVerticalOffset", 14.0, _in_range(0.0, 60.0)),
    _Field("typography", "family", "typographyFamily", "", lambda v: isinstance(v, str)),
    _Field("typography", "size_title", "typographySizeTitle", 26.0, _in_range(10.0, 60.0)),
    _Field("typography", "size_body", "typographySizeBody", 14.0, _in_range(8.0, 32.0)),
    _Field("motion", "transition_duration_ms", "motionTransitionDurationMs", 220.0, _in_range(0.0, 2000.0)),
    _Field("motion", "panel_grow", "motionPanelGrow", 1.05, _in_range(1.0, 1.5)),
    _Field("engine", "channel", "engineChannel", "nightly", _is_choice("nightly", "stable")),
]

_DEFAULT_TOML = """\
# Tema de discargar. Se recarga en caliente: guarda el archivo con la app
# abierta y verás el cambio al momento. Un valor fuera de rango o de tipo
# incorrecto se ignora (queda registrado en el log) y se usa el valor por
# defecto de esa clave concreta; el resto del archivo no se ve afectado.

[gradient]
top = "#e9ebee"      # gris claro
bottom = "#fdfdfd"   # casi blanco

[glass]
opacity_decorative = 0.28    # paneles solo decorativos
opacity_content = 0.62       # paneles con texto: deben quedar siempre legibles
refraction_strength = 34.0   # cuánto se dobla el fondo cerca del borde
refraction_reach = 40.0      # ancho de la franja de refracción, en píxeles
corner_radius = 24.0
border_width = 1.0
border_color = "#40ffffff"
tint_color = "#3355aa"       # tinte mínimo para que el cristal no sea blanco puro
tint_strength = 0.06
top_highlight_strength = 0.35

[shadow]
color = "#33223344"
blur = 0.9
vertical_offset = 14.0

[typography]
family = ""          # vacío = tipografía del sistema
size_title = 26.0
size_body = 14.0

[motion]
transition_duration_ms = 220.0
panel_grow = 1.05     # cuánto crece el panel principal al descargar

[engine]
channel = "nightly"   # "nightly" o "stable"
"""


class Theme(QObject):
    """Expone el tema a QML como propiedades que se actualizan solas."""

    changed = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._path: Path = config_dir() / THEME_FILENAME
        self._values: dict[str, Any] = {f.qml_name: f.default for f in _FIELDS}
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._ensure_file_exists()
        self.reload()

    def _ensure_file_exists(self) -> None:
        if not self._path.is_file():
            self._path.write_text(_DEFAULT_TOML, encoding="utf-8")
            logger.info("theme.toml creado con valores por defecto en %s", self._path)

    def reload(self) -> None:
        try:
            raw = tomllib.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            logger.warning("No se pudo leer %s (%s); se usan los valores por defecto", self._path, exc)
            raw = {}

        for field in _FIELDS:
            section = raw.get(field.section, {})
            value = section.get(field.key, field.default) if isinstance(section, dict) else field.default
            if not field.validate(value):
                logger.warning(
                    "theme.toml: [%s] %s = %r fuera de rango o inválido; usando %r",
                    field.section, field.key, value, field.default,
                )
                value = field.default
            self._values[field.qml_name] = float(value) if isinstance(field.default, float) else value

        if self._path.is_file() and str(self._path) not in self._watcher.files():
            self._watcher.addPath(str(self._path))

        self.changed.emit()

    def _on_file_changed(self, _path: str) -> None:
        # Algunos editores sustituyen el archivo en vez de escribirlo in-place;
        # el watcher deja de vigilar esa ruta y hay que volver a añadirla.
        self.reload()


def _make_property(qml_name: str, py_type: type) -> Property:
    def getter(self: Theme) -> Any:
        return self._values[qml_name]

    return Property(py_type, fget=getter, notify=Theme.changed)  # type: ignore[arg-type]


for _f in _FIELDS:
    _py_type = str if isinstance(_f.default, str) else float
    setattr(Theme, _f.qml_name, _make_property(_f.qml_name, _py_type))
del _f
