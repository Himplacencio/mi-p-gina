/* Presentación que se muestra mientras se instala MoonOS */
import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 9000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    function onActivate() { presentation.currentSlide = 0; }
    function onLeave() { }

    component MoonSlide: Slide {
        property string heading
        property string body
        Rectangle { anchors.fill: parent; color: "#14122b" }
        Image {
            source: "logo.png"
            width: 140; height: 140
            fillMode: Image.PreserveAspectFit
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top; anchors.topMargin: 40
        }
        Text {
            text: heading
            color: "#ece6ff"; font.pixelSize: 30; font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
            y: 200
        }
        Text {
            text: body
            color: "#c8c2e8"; font.pixelSize: 17
            wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
            width: parent.width * 0.75
            anchors.horizontalCenter: parent.horizontalCenter
            y: 260
        }
    }

    MoonSlide {
        heading: "Bienvenido a MoonOS"
        body: "Un sistema basado en Arch Linux y CachyOS, pensado para jugar y para el día a día."
    }
    MoonSlide {
        heading: "Listo para jugar"
        body: "Steam, Lutris, GameMode, MangoHud y Gamescope vienen preinstalados."
    }
    MoonSlide {
        heading: "Drivers automáticos"
        body: "MoonOS detecta tu tarjeta gráfica (NVIDIA, AMD o Intel) e instala los drivers adecuados."
    }
    MoonSlide {
        heading: "Kernel de CachyOS"
        body: "El kernel linux-cachyos está optimizado para dar más rendimiento y menos latencia."
    }
}
