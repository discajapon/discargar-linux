import QtQuick
import QtQuick.Effects

// Lámina de cristal líquido: refracción real (GPU) concentrada en una franja
// estrecha del borde, casi limpia en el centro, con filo claro arriba,
// sombra amplia y difusa debajo, y un tinte mínimo que evita el blanco puro.
//
// Requiere `backdrop`: el Item de fondo del que se captura la refracción.
Item {
    id: root

    property Item backdrop
    property real cornerRadius: 24
    property real refractionStrength: 18
    property real edgeWidth: 28
    property real refractionPadding: 48
    property color tintColor: "#3355aa"
    property real tintStrength: 0.06
    // Los paneles con texto son notablemente más opacos que los decorativos.
    property real glassOpacity: 0.5
    property real topHighlightStrength: 0.35

    // Sombra amplia y difusa debajo del panel.
    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        radius: root.cornerRadius
        color: "transparent"
        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: "#33223344"
            shadowBlur: 0.9
            shadowVerticalOffset: 14
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
        opacity: root.glassOpacity
    }

    // Filo claro adicional en el borde superior (contorno fino, no solo el
    // aporte del shader), y sombra de contorno sutil en el resto.
    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: "transparent"
        border.width: 1
        border.color: "#40ffffff"
    }

    default property alias content: contentArea.data
    Item {
        id: contentArea
        anchors.fill: parent
    }
}
