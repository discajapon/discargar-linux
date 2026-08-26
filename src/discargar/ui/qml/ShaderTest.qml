import QtQuick

// Prueba mínima y aislada del shader de refracción sobre el fondo previsto,
// tal como pide el CLAUDE.md antes de construir la ventana real encima.
// Reproduce el tamaño aproximado de la ventana final y dos paneles: uno
// decorativo (menos opaco) y uno con texto (más opaco, como pide el
// requisito 10) para comprobar que el texto queda legible en todo caso.
Item {
    id: root
    width: 420
    height: 640

    Background {
        id: bg
        anchors.fill: parent
    }

    // Panel decorativo: cristal más limpio, deja ver bien la refracción.
    GlassPanel {
        backdrop: bg
        x: 40
        y: 60
        width: root.width - 80
        height: 140
        glassOpacity: 0.28
        refractionStrength: 34
        edgeWidth: 40
    }

    // Panel con texto: notablemente más opaco, el texto debe leerse siempre.
    GlassPanel {
        id: textPanel
        backdrop: bg
        x: 30
        y: 260
        width: root.width - 60
        height: 260
        glassOpacity: 0.62

        Column {
            anchors.centerIn: parent
            spacing: 18
            width: parent.width - 48

            Text {
                text: "Discargar"
                font.pixelSize: 26
                font.weight: Font.DemiBold
                color: "#1c1f26"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Rectangle {
                width: parent.width
                height: 44
                radius: 12
                color: "#ffffff"
                opacity: 0.7
                border.width: 1
                border.color: "#22000000"

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    text: "https://ejemplo.com/video-de-prueba"
                    color: "#33363f"
                    font.pixelSize: 13
                    elide: Text.ElideRight
                    width: parent.width - 28
                }
            }

            Rectangle {
                width: parent.width
                height: 46
                radius: 14
                color: "#2f6fed"
                anchors.horizontalCenter: parent.horizontalCenter

                Text {
                    anchors.centerIn: parent
                    text: "Descargar"
                    color: "white"
                    font.pixelSize: 15
                    font.weight: Font.Medium
                }
            }
        }
    }

    // Panel pequeño extra cerca de una esquina, para comprobar la
    // refracción de estructura de fondo cercana a los bordes de la ventana.
    GlassPanel {
        backdrop: bg
        x: root.width - 90
        y: 20
        width: 50
        height: 50
        cornerRadius: 25
        glassOpacity: 0.3
    }
}
