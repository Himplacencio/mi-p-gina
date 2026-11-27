# Video de TikTok de MoonOS (generado con código)

1. `node record.js` graba las 6 escenas (página web y demo) a 1080×1920 en cámara lenta x4.
   Con `ONLY=2-pagina node record.js` se repite una sola escena.
2. `python3 assemble.py` monta el video final con ffmpeg: acelera x4, añade transiciones y una pista de audio en silencio.

Requisitos: Node con Playwright (Chromium) y ffmpeg. En TikTok, añade un sonido en tendencia desde el editor de la app.

## Video 2: RAM en vivo (`moonos-ram-tiktok.mp4`)

1. Workflow «Grabar el arranque de MoonOS» con `modo=terminal` → `moonos/marketing/arranque-real/terminal.mp4`.
2. `python3 montar-terminal.py salida.mp4` → video vertical con zoom y textos.
3. La voz (`voz-ram.mp3`, ElevenLabs) se corta en sus pausas y cada frase se coloca donde
   ocurre en pantalla (p. ej. «y escribo fast fetch» en el segundo 8, mientras se escribe).

## Video 4: estilo cinematográfico (`moonos-cine.mp4`, 16:9)

Intro con una línea de neón que dibuja la órbita de la luna, títulos de sección sobre las
grabaciones reales y cierre «BETA · LLEGA EN 2027». Todo se dibuja en `cine.html` (canvas).

1. Sacar los cuadros de cada sección (30 fps, 4,6 s) de `arranque-real/*.mp4` a `cuadros/s1 … s9`
   (s3 es `web-capturas/bienvenida-inicio.png` como `still.png`); los segundos de inicio están
   en la lista `SECCIONES` de `cine.html`.
2. `node montar-cine.js cuadros ../moonos-cine.mp4` dibuja los 1515 cuadros y arma el video (sin audio:
   en TikTok se le pone un sonido).
