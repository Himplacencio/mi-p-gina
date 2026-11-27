/* Reloj (MoonOS): reloj grande de vidrio para el escritorio. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    property date now: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    Plasmoid.backgroundHints: PlasmaCore.Types.TranslucentBackground
    preferredRepresentation: fullRepresentation

    fullRepresentation: Item {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 11
        Layout.preferredHeight: Kirigami.Units.gridUnit * 8
        Layout.minimumWidth: Kirigami.Units.gridUnit * 8
        Layout.minimumHeight: Kirigami.Units.gridUnit * 6

        Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(root.now, "hh:mm")
                color: "#ffffff"
                font.pixelSize: Math.min(parent.parent.width / 3.2, parent.parent.height / 1.9)
                font.weight: Font.Light
                font.letterSpacing: -2
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.locale().toString(root.now, Qt.locale().name.startsWith("es") ? "dddd d 'de' MMMM" : "dddd, MMMM d")
                color: "#d8d2ff"
                font.pixelSize: Math.max(13, parent.parent.height / 11)
                font.weight: Font.DemiBold
            }
        }
    }
}
