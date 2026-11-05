# Vídeo explicativo: ¿Cómo funciona la fotosíntesis?

Vídeo animado (1920x1080, 30 fps, ~1 min 37 s, con música) generado **100 % por código**.

▶️ Vídeo: [`fotosintesis.mp4`](fotosintesis.mp4)

## Escenas
1. **Título**: sale el sol y crece la planta.
2. **Los 3 ingredientes**: luz solar, agua (H₂O) que sube desde las raíces y CO₂ que entra por los estomas.
3. **Dentro de la hoja**: zoom a las células y sus cloroplastos.
4. **El cloroplasto**: membrana, tilacoides (con clorofila) y estroma.
5. **Fase 1 · Fase luminosa**: la luz rompe el agua → se libera O₂ y se fabrican ATP y NADPH.
6. **Fase 2 · Ciclo de Calvin**: el CO₂ y la energía producen glucosa.
7. **Los resultados**: el oxígeno sale al aire y la glucosa alimenta a la planta (que crece y florece).
8. **La ecuación**: 6 CO₂ + 6 H₂O + luz → C₆H₁₂O₆ + 6 O₂.
9. **Cierre**.

## Cómo regenerarlo
Requisitos: Python 3, Pillow, NumPy y FFmpeg.

```bash
python3 generar_video.py                  # crea fotosintesis.mp4
python3 generar_video.py --preview 12 45  # guarda solo esos segundos como PNG
```

Los textos, tiempos y colores están en `generar_video.py`: cada escena es una función
`sc_*` y la lista `SCENES` define su orden y duración.

---

# Versión vertical (estilo historia): «Imagina que eres una planta»

▶️ Vídeo: [`fotosintesis_vertical.mp4`](fotosintesis_vertical.mp4) (1080x1920, 9:16, ~81 s)

Formato para TikTok/Reels/Shorts: narración en segunda persona, personaje maniquí con
sombreado 3D (con un brote en la cabeza), cortes rápidos cada 1–3 s, subtítulos grandes
palabra a palabra (palabras clave en amarillo), viñeteado, grano de película, música
ambiental que cambia según la escena y efectos de sonido.

Guion: la planta tiene hambre → amanece → «tu superpoder: la fotosíntesis» → receta secreta
(luz, agua, CO₂) → raíces, estomas → viaje dentro del cloroplasto → fase luminosa → ciclo de
Calvin → glucosa → «algo respira justo detrás de ti»… es un humano que respira tu oxígeno →
la ecuación → pregunta final para comentar (1 o 2).

```bash
python3 generar_video_vertical.py                 # crea fotosintesis_vertical.mp4
python3 generar_video_vertical.py --preview 3 20  # guarda esos segundos como PNG
```

El guion está en la lista `SHOTS`: cada plano tiene su escena, parámetros de cámara,
subtítulos con duración, efectos de sonido y ambiente musical.
