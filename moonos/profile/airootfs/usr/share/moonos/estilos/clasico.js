// Estilo «Clásico»: una sola barra abajo (vidrio) y escritorio limpio.
panels().forEach(function (p) { if (p.location === 'top') p.remove(); });
desktops().forEach(function (d) {
    ['org.moonos.reloj', 'org.moonos.luna', 'org.moonos.calendario', 'org.moonos.musica'].forEach(function (t) {
        d.widgets(t).forEach(function (w) { w.remove(); });
    });
});
panels().forEach(function (p) {
    if (p.location !== 'bottom') return;
    var tipos = p.widgets().map(function (w) { return w.type; });
    if (tipos.indexOf('org.kde.plasma.kickoff') < 0) {
        // Rehacer la barra en el orden habitual, conservando la lista de apps
        p.widgets().forEach(function (w) {
            if (w.type !== 'org.kde.plasma.icontasks' && w.type !== 'org.kde.plasma.taskmanager') w.remove();
        });
        var tareas = p.widgets()[0];
        p.addWidget('org.kde.plasma.kickoff');
        if (tareas) { var t = tareas.type; tareas.remove(); p.addWidget(t); }
        p.addWidget('org.kde.plasma.marginsseparator');
        p.addWidget('org.moonos.musica');
        p.addWidget('org.kde.plasma.systemtray');
        p.addWidget('org.kde.plasma.digitalclock');
        p.addWidget('org.kde.plasma.showdesktop');
    }
    try { p.lengthMode = 'fill'; p.alignment = 'left'; p.floating = true; p.opacity = 'translucent'; } catch (e) {}
    p.height = Math.round(gridUnit * 2.6);
});
