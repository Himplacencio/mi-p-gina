/*
 * Música en la barra — widget de MoonOS para el panel de KDE Plasma 6.
 * Muestra la canción que suena en Spotify (o en cualquier reproductor con
 * MPRIS): carátula, título, artista, cuánto falta y botones ⏮ ⏯ ⏭.
 * Se oculta solo cuando no suena nada.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.mpris as Mpris

PlasmoidItem {
    id: root

    Mpris.Mpris2Model { id: mpris }

    readonly property var player: mpris.currentPlayer
    readonly property string track: player ? (player.track || "") : ""
    readonly property string artist: player ? (player.artist || "") : ""
    readonly property string art: player ? (player.artUrl || "") : ""
    readonly property real lengthUs: player ? (player.length || 0) : 0
    readonly property real positionUs: player ? (player.position || 0) : 0
    readonly property bool hasMusic: track !== ""
    readonly property bool playing: !!player && (player.playbackStatus === Mpris.PlaybackStatus.Playing
                                                 || player.playbackStatus === 2)

    function fmt(us) {
        const s = Math.max(0, Math.round(us / 1000000))
        return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0")
    }
    function call(name) {
        if (player && typeof player[name] === "function") player[name]()
    }

    // La posición no se actualiza sola: se pide cada segundo mientras suena
    Timer {
        interval: 1000
        repeat: true
        running: root.playing
        onTriggered: root.call("updatePosition")
    }

    // En el escritorio es una tarjeta grande de vidrio; en la barra, una fila compacta
    readonly property bool enEscritorio: Plasmoid.formFactor === PlasmaCore.Types.Planar
    Plasmoid.backgroundHints: enEscritorio ? PlasmaCore.Types.TranslucentBackground : PlasmaCore.Types.DefaultBackground
    Plasmoid.status: (hasMusic || enEscritorio) ? PlasmaCore.Types.ActiveStatus : PlasmaCore.Types.HiddenStatus
    preferredRepresentation: fullRepresentation
    toolTipMainText: hasMusic ? track : i18n("Sin música")
    toolTipSubText: artist

    fullRepresentation: enEscritorio ? tarjeta : fila

    // ---------- Tarjeta grande (escritorio) ----------
    Component {
        id: tarjeta
        Item {
            id: card
            Layout.preferredWidth: Kirigami.Units.gridUnit * 16
            Layout.preferredHeight: Kirigami.Units.gridUnit * 7
            Layout.minimumWidth: Kirigami.Units.gridUnit * 12
            Layout.minimumHeight: Kirigami.Units.gridUnit * 6

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Kirigami.Units.smallSpacing * 2
                spacing: Kirigami.Units.smallSpacing
                RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Item {
                        Layout.preferredWidth: card.height * 0.45
                        Layout.preferredHeight: Layout.preferredWidth
                        Image {
                            id: bigCover
                            anchors.fill: parent
                            source: root.art
                            fillMode: Image.PreserveAspectCrop
                            visible: status === Image.Ready
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: 10
                            visible: !bigCover.visible
                            gradient: Gradient {
                                GradientStop { position: 0; color: "#a996ff" }
                                GradientStop { position: 1; color: "#5a3fd8" }
                            }
                            Text { anchors.centerIn: parent; text: "♪"; color: "white"; font.pixelSize: parent.height * 0.5 }
                        }
                    }
                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text {
                            text: root.hasMusic ? root.track : "Nada sonando"
                            color: "#ffffff"; font.pixelSize: 19; font.weight: Font.Bold
                            elide: Text.ElideRight; Layout.fillWidth: true
                        }
                        Text {
                            text: root.hasMusic ? root.artist : "Abre Spotify y dale play 🎵"
                            color: "#d8d2ff"; font.pixelSize: 14
                            elide: Text.ElideRight; Layout.fillWidth: true
                        }
                    }
                }
                // Progreso con tiempos
                RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Text { text: root.fmt(root.positionUs); color: "#d8d2ff"; font.pixelSize: 11; font.family: "monospace" }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 5
                        radius: 2.5
                        color: Qt.rgba(1, 1, 1, 0.2)
                        Rectangle {
                            height: parent.height; radius: parent.radius; color: "#ffffff"
                            width: root.lengthUs > 0 ? parent.width * Math.min(1, root.positionUs / root.lengthUs) : 0
                        }
                    }
                    Text {
                        text: root.lengthUs > 0 ? "-" + root.fmt(root.lengthUs - root.positionUs) : "-0:00"
                        color: "#d8d2ff"; font.pixelSize: 11; font.family: "monospace"
                    }
                }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: Kirigami.Units.gridUnit
                    PC3.ToolButton { icon.name: "media-skip-backward"; onClicked: root.call("Previous") }
                    PC3.ToolButton {
                        icon.name: root.playing ? "media-playback-pause" : "media-playback-start"
                        icon.width: Kirigami.Units.iconSizes.medium; icon.height: icon.width
                        onClicked: root.call("PlayPause")
                    }
                    PC3.ToolButton { icon.name: "media-skip-forward"; onClicked: root.call("Next") }
                }
            }
        }
    }

    // ---------- Fila compacta (barra de tareas) ----------
    Component {
        id: fila
    Item {
        id: box
        visible: root.hasMusic
        Layout.minimumWidth: root.hasMusic ? row.implicitWidth + Kirigami.Units.smallSpacing * 2 : 0
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.fillHeight: true

        RowLayout {
            id: row
            anchors.fill: parent
            anchors.leftMargin: Kirigami.Units.smallSpacing
            anchors.rightMargin: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            // Carátula (o una nota musical si el reproductor no manda imagen)
            Item {
                Layout.preferredWidth: Math.min(box.height - 8, 32)
                Layout.preferredHeight: Layout.preferredWidth
                Image {
                    id: cover
                    anchors.fill: parent
                    source: root.art
                    fillMode: Image.PreserveAspectCrop
                    visible: status === Image.Ready
                    smooth: true
                }
                Kirigami.Icon {
                    anchors.fill: parent
                    source: "media-default-album"
                    visible: !cover.visible
                }
            }

            ColumnLayout {
                spacing: 0
                Layout.maximumWidth: Kirigami.Units.gridUnit * 10
                PC3.Label {
                    text: root.track
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                    Layout.maximumWidth: Kirigami.Units.gridUnit * 10
                }
                PC3.Label {
                    text: root.artist
                    opacity: 0.7
                    font: Kirigami.Theme.smallFont
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                    Layout.maximumWidth: Kirigami.Units.gridUnit * 10
                }
                // Barra de progreso fina
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 3
                    radius: 1.5
                    color: Qt.rgba(1, 1, 1, 0.15)
                    Rectangle {
                        height: parent.height
                        radius: parent.radius
                        width: root.lengthUs > 0 ? parent.width * Math.min(1, root.positionUs / root.lengthUs) : 0
                        color: Kirigami.Theme.highlightColor
                    }
                }
            }

            // Cuánto falta para que termine
            PC3.Label {
                text: root.lengthUs > 0 ? "-" + root.fmt(root.lengthUs - root.positionUs) : ""
                font.family: "monospace"
                opacity: 0.85
                visible: text !== ""
            }

            PC3.ToolButton {
                icon.name: "media-skip-backward"
                onClicked: root.call("Previous")
                PC3.ToolTip.text: i18n("Anterior")
            }
            PC3.ToolButton {
                icon.name: root.playing ? "media-playback-pause" : "media-playback-start"
                onClicked: root.call("PlayPause")
                PC3.ToolTip.text: root.playing ? i18n("Pausar") : i18n("Reproducir")
            }
            PC3.ToolButton {
                icon.name: "media-skip-forward"
                onClicked: root.call("Next")
                PC3.ToolTip.text: i18n("Siguiente")
            }
        }
    }
    }
}
