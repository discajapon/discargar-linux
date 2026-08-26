import QtQuick

// Fondo de la ventana: degradado muy suave de gris claro a blanco, con
// estructura tenue en movimiento lento (formas de color muy leve).
//
// Esa estructura es necesaria para que la refracción del cristal se perciba:
// sobre un degradado totalmente plano no hay nada que distorsionar. Las
// formas se pintan con un gradiente radial propio (no con blur posterior):
// el blur pesado aplana el contraste local en el borde de cada forma justo
// donde el cristal necesita algo que doblar, así que aquí la suavidad viene
// de la opacidad baja, no de difuminar el contorno.
Item {
    id: root

    // La ventana real la pausa cuando pierde el foco y la vuelve instantánea
    // si el sistema pide reducir movimiento; aquí solo se expone el gancho.
    property bool animated: true

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: theme.gradientTop }
            GradientStop { position: 1.0; color: theme.gradientBottom }
        }
    }

    component Blob: Canvas {
        id: blob
        property color tint: "#7fa7d8"
        property real peakAlpha: 0.5

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            var r = Math.min(width, height) / 2
            var cx = width / 2
            var cy = height / 2
            var grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r)
            var c = tint
            grad.addColorStop(0.0, Qt.rgba(c.r, c.g, c.b, peakAlpha))
            grad.addColorStop(0.55, Qt.rgba(c.r, c.g, c.b, peakAlpha * 0.85))
            grad.addColorStop(0.82, Qt.rgba(c.r, c.g, c.b, peakAlpha * 0.35))
            grad.addColorStop(1.0, Qt.rgba(c.r, c.g, c.b, 0.0))
            ctx.fillStyle = grad
            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, 2 * Math.PI)
            ctx.fill()
        }
    }

    Blob {
        id: blobA
        width: root.width * 0.55
        height: width
        tint: "#4c7fd6"
        peakAlpha: 0.32
        x: root.width * 0.05
        y: root.height * 0.05

        SequentialAnimation on x {
            running: root.animated
            loops: Animation.Infinite
            NumberAnimation { to: root.width * 0.22; duration: 14000; easing.type: Easing.InOutSine }
            NumberAnimation { to: root.width * 0.05; duration: 14000; easing.type: Easing.InOutSine }
        }
    }

    Blob {
        id: blobB
        width: root.width * 0.45
        height: width
        tint: "#d6708f"
        peakAlpha: 0.28
        x: root.width * 0.5
        y: root.height * 0.45

        SequentialAnimation on y {
            running: root.animated
            loops: Animation.Infinite
            NumberAnimation { to: root.height * 0.6; duration: 18000; easing.type: Easing.InOutSine }
            NumberAnimation { to: root.height * 0.4; duration: 18000; easing.type: Easing.InOutSine }
        }
    }

    Blob {
        id: blobC
        width: root.width * 0.4
        height: width
        tint: "#4fb583"
        peakAlpha: 0.26
        x: root.width * 0.15
        y: root.height * 0.55

        SequentialAnimation on x {
            running: root.animated
            loops: Animation.Infinite
            NumberAnimation { to: root.width * 0.35; duration: 16000; easing.type: Easing.InOutSine }
            NumberAnimation { to: root.width * 0.1; duration: 16000; easing.type: Easing.InOutSine }
        }
    }
}
