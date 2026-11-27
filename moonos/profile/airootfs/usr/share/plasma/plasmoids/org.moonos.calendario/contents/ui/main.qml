/* Calendario (MoonOS): el mes actual con el día de hoy marcado. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    property date today: new Date()
    // Se refresca cada minuto (por si cambia el día)
    Timer { interval: 60000; running: true; repeat: true; onTriggered: root.today = new Date() }

    readonly property int year: today.getFullYear()
    readonly property int month: today.getMonth()
    // Lunes = 0 … domingo = 6
    readonly property int firstWeekday: (new Date(year, month, 1).getDay() + 6) % 7
    readonly property int daysInMonth: new Date(year, month + 1, 0).getDate()

    Plasmoid.backgroundHints: PlasmaCore.Types.TranslucentBackground
    preferredRepresentation: fullRepresentation

    fullRepresentation: Item {
        id: box
        Layout.preferredWidth: Kirigami.Units.gridUnit * 13
        Layout.preferredHeight: Kirigami.Units.gridUnit * 10
        Layout.minimumWidth: Kirigami.Units.gridUnit * 10
        Layout.minimumHeight: Kirigami.Units.gridUnit * 8
        readonly property real cell: Math.min(width / 7.4, (height - 40) / 7.2)

        RowLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing * 2
            spacing: Kirigami.Units.largeSpacing

            // Día grande a la izquierda
            ColumnLayout {
                Layout.alignment: Qt.AlignTop
                spacing: 0
                Text {
                    text: Qt.locale().toString(root.today, "dddd").toUpperCase()
                    color: "#ff8094"
                    font.pixelSize: box.cell * 0.42
                    font.weight: Font.Bold
                }
                Text {
                    text: root.today.getDate()
                    color: "#ffffff"
                    font.pixelSize: box.cell * 1.9
                    font.weight: Font.Light
                }
                Item { Layout.fillHeight: true }
                Text {
                    text: Qt.locale().toString(root.today, "MMMM yyyy")
                    color: "#d8d2ff"
                    font.pixelSize: box.cell * 0.42
                }
            }

            // Mes
            Grid {
                Layout.alignment: Qt.AlignTop | Qt.AlignRight
                columns: 7
                Repeater {
                    model: ["L", "M", "X", "J", "V", "S", "D"]
                    Text {
                        required property string modelData
                        width: box.cell; height: box.cell * 0.9
                        text: modelData
                        color: "#a7a2cf"
                        font.pixelSize: box.cell * 0.4
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                Repeater {
                    model: 42
                    Item {
                        required property int index
                        readonly property int day: index - root.firstWeekday + 1
                        readonly property bool valid: day >= 1 && day <= root.daysInMonth
                        readonly property bool isToday: valid && day === root.today.getDate()
                        width: box.cell; height: box.cell * 0.9
                        visible: index < 35 || root.firstWeekday + root.daysInMonth > 35
                        Rectangle {
                            anchors.centerIn: parent
                            width: Math.min(parent.width, parent.height) * 0.92
                            height: width
                            radius: width / 2
                            color: "#a996ff"
                            visible: parent.isToday
                        }
                        Text {
                            anchors.centerIn: parent
                            text: parent.valid ? parent.day : ""
                            color: parent.isToday ? "#120e2e" : "#eeeaff"
                            font.pixelSize: box.cell * 0.42
                            font.weight: parent.isToday ? Font.Bold : Font.Normal
                        }
                    }
                }
            }
        }
    }
}
