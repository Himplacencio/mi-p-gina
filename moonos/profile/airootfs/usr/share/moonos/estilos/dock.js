// Estilo «MoonOS Dock»: barra superior + dock centrado + widgets de vidrio en el escritorio.
// Se ejecuta con el intérprete de scripts de Plasma (evaluateScript).
var abajo = panels().filter(function (p) { return p.location === 'bottom'; });
var arriba = panels().filter(function (p) { return p.location === 'top'; });

// 1) Barra superior (solo si no existe ya)
if (arriba.length === 0) {
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
}

// 2) La barra de abajo se convierte en un dock: solo las apps, centrado y flotante
abajo.forEach(function (p) {
    p.widgets().forEach(function (w) {
        if (w.type !== 'org.kde.plasma.icontasks' && w.type !== 'org.kde.plasma.taskmanager') w.remove();
    });
    try { p.lengthMode = 'fit'; p.alignment = 'center'; p.floating = true; p.opacity = 'translucent'; } catch (e) {}
    p.height = Math.round(gridUnit * 3.4);
});

// 3) Widgets de vidrio en el escritorio (pantalla principal)
var d = desktopForScreen(0) || desktops()[0];
if (d && d.widgets('org.moonos.reloj').length === 0) {
    var g = gridUnit;
    d.addWidget('org.moonos.reloj', g * 2, g * 3, g * 15, g * 10.5);
    d.addWidget('org.moonos.luna', g * 18, g * 3, g * 17, g * 10.5);
    d.addWidget('org.moonos.calendario', g * 2, g * 14.5, g * 33, g * 12);
    d.addWidget('org.moonos.musica', g * 2, g * 27.5, g * 33, g * 11.5);
}
