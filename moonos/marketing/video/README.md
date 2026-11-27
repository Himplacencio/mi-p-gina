# Video de TikTok de MoonOS (generado con código)

1. `node record.js` graba las 6 escenas (página web y demo) a 1080×1920 en cámara lenta x4.
   Con `ONLY=2-pagina node record.js` se repite una sola escena.
2. `python3 assemble.py` monta el video final con ffmpeg: acelera x4, añade transiciones y una pista de audio en silencio.

Requisitos: Node con Playwright (Chromium) y ffmpeg. En TikTok, añade un sonido en tendencia desde el editor de la app.
