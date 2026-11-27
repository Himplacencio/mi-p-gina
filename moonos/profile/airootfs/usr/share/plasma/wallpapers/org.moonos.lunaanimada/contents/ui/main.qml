/*
 * Luna animada — fondo de pantalla animado de MoonOS para KDE Plasma 6.
 * Cielo con estrellas que titilan, luna que flota y «respira», nubes que
 * pasan, estrellas fugaces de vez en cuando y montañas con algo de profundidad.
 * Todo son animaciones suaves y lentas para gastar pocos recursos.
 */
import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root

    // ---------- Cielo ----------
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0a0920" }
            GradientStop { position: 0.65; color: "#221a52" }
            GradientStop { position: 1.0; color: "#3a2a7a" }
        }
    }

    // ---------- Estrellas ----------
    Item {
        id: stars
        anchors.fill: parent

        Repeater {
            model: 160
            delegate: Rectangle {
                id: star
                required property int index
                // Posición y tamaño pseudoaleatorios pero estables (no cambian al redimensionar)
                function hash(n) { const v = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return v - Math.floor(v) }
                readonly property real rx: hash(index * 3 + 1)
                readonly property real ry: hash(index * 3 + 2)
                readonly property real rs: hash(index * 3 + 3)
                readonly property real base: 0.35 + rs * 0.6
                x: rx * stars.width
                y: ry * stars.height * 0.78
                width: 1.2 + rs * rs * 2.4
                height: width
                radius: width / 2
                color: "#ffffff"
                opacity: base

                // Una de cada tres estrellas titila, cada una a su ritmo
                SequentialAnimation on opacity {
                    running: star.index % 3 === 0
                    loops: Animation.Infinite
                    PauseAnimation { duration: (star.index * 137) % 4000 }
                    NumberAnimation { to: 0.15; duration: 1400 + (star.index * 53) % 1800; easing.type: Easing.InOutSine }
                    NumberAnimation { to: star.base; duration: 1400 + (star.index * 71) % 1800; easing.type: Easing.InOutSine }
                }
            }
        }
    }

    // ---------- Estrella fugaz ----------
    Item {
        id: shooting
        width: Math.max(140, root.width * 0.09)
        height: 2
        opacity: 0
        rotation: 18
        Rectangle {
            anchors.fill: parent
            radius: 1
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 1.0; color: "#ffffff" }
            }
        }
        ParallelAnimation {
            id: shoot
            NumberAnimation { target: shooting; property: "x"; from: shootTimer.sx; to: shootTimer.sx + root.width * 0.28; duration: 900; easing.type: Easing.OutQuad }
            NumberAnimation { target: shooting; property: "y"; from: shootTimer.sy; to: shootTimer.sy + root.width * 0.09; duration: 900; easing.type: Easing.OutQuad }
            SequentialAnimation {
                NumberAnimation { target: shooting; property: "opacity"; to: 1; duration: 120 }
                PauseAnimation { duration: 380 }
                NumberAnimation { target: shooting; property: "opacity"; to: 0; duration: 400 }
            }
        }
        Timer {
            id: shootTimer
            property real sx: 0
            property real sy: 0
            interval: 9000
            running: true
            repeat: true
            onTriggered: {
                sx = Math.random() * root.width * 0.6
                sy = Math.random() * root.height * 0.3
                interval = 8000 + Math.random() * 14000
                shoot.restart()
            }
        }
    }

    // ---------- Luna ----------
    Image {
        id: moon
        source: Qt.resolvedUrl("../images/luna.png")
        readonly property real size: Math.min(root.width, root.height) * 0.46
        width: size
        height: size
        smooth: true
        x: root.width * 0.74 - width / 2 + drift
        y: root.height * 0.30 - height / 2 + bob
        property real bob: 0
        property real drift: 0

        // Flota suavemente arriba y abajo
        SequentialAnimation on bob {
            loops: Animation.Infinite
            NumberAnimation { from: -10; to: 10; duration: 6500; easing.type: Easing.InOutSine }
            NumberAnimation { from: 10; to: -10; duration: 6500; easing.type: Easing.InOutSine }
        }
        // Se desplaza muy despacio de lado a lado
        SequentialAnimation on drift {
            loops: Animation.Infinite
            NumberAnimation { from: -root.width * 0.02; to: root.width * 0.02; duration: 40000; easing.type: Easing.InOutSine }
            NumberAnimation { from: root.width * 0.02; to: -root.width * 0.02; duration: 40000; easing.type: Easing.InOutSine }
        }
        // El brillo «respira»
        SequentialAnimation on scale {
            loops: Animation.Infinite
            NumberAnimation { from: 1.0; to: 1.025; duration: 4000; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.025; to: 1.0; duration: 4000; easing.type: Easing.InOutSine }
        }
    }

    // ---------- Nubes ----------
    Repeater {
        model: 2
        delegate: Image {
            id: cloud
            required property int index
            source: Qt.resolvedUrl("../images/nube.png")
            width: root.width * (0.45 + index * 0.15)
            height: width * 0.26
            y: root.height * (0.12 + index * 0.18)
            opacity: 0.22 + index * 0.08
            smooth: true
            // t va de 0 a 1: la nube cruza la pantalla de izquierda a derecha
            property real t: index * 0.55
            x: -width + (t % 1) * (root.width + width)
            NumberAnimation on t {
                from: cloud.index * 0.55
                to: 1 + cloud.index * 0.55
                duration: 140000 + cloud.index * 60000
                loops: Animation.Infinite
            }
        }
    }

    // ---------- Montañas (dos capas con leve efecto de profundidad) ----------
    Image {
        id: backHills
        source: Qt.resolvedUrl("../images/montanas-fondo.png")
        width: root.width * 1.25
        height: root.height * 0.30
        y: root.height - height
        x: -root.width * 0.12 + sway
        property real sway: 0
        SequentialAnimation on sway {
            loops: Animation.Infinite
            NumberAnimation { from: -18; to: 18; duration: 30000; easing.type: Easing.InOutSine }
            NumberAnimation { from: 18; to: -18; duration: 30000; easing.type: Easing.InOutSine }
        }
    }
    Image {
        source: Qt.resolvedUrl("../images/montanas-frente.png")
        width: root.width * 1.25
        height: root.height * 0.22
        y: root.height - height
        x: -root.width * 0.12 - backHills.sway * 0.5
    }
}
