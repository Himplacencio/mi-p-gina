// Estilo «MoonOS Dock»: barra superior + dock centrado + widgets de vidrio en el escritorio.
// Se ejecuta con el intérprete de scripts de Plasma (evaluateScript).
// Las barras se crean desde cero: modificar la barra original de Plasma la dejaba invisible.
var APPS = ['preferred://filemanager', 'preferred://browser', 'applications:steam.desktop',
            'applications:moonos-tienda.desktop', 'applications:moonos-luna.desktop', 'applications:org.kde.konsole.desktop'];

function lanzadores(tareas) {
    try {
        tareas.currentConfigGroup = ['General'];
        tareas.writeConfig('launchers', APPS.join(','));
        tareas.reloadConfig();
    } catch (e) {}
}

panels().forEach(function (p) { p.remove(); });

// 1) Barra superior
var top = new Panel;
top.location = 'top';
top.height = Math.round(gridUnit * 1.7);
try { top.floating = false; top.opacity = 'translucent'; } catch (e) {}
var menu = top.addWidget('org.kde.plasma.kickoff');
try { menu.currentConfigGroup = ['General']; menu.writeConfig('icon', '/usr/share/pixmaps/moonos.png'); } catch (e) {}
top.addWidget('org.kde.plasma.appmenu');
top.addWidget('org.kde.plasma.panelspacer');
top.addWidget('org.kde.plasma.digitalclock');
top.addWidget('org.kde.plasma.panelspacer');
top.addWidget('org.moonos.musica');
top.addWidget('org.kde.plasma.systemtray');

// 2) Dock abajo: solo las apps, centrado, flotante y de vidrio
var dock = new Panel;
dock.location = 'bottom';
dock.height = Math.round(gridUnit * 3.4);
lanzadores(dock.addWidget('org.kde.plasma.icontasks'));
try { dock.lengthMode = 'fit'; dock.alignment = 'center'; dock.floating = true; dock.opacity = 'translucent'; } catch (e) {}

// 3) Widgets de vidrio en el escritorio (pantalla principal), dejando libre
//    la columna de iconos de la izquierda (p. ej. «Instalar MoonOS»)
var d = desktopForScreen(0) || desktops()[0];
if (d && d.widgets('org.moonos.reloj').length === 0) {
    var g = gridUnit;
    d.addWidget('org.moonos.reloj', g * 7, g * 3, g * 15, g * 10.5);
    d.addWidget('org.moonos.luna', g * 23, g * 3, g * 17, g * 10.5);
    d.addWidget('org.moonos.calendario', g * 7, g * 14.5, g * 33, g * 12);
    d.addWidget('org.moonos.musica', g * 7, g * 27.5, g * 33, g * 11.5);
}
