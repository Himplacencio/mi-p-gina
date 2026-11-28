# 🌙 MoonOS

**MoonOS** es una distribución Linux para jugar, basada en **Arch Linux** y **CachyOS**.

- **Kernel `linux-cachyos`:** optimizado para rendimiento y baja latencia.
- **Escritorio KDE Plasma ligero:** Dolphin, Konsole, Firefox, Haruna (vídeo), KWrite y Ark. Sin programas de relleno: usa menos de 1,5 GB de RAM y la ISO pesa menos de 4 GB.
- **Drivers automáticos:** detecta tu tarjeta gráfica (NVIDIA, AMD o Intel) y deja instalados solo los drivers que necesitas, usando `chwd` de CachyOS.
- **Listo para jugar:** Steam, Lutris, GameMode, MangoHud y Gamescope. Steam descarga Proton por su cuenta. Si quieres Proton-CachyOS: `sudo pacman -S proton-cachyos`.
- **Instalador gráfico (Calamares)** con sistema de archivos Btrfs y compresión zstd.
- **Flatpak** preinstalado para instalar más programas fácilmente.
- **Seguridad:** firewall (ufw) activado de serie: bloquea lo que intenta entrar sin permiso y deja salir todo (internet, Steam y juegos funcionan igual; Steam Remote Play queda permitido). Se apaga o prende en Bienvenida → Hazlo tuyo → Seguridad.

## Bienvenida y personalización

- **Bienvenida a MoonOS** se abre sola al iniciar. En el modo Live tiene el botón **Instalar MoonOS** y muestra el equipo detectado; ya instalado, da la bienvenida y lleva a personalizar. Se puede desactivar con «Mostrar al iniciar».
- **Modo PC antiguo** (Hazlo tuyo → Efectos): apaga desenfoque, transparencias, animaciones y el fondo animado para PCs lentos. La Bienvenida lo sugiere sola si el equipo tiene ≤ 4,5 GB de RAM o ≤ 2 núcleos.
- **Hazlo tuyo:** tema oscuro o claro, 8 colores de acento, fondo (luna animada, luna clásica o una imagen propia), panel abajo, arriba o a la izquierda, estilo clásico o dock tipo Mac, panel flotante, ventanas gelatina y animaciones rápidas.
- **Tienda MoonOS:** instala Spotify, Discord, Chrome, Brave, Heroic, OBS, LibreOffice y más con un clic, o busca cualquier otra app en Flathub. Las apps se instalan aisladas (Flatpak, sin contraseña) y no pueden dañar el sistema. Está anclada en la barra.
- **Estilo MoonOS Dock** (en «Hazlo tuyo»): barra superior con menú, reloj al centro, música y bandeja; dock centrado y flotante abajo; y widgets de vidrio en el escritorio: reloj, fase lunar (calculada en el equipo), calendario y tarjeta de música. Es el **estilo de inicio por defecto**; el botón «Clásico» lo deja con una sola barra abajo.
- **Barra de vidrio y música:** barra flotante y translúcida con colores MoonOS; el widget «Música en la barra» muestra la canción de Spotify (u otro reproductor), cuánto falta y botones ⏮ ⏯ ⏭.
- **Luna animada:** fondo animado para Plasma (`org.moonos.lunaanimada`) con estrellas que titilan, luna que flota, nubes y estrellas fugaces. También aparece en *Configurar escritorio y fondo de pantalla → Tipo de fondo*.

## Modo juego automático

Cuando abres un juego, MoonOS pone todo el equipo a su servicio, y lo devuelve a la normalidad al cerrarlo:

- **CPU al máximo:** GameMode cambia el gobernador de la CPU y el perfil de energía a "rendimiento".
- **Prioridad para el juego:** el juego recibe más prioridad de CPU y de disco que cualquier otro programa.
- **GPU AMD al máximo:** en tarjetas AMD, la GPU se fija en su frecuencia más alta. MoonOS detecta la tarjeta al arrancar y lo configura solo.
- **Tareas de fondo en pausa:** el indexador de archivos de KDE (Baloo) viene apagado de serie, y si lo activas se pausa mientras juegas.
- **Sin interrupciones:** no salta el protector de pantalla.
- **Steam ya viene configurado:** su acceso directo lo abre con `gamemoderun`, así que todos tus juegos de Steam usan el modo juego sin tocar nada. En Lutris, GameMode viene activado de serie.

