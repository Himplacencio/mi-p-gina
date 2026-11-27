#!/usr/bin/env bash
# =============================================================
#  Construye la ISO de MoonOS.
#  Requisitos: Arch Linux (o el contenedor Docker archlinux) y root.
#  Uso:  sudo ./build.sh
#  Variables opcionales: WORK=/ruta/trabajo  OUT=/ruta/salida
# =============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${WORK:-/tmp/moonos-work}"
OUT="${OUT:-$HERE/out}"
PROFILE="$WORK/profile"
RELENG=/usr/share/archiso/configs/releng
CACHYOS_KEY="F3B607488DB35A47"

msg() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Ejecuta este script como root."
[[ -f /etc/arch-release ]] || die "Necesitas Arch Linux (o el contenedor Docker 'archlinux')."

msg "Configurando espejos e instalando archiso"
if ! grep -q '^Server' /etc/pacman.d/mirrorlist; then
    echo 'Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch' > /etc/pacman.d/mirrorlist
fi
pacman-key --init
pacman-key --populate archlinux
pacman -Sy --noconfirm archlinux-keyring
pacman -Su --noconfirm --needed archiso

msg "Importando la clave de firma de CachyOS"
pacman-key --recv-keys "$CACHYOS_KEY" --keyserver hkps://keyserver.ubuntu.com
pacman-key --lsign-key "$CACHYOS_KEY"

msg "Preparando el perfil (base: releng de archiso + MoonOS)"
rm -rf "$WORK"
mkdir -p "$PROFILE/airootfs/etc/mkinitcpio.conf.d" "$PROFILE/airootfs/etc/mkinitcpio.d" "$OUT"

# Menús de arranque oficiales de archiso
for d in efiboot syslinux grub; do
    if [[ -d "$RELENG/$d" ]]; then cp -a "$RELENG/$d" "$PROFILE/"; fi
done
# Configuración de initramfs del modo Live, adaptada al kernel de CachyOS
cp "$RELENG/airootfs/etc/mkinitcpio.conf.d/archiso.conf" "$PROFILE/airootfs/etc/mkinitcpio.conf.d/"
sed -e 's#vmlinuz-linux#vmlinuz-linux-cachyos#g' \
    -e 's#initramfs-linux#initramfs-linux-cachyos#g' \
    "$RELENG/airootfs/etc/mkinitcpio.d/linux.preset" \
    > "$PROFILE/airootfs/etc/mkinitcpio.d/linux-cachyos.preset"

# Archivos propios de MoonOS encima
cp -a "$HERE/profile/." "$PROFILE/"

# Usar los mismos modos de arranque que el releng de esta versión de archiso
releng_bootmodes="$(grep '^bootmodes=' "$RELENG/profiledef.sh")"
sed -i "s|^bootmodes=.*|${releng_bootmodes}|" "$PROFILE/profiledef.sh"
echo "Modos de arranque: $releng_bootmodes"

# Menús de arranque: kernel de CachyOS y nombre MoonOS
bootdirs=()
for d in efiboot syslinux grub; do if [[ -d "$PROFILE/$d" ]]; then bootdirs+=("$PROFILE/$d"); fi; done
find "${bootdirs[@]}" -type f \( -name '*.cfg' -o -name '*.conf' \) | while read -r f; do
    sed -i -e 's#/vmlinuz-linux\b#/vmlinuz-linux-cachyos#g' \
           -e 's#/initramfs-linux\.img#/initramfs-linux-cachyos.img#g' \
           -e 's#Arch Linux install medium#MoonOS Live#g' \
           -e 's#Arch Linux#MoonOS#g' "$f"
done
if grep -rnE 'vmlinuz-linux([^-]|$)|initramfs-linux\.img' "${bootdirs[@]}"; then
    die "Quedaron referencias al kernel 'linux' sin cambiar (ver arriba)."
fi

msg "Construyendo la ISO (esto tarda bastante)"
mkarchiso -v -w "$WORK/build" -o "$OUT" "$PROFILE"

cd "$OUT"
for iso in *.iso; do sha256sum "$iso" > "$iso.sha256"; done
msg "¡Listo! ISO en: $OUT"
ls -lh "$OUT"
