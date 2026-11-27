// Pantalla de carga de MoonOS: la luna y el nombre sobre el fondo índigo
import QtQuick

Rectangle {
    id: root
    color: "#0d0b24"
    property int stage

    onStageChanged: {
        if (stage === 2) entrada.start()
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0d0b24" }
            GradientStop { position: 1.0; color: "#241c5c" }
        }
    }

    Column {
        id: contenido
        anchors.centerIn: parent
        spacing: 28
        opacity: 0

        Image {
            id: luna
            anchors.horizontalCenter: parent.horizontalCenter
            source: "images/luna.png"
            width: 128; height: 128
            sourceSize: Qt.size(256, 256)
            smooth: true
            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.06; duration: 1400; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.06; to: 1.0; duration: 1400; easing.type: Easing.InOutSine }
            }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "MoonOS"
            color: "#ece8ff"
            font.pixelSize: 40
            font.weight: Font.Bold
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 220; height: 4; radius: 2
            color: "#2e2768"
            Rectangle {
                width: parent.width * Math.min(1, root.stage / 6); height: parent.height; radius: 2
                color: "#a996ff"
                Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
            }
        }
    }

    OpacityAnimator { id: entrada; target: contenido; from: 0; to: 1; duration: 600; easing.type: Easing.InOutQuad }
    Component.onCompleted: entrada.start()
}
