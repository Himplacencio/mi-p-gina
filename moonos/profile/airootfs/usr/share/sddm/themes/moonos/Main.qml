// Pantalla de inicio de sesión de MoonOS (tema de SDDM, Qt 6)
// Fondo de la luna desenfocado, reloj grande, tarjeta de vidrio con el usuario y la contraseña,
// y abajo: usuario, sesión y botones de suspender / reiniciar / apagar.
import QtQuick
import QtQuick.Effects

Rectangle {
    id: root
    width: 1920; height: 1080
    color: "#0d0b24"

    readonly property color acento: "#a996ff"
    readonly property color texto: "#f1eeff"
    readonly property color suave: "#b9b2e6"
    readonly property var es: Qt.locale("es_ES")
    function conf(clave, porDefecto) {
        try { const v = config.stringValue ? config.stringValue(clave) : config[clave]; return v ? v : porDefecto }
        catch (e) { return porDefecto }
    }

    // ---------- datos de SDDM ----------
    property int usuario: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property int sesion: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    Repeater { id: usuarios; model: userModel
        delegate: Item { property string nombre: model.name; property string real: model.realName || ""; property string icono: model.icon || "" } }
    Repeater { id: sesiones; model: sessionModel
        delegate: Item { property string nombre: model.name } }
    readonly property var actual: usuarios.count > 0 ? usuarios.itemAt(Math.min(usuario, usuarios.count - 1)) : null
    readonly property string nombreUsuario: actual ? actual.nombre : ""
    readonly property string nombreVisible: actual ? (actual.real !== "" ? actual.real : actual.nombre) : "Usuario"
    readonly property string nombreSesion: sesiones.count > 0 && sesiones.itemAt(Math.min(sesion, sesiones.count - 1))
                                           ? sesiones.itemAt(Math.min(sesion, sesiones.count - 1)).nombre : "Plasma"

    function entrar() {
        if (clave.text === "" || ocupado) return
        ocupado = true; error.text = ""
        sddm.login(nombreUsuario, clave.text, sesion)
    }
    property bool ocupado: false
    Connections {
        target: sddm
        function onLoginFailed() {
            root.ocupado = false; clave.text = ""; clave.forceActiveFocus()
            error.text = "Contraseña incorrecta. Inténtalo de nuevo."; temblor.start()
        }
        function onLoginSucceeded() { error.text = "" }
    }

    // ---------- fondo ----------
    // El fondo viene ya desenfocado (fondo.jpg): así no depende de efectos de la tarjeta gráfica.
    // Si en theme.conf se pone otra imagen en «background», se usa esa tal cual.
    Image {
        anchors.fill: parent
        source: root.conf("background", "fondo.jpg")
        fillMode: Image.PreserveAspectCrop
    }
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#990d0b24" }
            GradientStop { position: 0.55; color: "#550d0b24" }
            GradientStop { position: 1.0; color: "#cc07061a" }
        }
    }

    // ---------- arriba: marca y reloj ----------
    Row {
        anchors { left: parent.left; top: parent.top; margins: 34 }
        spacing: 12
        Image { source: "luna.png"; width: 30; height: 30; sourceSize: Qt.size(60, 60); anchors.verticalCenter: parent.verticalCenter }
        Text { text: "MoonOS"; color: root.texto; font.pixelSize: 20; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
    }
    Column {
        id: reloj
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: parent.height * 0.11 }
        spacing: 4
        property date ahora: new Date()
        Timer { interval: 1000; running: true; repeat: true; onTriggered: reloj.ahora = new Date() }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(reloj.ahora, "HH:mm")
            color: root.texto; font.pixelSize: 128; font.weight: Font.Light
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: { const s = root.es.toString(reloj.ahora, "dddd d 'de' MMMM"); return s.charAt(0).toUpperCase() + s.slice(1) }
            color: root.suave; font.pixelSize: 26
        }
    }

    // ---------- tarjeta de vidrio ----------
    Item {
        id: tarjeta
        width: 440; height: contenido.implicitHeight + 64
        anchors { horizontalCenter: parent.horizontalCenter; top: reloj.bottom; topMargin: parent.height * 0.07 }

        Rectangle {
            anchors.fill: parent; radius: 28
            color: "#3318163f"; border.color: "#40c9bdff"; border.width: 1
        }
        Column {
            id: contenido
            anchors.centerIn: parent
            spacing: 18
            width: parent.width - 64

            // foto o inicial
            Item {
                width: 108; height: 108; anchors.horizontalCenter: parent.horizontalCenter
                Rectangle {
                    anchors.fill: parent; radius: width / 2
                    gradient: Gradient {
                        GradientStop { position: 0; color: "#b3a0ff" }
                        GradientStop { position: 1; color: "#6f5bd6" }
                    }
                    border.color: "#80ffffff"; border.width: 2
                    Text {
                        anchors.centerIn: parent; visible: foto.status !== Image.Ready
                        text: root.nombreVisible.charAt(0).toUpperCase()
                        color: "white"; font.pixelSize: 48; font.weight: Font.DemiBold
                    }
                }
                Image {
                    id: foto; anchors.fill: parent; anchors.margins: 3
                    source: root.actual && root.actual.icono !== "" ? "file://" + root.actual.icono.replace("file://", "") : ""
                    fillMode: Image.PreserveAspectCrop; visible: false
                }
                MultiEffect {
                    anchors.fill: foto; source: foto; visible: foto.status === Image.Ready
                    maskEnabled: true; maskSource: mascara
                }
                Item { id: mascara; anchors.fill: foto; layer.enabled: true; visible: false
                    Rectangle { anchors.fill: parent; radius: width / 2 } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.nombreVisible
                color: root.texto; font.pixelSize: 26; font.weight: Font.DemiBold
            }

            // contraseña
            Rectangle {
                id: caja
                width: parent.width; height: 54; radius: 27
                color: "#55100e30"
                border.width: clave.activeFocus ? 2 : 1
                border.color: clave.activeFocus ? root.acento : "#50c9bdff"
                Behavior on border.color { ColorAnimation { duration: 180 } }
                SequentialAnimation on x {
                    id: temblor; running: false
                    NumberAnimation { to: -12; duration: 50 } NumberAnimation { to: 12; duration: 70 }
                    NumberAnimation { to: -8; duration: 60 } NumberAnimation { to: 0; duration: 60 }
                }
                TextInput {
                    id: clave; objectName: "clave"
                    anchors { left: parent.left; right: boton.left; verticalCenter: parent.verticalCenter; leftMargin: 24; rightMargin: 10 }
                    echoMode: TextInput.Password; passwordCharacter: "●"
                    color: root.texto; font.pixelSize: 20; selectionColor: root.acento
                    focus: true; clip: true
                    Keys.onReturnPressed: root.entrar(); Keys.onEnterPressed: root.entrar()
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: clave.text === ""; text: "Contraseña"; color: "#8f88c4"; font.pixelSize: 19
                    }
                }
                Rectangle {
                    id: boton
                    width: 42; height: 42; radius: 21
                    anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                    color: zona.containsMouse ? "#bcadff" : root.acento
                    opacity: clave.text === "" ? 0.45 : 1
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                    Text { anchors.centerIn: parent; text: root.ocupado ? "…" : "→"; color: "#14103a"; font.pixelSize: 22; font.weight: Font.Bold }
                    MouseArea { id: zona; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.entrar() }
                }
            }
            Text {
                id: error
                width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
                color: "#ffb4c8"; font.pixelSize: 16; text: ""
            }
            Text {
                width: parent.width; horizontalAlignment: Text.AlignHCenter
                visible: { try { return keyboard.capsLock } catch (e) { return false } }
                text: "⇪  Mayúsculas activadas"; color: "#ffd8a0"; font.pixelSize: 15
            }
        }
    }

    // ---------- abajo: usuario, sesión y energía ----------
    component Chip: Rectangle {
        id: chip
        property string etiqueta: ""
        property string icono: ""
        signal pulsado()
        height: 44; width: fila.width + 32; radius: 22
        color: area.containsMouse ? "#44302a78" : "#2a1a1745"
        border.color: "#38c9bdff"; border.width: 1
        Row { id: fila; anchors.centerIn: parent; spacing: 8
            Text { text: chip.icono; color: root.suave; font.pixelSize: 17; anchors.verticalCenter: parent.verticalCenter; visible: chip.icono !== "" }
            Text { text: chip.etiqueta; color: root.texto; font.pixelSize: 16; anchors.verticalCenter: parent.verticalCenter; visible: chip.etiqueta !== "" } }
        MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: chip.pulsado() }
    }
    Row {
        anchors { left: parent.left; bottom: parent.bottom; margins: 34 }
        spacing: 12
        Chip { icono: "👤"; etiqueta: usuarios.count > 1 ? root.nombreVisible + "  ▾" : root.nombreVisible
               onPulsado: { if (usuarios.count > 1) { root.usuario = (root.usuario + 1) % usuarios.count; clave.text = ""; error.text = ""; clave.forceActiveFocus() } } }
        Chip { icono: "🖥"; etiqueta: sesiones.count > 1 ? root.nombreSesion + "  ▾" : root.nombreSesion
               onPulsado: { if (sesiones.count > 1) root.sesion = (root.sesion + 1) % sesiones.count; clave.forceActiveFocus() } }
    }
    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 34 }
        spacing: 12
        Chip { icono: "☾"; etiqueta: "Suspender"; visible: !sddm || sddm.canSuspend; onPulsado: sddm.suspend() }
        Chip { icono: "↻"; etiqueta: "Reiniciar"; visible: !sddm || sddm.canReboot; onPulsado: sddm.reboot() }
        Chip { icono: "⏻"; etiqueta: "Apagar"; visible: !sddm || sddm.canPowerOff; onPulsado: sddm.powerOff() }
    }

    Component.onCompleted: clave.forceActiveFocus()
}
