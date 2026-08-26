"""Detección de "reducir movimiento" vía el portal de escritorio estándar
(org.freedesktop.portal.Desktop), no de una API específica de GNOME: así
funciona igual dentro del sandbox de Flatpak, sin permisos especiales.

Qt6 añadió QStyleHints.reduceMotion, pero esta versión de PySide6 no lo
expone (comprobado en desarrollo: el atributo no existe), así que se lee
directamente del portal.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, SLOT, Signal, Slot
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusVariant

from discargar.log import get_logger

logger = get_logger(__name__)

_PORTAL_SERVICE = "org.freedesktop.portal.Desktop"
_PORTAL_PATH = "/org/freedesktop/portal/desktop"
_SETTINGS_INTERFACE = "org.freedesktop.portal.Settings"
_NAMESPACE = "org.gnome.desktop.interface"
_KEY = "enable-animations"


def _unwrap(value):
    """Los valores del portal llegan envueltos en variantes anidadas."""
    while hasattr(value, "variant"):
        value = value.variant()
    return value


class ReducedMotion(QObject):
    """`active` es True cuando el sistema pide reducir movimiento."""

    changed = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._active = False

        bus = QDBusConnection.sessionBus()
        if not bus.isConnected():
            logger.warning("Sin bus de sesión D-Bus: se asume sin reducir movimiento")
            return

        iface = QDBusInterface(_PORTAL_SERVICE, _PORTAL_PATH, _SETTINGS_INTERFACE, bus)
        if iface.isValid():
            reply = iface.call("ReadOne", _NAMESPACE, _KEY)
            self._apply_enable_animations(_unwrap(reply.arguments()[0]) if reply.arguments() else None)
        else:
            logger.info("Portal de ajustes de escritorio no disponible; se asume sin reducir movimiento")

        connected = bus.connect(
            _PORTAL_SERVICE, _PORTAL_PATH, _SETTINGS_INTERFACE, "SettingChanged",
            self, SLOT("_on_setting_changed(QString,QString,QDBusVariant)"),
        )
        if not connected:
            logger.warning("No se pudo suscribir a cambios del portal de ajustes")

    @Slot(str, str, QDBusVariant)
    def _on_setting_changed(self, namespace: str, key: str, value) -> None:
        if namespace != _NAMESPACE or key != _KEY:
            return
        self._apply_enable_animations(_unwrap(value))

    def _apply_enable_animations(self, enable_animations) -> None:
        if not isinstance(enable_animations, bool):
            return
        active = not enable_animations
        if active != self._active:
            self._active = active
            logger.info("Reducir movimiento: %s", active)
            self.changed.emit()

    def _get_active(self) -> bool:
        return self._active

    active = Property(bool, fget=_get_active, notify=changed)  # type: ignore[arg-type]
