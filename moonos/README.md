# 🌙 MoonOS

**MoonOS** es una distribución Linux para jugar, basada en **Arch Linux** y **CachyOS**.

- **Kernel `linux-cachyos`:** optimizado para rendimiento y baja latencia.
- **Escritorio KDE Plasma completo:** Dolphin, Konsole, Kate, Firefox, VLC, etc.
- **Drivers automáticos:** detecta tu tarjeta gráfica (NVIDIA, AMD o Intel) y deja instalados solo los drivers que necesitas, usando `chwd` de CachyOS.
- **Listo para jugar:** Steam, Lutris, Proton-CachyOS, GameMode, MangoHud y Gamescope.
- **Instalador gráfico (Calamares)** con sistema de archivos Btrfs y compresión zstd.
- **AUR y Flatpak:** `paru` y `flatpak` preinstalados.

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
