#!/usr/bin/env bash
# shellcheck disable=SC2034
# Perfil de archiso para MoonOS.
# build.sh sustituye la línea "bootmodes" por la del perfil releng instalado,
# para que coincida siempre con la versión de archiso usada al compilar.

iso_name="moonos"
iso_label="MOONOS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="MoonOS <https://github.com/himplacencio/mi-p-gina>"
iso_application="MoonOS Live"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
# xz comprime más que zstd: la ISO pesa menos (objetivo: menos de 4 GB)
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/usr/local/bin/moonos-bienvenida"]="0:0:755"
  ["/usr/local/bin/moonos-branding"]="0:0:755"
  ["/usr/local/bin/moonos-demo-musica"]="0:0:755"
  ["/usr/local/bin/moonos-drivers"]="0:0:755"
  ["/usr/local/bin/moonos-firewall"]="0:0:755"
  ["/usr/local/bin/moonos-gamemode"]="0:0:755"
  ["/usr/local/bin/moonos-gamemode-config"]="0:0:755"
  ["/usr/local/bin/moonos-steam-gamemode"]="0:0:755"
  ["/usr/local/bin/moonos-install"]="0:0:755"
  ["/usr/local/bin/moonos-live-setup"]="0:0:755"
  ["/usr/local/bin/moonos-luna"]="0:0:755"
  ["/usr/lib/moonos-luna/piper/piper"]="0:0:755"
  ["/usr/local/bin/moonos-postinstall"]="0:0:755"
  ["/usr/local/bin/moonos-tienda"]="0:0:755"
  ["/usr/local/bin/moonos-user-setup"]="0:0:755"
)
