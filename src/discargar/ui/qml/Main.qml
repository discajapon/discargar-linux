import QtQuick
import QtQuick.Window

// Ventana principal: título, campo de URL con botón de pegar, botón de
// descarga que se convierte en indicador de progreso, línea de estado, y el
// icono discreto de ajustes. `theme`, `reducedMotion` y `backend` llegan
// como propiedades de contexto desde app.py.
Window {
    id: mainWindow
    width: 420
    height: 620
    minimumWidth: 380
    minimumHeight: 560
    maximumWidth: 460
    maximumHeight: 700
    visible: true
    title: "Discargar"
    color: theme.gradientBottom

    Background {
        id: background
        anchors.fill: parent
        animated: mainWindow.active && !reducedMotion.active
    }

    Rectangle {
        id: settingsButton
        width: 34
        height: 34
        radius: 17
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 16
        color: settingsMouse.containsMouse ? "#14000000" : "transparent"

        Text {
            anchors.centerIn: parent
            text: "⚙"
            font.pixelSize: 17
            color: "#5c6472"
        }

        MouseArea {
            id: settingsMouse
            objectName: "settingsMouse"
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: settingsPopup.open()
        }
    }

    GlassPanel {
        id: mainPanel
        backdrop: background
        isContentPanel: true
        active: backend.isDownloading
        anchors.horizontalCenter: parent.horizontalCenter
        y: 108
        width: parent.width - 64
        height: 300

        Column {
            anchors.centerIn: parent
            width: parent.width - 56
            spacing: 20

            Text {
                text: "Discargar"
                font.pixelSize: theme.typographySizeTitle
                font.family: theme.typographyFamily.length > 0 ? theme.typographyFamily : Qt.application.font.family
                font.weight: Font.DemiBold
                color: "#1c1f26"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Campo de URL con botón de pegar evidente.
            Rectangle {
                width: parent.width
                height: 46
                radius: 12
                color: "#ffffff"
                opacity: 0.75
                border.width: 1
                border.color: "#22000000"

                TextInput {
                    id: urlInput
                    objectName: "urlInput"
                    anchors.left: parent.left
                    anchors.right: pasteButton.left
                    anchors.leftMargin: 14
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    font.pixelSize: theme.typographySizeBody
                    color: "#20232b"
                    clip: true
                    selectByMouse: true
                    enabled: !backend.isDownloading

                    Text {
                        visible: urlInput.text.length === 0
                        text: qsTr("Paste a video link…")
                        color: "#9aa0ac"
                        font: urlInput.font
                    }
                }

                Rectangle {
                    id: pasteButton
                    width: 34
                    height: 34
                    radius: 8
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    color: pasteMouse.containsMouse ? "#14000000" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "⧉"
                        font.pixelSize: 17
                        color: "#5c6472"
                    }

                    MouseArea {
                        id: pasteMouse
                        objectName: "pasteMouse"
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !backend.isDownloading
                        onClicked: urlInput.text = backend.pasteFromClipboard()
                    }
                }
            }

            // Botón de descarga; mientras descarga se convierte en indicador
            // de progreso y es clicable para cancelar.
            Rectangle {
                id: actionButton
                width: parent.width
                height: 46
                radius: 14
                color: "#2f6fed"
                opacity: (backend.isEngineReady || backend.isDownloading) ? 1.0 : 0.5
                clip: true

                Rectangle {
                    visible: backend.isDownloading && backend.progressFraction >= 0
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    width: parent.width * Math.max(0, Math.min(1, backend.progressFraction))
                    color: "#1c4fc4"
                }

                Text {
                    anchors.centerIn: parent
                    text: backend.isDownloading ? qsTr("Cancel") : qsTr("Download")
                    color: "white"
                    font.pixelSize: 15
                    font.weight: Font.Medium
                }

                MouseArea {
                    objectName: "actionMouse"
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    enabled: backend.isEngineReady || backend.isDownloading
                    onClicked: backend.isDownloading
                        ? backend.cancelDownload()
                        : backend.startDownload(urlInput.text)
                }
            }

            Text {
                text: backend.statusText
                color: "#5c6472"
                font.pixelSize: 13
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap
            }
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        text: "disca_japon 2026 · discajapon.com"
        font.pixelSize: 11
        color: "#9aa0ac"
    }

    SettingsPanel {
        id: settingsPopup
        objectName: "settingsPopup"
        anchors.centerIn: parent
    }
}
