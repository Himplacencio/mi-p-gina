/* Fase lunar (MoonOS): la luna de esta noche, calculada en el propio equipo. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    // Mes sinódico y luna nueva de referencia (6 de enero de 2000, 18:14 UTC)
    readonly property real synodic: 29.530588853
    readonly property real refNew: Date.UTC(2000, 0, 6, 18, 14)
    property real age: 0
    function update() {
        const d = (Date.now() - refNew) / 86400000
        age = ((d % synodic) + synodic) % synodic
    }
    readonly property real illum: (1 - Math.cos(2 * Math.PI * age / synodic)) / 2
    readonly property string phaseName: ["Luna nueva", "Luna creciente", "Cuarto creciente", "Gibosa creciente",
                                         "Luna llena", "Gibosa menguante", "Cuarto menguante", "Luna menguante"][Math.round(age / synodic * 8) % 8]
    readonly property int daysToFull: Math.round(((synodic / 2 - age) + synodic) % synodic)

    Timer { interval: 600000; running: true; repeat: true; triggeredOnStart: true; onTriggered: root.update() }

    Plasmoid.backgroundHints: PlasmaCore.Types.TranslucentBackground
    preferredRepresentation: fullRepresentation

    fullRepresentation: Item {
        id: box
        Layout.preferredWidth: Kirigami.Units.gridUnit * 13
        Layout.preferredHeight: Kirigami.Units.gridUnit * 6
        Layout.minimumWidth: Kirigami.Units.gridUnit * 10
        Layout.minimumHeight: Kirigami.Units.gridUnit * 5

        RowLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing * 2
            spacing: Kirigami.Units.largeSpacing

            Canvas {
                id: canvas
                Layout.preferredWidth: Math.min(box.height - 16, 96)
                Layout.preferredHeight: Layout.preferredWidth
                // Redibujar cuando cambia la fase
                Connections { target: root; function onAgeChanged() { canvas.requestPaint() } }
                Component.onCompleted: requestPaint()
                onPaint: {
                    const c = getContext("2d"), R = width / 2 - 2, cx = width / 2, cy = height / 2
                    c.reset()
                    c.fillStyle = "#2a2456"
                    c.beginPath(); c.arc(cx, cy, R, 0, 2 * Math.PI); c.fill()
                    // Para cada altura, la parte iluminada va del borde de la luna (limbo)
                    // a la línea de sombra (terminador), que depende de la fase.
                    const waxing = root.age < root.synodic / 2
                    const k = Math.cos(2 * Math.PI * root.age / root.synodic)
                    const steps = 48, limb = [], term = []
                    for (let i = 0; i <= steps; i++) {
                        const y = -R + 2 * R * i / steps
                        const w = Math.sqrt(Math.max(0, R * R - y * y))
                        limb.push([cx + (waxing ? w : -w), cy + y])
                        term.push([cx + (waxing ? k * w : -k * w), cy + y])
                    }
                    c.fillStyle = "#f4ecd0"
                    c.beginPath()
                    c.moveTo(limb[0][0], limb[0][1])
                    for (const p of limb) c.lineTo(p[0], p[1])
                    for (let i = term.length - 1; i >= 0; i--) c.lineTo(term[i][0], term[i][1])
                    c.closePath(); c.fill()
                }
            }
            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true
                Text { text: "Esta noche"; color: "#a7a2cf"; font.pixelSize: 13; font.weight: Font.Bold }
                Text { text: root.phaseName; color: "#ffffff"; font.pixelSize: Math.min(21, box.width / 15); font.weight: Font.DemiBold; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: Math.round(root.illum * 100) + " % iluminada"; color: "#f4ecd0"; font.pixelSize: 14 }
                Text {
                    text: root.daysToFull === 0 ? "¡Hoy hay luna llena! 🌕" : "Luna llena en " + root.daysToFull + (root.daysToFull === 1 ? " día" : " días")
                    color: "#d8d2ff"; font.pixelSize: 13
                }
            }
        }
    }
}
