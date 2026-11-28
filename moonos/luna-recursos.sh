#!/usr/bin/env bash
# =============================================================
#  Descarga lo que necesita Luna (el asistente de voz de MoonOS)
#  y lo deja dentro del sistema que se va a construir.
#    - libvosk.so: reconocimiento de voz sin internet (de la rueda oficial de Vosk en PyPI)
#    - modelo pequeño de español de Vosk (~40 MB)
#    - Piper: convierte texto en voz, sin internet
#    - dos voces en español de Piper: Daniela (femenina) y Ald (masculina)
#  Si algo no se puede descargar, Luna igual funciona escribiendo y
#  hablando con la voz básica de espeak-ng; el aviso queda en el registro.
#  Uso: luna-recursos.sh <carpeta airootfs>
# =============================================================
set -uo pipefail
ROOT="${1:?falta la carpeta airootfs}"
LIB="$ROOT/usr/lib/moonos-luna"
DAT="$ROOT/usr/share/moonos/luna"
TMP="$(mktemp -d)"
mkdir -p "$LIB" "$DAT/voces"

aviso() { printf '\033[1;33mLuna: %s\033[0m\n' "$*"; }
bajar() {  # bajar <url> <destino> [sha256]
    local url="$1" dst="$2" sum="${3:-}" i
    for i in 1 2 3; do
        if curl -fsSL --retry 2 -o "$dst" "$url"; then
            if [[ -z "$sum" ]] || echo "$sum  $dst" | sha256sum -c --status; then return 0; fi
            aviso "la huella de $(basename "$dst") no coincide"
            return 1
        fi
        sleep 3
    done
    aviso "no se pudo descargar $url"; return 1
}

# 1) Reconocimiento de voz: libvosk.so (se usa directo con ctypes, sin dependencias de Python)
VOSK_WHL="https://files.pythonhosted.org/packages/fc/ca/83398cfcd557360a3d7b2d732aee1c5f6999f68618d1645f38d53e14c9ff/vosk-0.3.45-py3-none-manylinux_2_12_x86_64.manylinux2010_x86_64.whl"
if bajar "$VOSK_WHL" "$TMP/vosk.whl" 25e025093c4399d7278f543568ed8cc5460ac3a4bf48c23673ace1e25d26619f; then
    unzip -q -o -j "$TMP/vosk.whl" vosk/libvosk.so -d "$LIB" && echo "Luna: libvosk.so listo"
fi

# 2) Modelo de español para Vosk
if bajar "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip" "$TMP/modelo.zip"; then
    unzip -q -o "$TMP/modelo.zip" -d "$TMP/modelo" && rm -rf "$DAT/vosk-es" \
        && mv "$TMP"/modelo/vosk-model-small-es-* "$DAT/vosk-es" && echo "Luna: modelo de voz en español listo"
fi

# 3) Piper (texto a voz): binario con sus librerías y datos de pronunciación
if bajar "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz" "$TMP/piper.tgz"; then
    rm -rf "$LIB/piper" && tar -xzf "$TMP/piper.tgz" -C "$LIB" && echo "Luna: Piper listo"
fi

# 4) Voces en español
HF="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es"
for voz in "es_AR/daniela/high/es_AR-daniela-high" "es_MX/ald/medium/es_MX-ald-medium"; do
    nombre="$(basename "$voz")"
    bajar "$HF/$voz.onnx" "$DAT/voces/$nombre.onnx" && bajar "$HF/$voz.onnx.json" "$DAT/voces/$nombre.onnx.json" \
        && echo "Luna: voz $nombre lista"
done

rm -rf "$TMP"
du -sh "$LIB" "$DAT" 2>/dev/null || true
exit 0
