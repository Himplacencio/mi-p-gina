// Estilo «Clásico»: una sola barra abajo (vidrio) y escritorio limpio.
// La barra se crea desde cero: modificar la barra original de Plasma la dejaba invisible.
var APPS = ['preferred://filemanager', 'preferred://browser', 'applications:steam.desktop',
            'applications:moonos-tienda.desktop', 'applications:org.kde.konsole.desktop'];

desktops().forEach(function (d) {
    ['org.moonos.reloj', 'org.moonos.luna', 'org.moonos.calendario', 'org.moonos.musica'].forEach(function (t) {
        d.widgets(t).forEach(function (w) { w.remove(); });
    });
});
panels().forEach(function (p) { p.remove(); });

var p = new Panel;
p.location = 'bottom';
p.height = Math.round(gridUnit * 2.6);
var menu = p.addWidget('org.kde.plasma.kickoff');
try { menu.currentConfigGroup = ['General']; menu.writeConfig('icon', '/usr/share/pixmaps/moonos.png'); } catch (e) {}
var tareas = p.addWidget('org.kde.plasma.icontasks');
try { tareas.currentConfigGroup = ['General']; tareas.writeConfig('launchers', APPS.join(',')); tareas.reloadConfig(); } catch (e) {}
p.addWidget('org.kde.plasma.marginsseparator');
p.addWidget('org.moonos.musica');
p.addWidget('org.kde.plasma.systemtray');
p.addWidget('org.kde.plasma.digitalclock');
p.addWidget('org.kde.plasma.showdesktop');
try { p.lengthMode = 'fill'; p.floating = true; p.opacity = 'translucent'; } catch (e) {}
