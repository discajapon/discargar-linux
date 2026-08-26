import QtQuick
import QtQuick.Controls

// Pantalla de ajustes: solo licencias, créditos y el correo de feedback
// (requisito 28), nada más. `licenses` llega como propiedad de contexto.
Popup {
    id: root
    width: 340
    height: 460
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property string openLicenseFile: ""

    onClosed: openLicenseFile = ""

    background: Rectangle {
        radius: 20
        color: "#fbfbfc"
        border.width: 1
        border.color: "#e2e5eb"
    }

    contentItem: Item {
        anchors.fill: parent

        Column {
            visible: root.openLicenseFile === ""
            anchors.fill: parent
            anchors.margins: 22
            spacing: 20

            Text {
                text: qsTr("About")
                font.pixelSize: 17
                font.weight: Font.DemiBold
                color: "#1c1f26"
            }

            Column {
                width: parent.width
                spacing: 8
                Text { text: qsTr("Credits"); font.pixelSize: 12; color: "#9aa0ac"; font.weight: Font.Medium }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    font.pixelSize: 13
                    color: "#33363f"
                    text: qsTr("Powered by yt-dlp and FFmpeg.")
                }
            }

            Column {
                width: parent.width
                spacing: 4
                Text { text: qsTr("Licenses"); font.pixelSize: 12; color: "#9aa0ac"; font.weight: Font.Medium }
                Repeater {
                    model: licenses.entries
                    delegate: Rectangle {
                        width: parent.width
                        height: 34
                        radius: 8
                        color: licenseMouse.containsMouse ? "#14000000" : "transparent"

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 8
                            Text { text: modelData.name; font.pixelSize: 13; color: "#20232b" }
                            Text { text: modelData.spdx; font.pixelSize: 11; color: "#9aa0ac" }
                        }

                        MouseArea {
                            id: licenseMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.openLicenseFile = modelData.file
                        }
                    }
                }
            }

            Column {
                width: parent.width
                spacing: 4
                Text { text: qsTr("Feedback"); font.pixelSize: 12; color: "#9aa0ac"; font.weight: Font.Medium }
                Text { text: "disca_japon@proton.me"; font.pixelSize: 13; color: "#2f6fed" }
            }
        }

        Column {
            visible: root.openLicenseFile !== ""
            anchors.fill: parent
            anchors.margins: 22
            spacing: 14

            Text {
                text: "‹ " + qsTr("Back")
                color: "#2f6fed"
                font.pixelSize: 13
                MouseArea { anchors.fill: parent; onClicked: root.openLicenseFile = "" }
            }

            Flickable {
                width: parent.width
                height: parent.height - 34
                clip: true
                contentWidth: width
                contentHeight: licenseText.implicitHeight
                boundsBehavior: Flickable.StopAtBounds

                Text {
                    id: licenseText
                    width: parent.width
                    text: root.openLicenseFile !== "" ? licenses.text(root.openLicenseFile) : ""
                    font.pixelSize: 11
                    font.family: "monospace"
                    color: "#33363f"
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