Al activarse y desactivarse verás una notificación. Para comprobarlo en la terminal: `gamemoded -s`.

A esto se suman el kernel de CachyOS (planificador BORE, optimizado para baja latencia) y los ajustes del sistema de `cachyos-settings`.

## Cómo conseguir la ISO

La ISO se construye automáticamente en GitHub cada vez que cambia algo en esta carpeta:

1. En GitHub, abre la pestaña **Actions** del repositorio.
2. Entra en la última ejecución de **"Construir ISO de MoonOS"** que tenga ✅.
3. Abajo, en **Artifacts**, descarga **`moonos-iso`** (un `.zip` con la `.iso` dentro).

También puedes lanzarla a mano desde **Actions → Construir ISO de MoonOS → Run workflow**.

## Probarla e instalarla

1. **Pruébala primero en una máquina virtual**, por ejemplo VirtualBox o GNOME Boxes. Dale al menos 4 GB de RAM y 40 GB de disco, y activa EFI si puedes.
2. Para instalarla en un PC, graba la ISO en un USB de 8 GB o más con [Ventoy](https://www.ventoy.net), [Rufus](https://rufus.ie) o [balenaEtcher](https://etcher.balena.io).
3. Arranca desde el USB. Entrarás directamente al escritorio de MoonOS (modo Live).
4. Haz doble clic en **"Instalar MoonOS"** en el escritorio.

> ⚠️ El instalador puede borrar el disco que elijas. Haz una copia de seguridad antes de instalar en un PC con datos.

Si al instalar hay internet, MoonOS actualiza el sistema y configura los drivers en ese momento. Si no hay internet, lo hace en el primer arranque con conexión. El registro queda en `/var/log/moonos-drivers.log`.

## Estructura

```
moonos/
├── build.sh                      # Script que construye la ISO
└── profile/                      # Perfil de archiso
    ├── profiledef.sh             # Nombre, versión y opciones de la ISO
    ├── packages.x86_64           # Lista de paquetes (¡edítala para añadir programas!)
    ├── pacman.conf               # Repositorios usados al construir
    └── airootfs/                 # Archivos que se copian al sistema
        ├── etc/                  # Configuración (idioma, teclado, servicios...)
        └── usr/
            ├── local/bin/        # Scripts de MoonOS (drivers, post-instalación...)
            └── share/
                ├── moonos/calamares/   # Configuración y marca del instalador
                ├── wallpapers/MoonOS/  # Fondo de pantalla
                └── pixmaps/moonos.png  # Logo
```

`build.sh` toma los menús de arranque oficiales del perfil `releng` de archiso, los adapta al kernel de CachyOS y al nombre MoonOS, y les añade este perfil encima.

## Personalizar

| Quiero cambiar…        | Archivo                                                            |
|------------------------|--------------------------------------------------------------------|
| Programas incluidos    | `profile/packages.x86_64`                                          |
| Idioma del modo Live   | `profile/airootfs/etc/locale.conf` (ahora `es_MX.UTF-8`)           |
| Teclado del modo Live  | `etc/vconsole.conf` y `etc/X11/xorg.conf.d/00-keyboard.conf` (ahora latinoamericano) |
| Fondo de pantalla      | `usr/share/wallpapers/MoonOS/contents/images/1920x1080.png`        |
| Logo                   | `usr/share/pixmaps/moonos.png` y `usr/share/moonos/calamares/branding/moonos/logo.png` |
| Pasos del instalador   | `usr/share/moonos/calamares/`                                      |

## Construir en tu propio PC (opcional)

En Arch Linux, CachyOS o cualquier Linux con Docker:

```bash
# En Arch / CachyOS:
sudo ./moonos/build.sh

# Con Docker, en cualquier Linux:
sudo docker run --rm --privileged -v "$PWD":/src archlinux:latest bash /src/moonos/build.sh
```

La ISO queda en `moonos/out/`.

## Limitaciones conocidas

- En el **modo Live** se usa el driver NVIDIA "open", que solo funciona en GPUs NVIDIA **GTX 16xx / RTX 20xx o más nuevas**. Con tarjetas NVIDIA más antiguas, el Live puede quedarse en pantalla negra. Una vez instalado, `chwd` elige el driver correcto.
- MoonOS usa los repositorios de CachyOS y Arch. Las actualizaciones (`sudo pacman -Syu`) vienen directamente de ellos.
