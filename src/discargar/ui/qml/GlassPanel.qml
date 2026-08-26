import QtQuick
import QtQuick.Effects

// Lámina de cristal líquido: refracción real (GPU) concentrada en una franja
// estrecha del borde, casi limpia en el centro, con filo claro arriba,
// sombra amplia y difusa debajo, y un tinte mínimo que evita el blanco puro.
// Todos los valores por defecto vienen del tema (recarga en caliente).
//
// Requiere `backdrop`: el Item de fondo del que se captura la refracción.
Item {
    id: root

    property Item backdrop
    property real cornerRadius: theme.glassCornerRadius
    property real refractionStrength: theme.glassRefractionStrength
    property real edgeWidth: theme.glassRefractionReach
    property real refractionPadding: 48
    property color tintColor: theme.glassTintColor
    property real tintStrength: theme.glassTintStrength
    // Los paneles con texto son notablemente más opacos que los decorativos.
    property bool isContentPanel: false
    property real glassOpacity: isContentPanel ? theme.glassOpacityContent : theme.glassOpacityDecorative
    property real topHighlightStrength: theme.glassTopHighlightStrength

    // El panel principal, mientras descarga: crece y pierde opacidad (queda
    // "cristal limpio"), manteniendo borde y sombra. Instantáneo si el
    // sistema pide reducir movimiento.
    property bool active: false
    property real activeGrow: theme.motionPanelGrow
    property real activeOpacity: 0.04
    readonly property int transitionDuration: reducedMotion.active ? 0 : theme.motionTransitionDurationMs

    scale: active ? activeGrow : 1.0
    Behavior on scale {
        NumberAnimation { duration: root.transitionDuration; easing.type: Easing.InOutQuad }
    }

    // Sombra amplia y difusa debajo del panel.
    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        radius: root.cornerRadius
        color: "transparent"
        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: theme.shadowColor
            shadowBlur: theme.shadowBlur
            shadowVerticalOffset: theme.shadowVerticalOffset
            shadowHorizontalOffset: 0
            shadowScale: 1.0
        }
    }

    ShaderEffectSource {
        id: bgSource
        sourceItem: root.backdrop
        live: true
        hideSource: false
        visible: false
        sourceRect: {
            if (!root.backdrop) return Qt.rect(0, 0, 1, 1)
            var pos = root.mapToItem(root.backdrop, -root.refractionPadding, -root.refractionPadding)
            return Qt.rect(pos.x, pos.y,
                            root.width + 2 * root.refractionPadding,
                            root.height + 2 * root.refractionPadding)
        }
    }

    ShaderEffect {
        id: glass
        anchors.fill: parent

        property variant source: bgSource
        property vector2d itemSize: Qt.vector2d(root.width, root.height)
        property real cornerRadius: root.cornerRadius
        property real edgeWidth: root.edgeWidth
        property real refractionStrength: root.refractionStrength
        property real padding: root.refractionPadding
        property vector4d tintColor: Qt.vector4d(
            root.tintColor.r, root.tintColor.g, root.tintColor.b, root.tintStrength)
        property real topHighlightStrength: root.topHighlightStrength

        fragmentShader: Qt.resolvedUrl("../shaders/refraction.frag.qsb")
    }

    // Panel translúcido adicional: sube la opacidad general para que el
    // contenido con texto sea legible sobre cualquier zona del fondo,
    // manteniéndose por encima del cristal decorativo.
    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: "#ffffff"
        opacity: root.active ? root.activeOpacity : root.glassOpacity
        Behavior on opacity {
            NumberAnimation { duration: root.transitionDuration; easing.type: Easing.InOutQuad }
        }
    }

    // Filo claro adicional en el borde superior (contorno fino, no solo el
    // aporte del shader), y borde sutil en el resto. Se mantiene incluso en
    // estado activo: "manteniendo borde y sombra" (requisito 4).
    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: "transparent"
        border.width: theme.glassBorderWidth
        border.color: theme.glassBorderColor
    }

    default property alias content: contentArea.data
    Item {
        id: contentArea
        anchors.fill: parent
    }
}
