# Vídeo: ¿Qué hace el procesador de un celular o computador?

▶️ Vídeo: [`procesador.mp4`](procesador.mp4) (vertical 1080x1920, ~93 s, con música y efectos)

Pensado para niños (y especialmente para niños con TDAH):
- **Una idea por pantalla** y cambios de imagen cada 1–3 segundos.
- **Marcador «PARTE X DE 7»** con puntos de progreso, para saber siempre dónde vamos.
- **Comparaciones cotidianas**: cerebro, trabajadores, bolsillo, mesa, mochila, pintor.
- Colores vivos, subtítulos cortos con palabras clave en amarillo, música alegre.
- **Resumen** al final y una **pregunta** para comentar.

## Partes
0. Intro: tu celular tiene un cerebro → el procesador (CPU), más pequeño que una galleta.
1. ¿Qué hace?: da las órdenes (pantalla, cámara, música, juegos). Tocas la cámara → piensa → se abre.
2. Interruptores: miles de millones; encendido = 1, apagado = 0.
3. Núcleos: cada núcleo es un trabajador; más núcleos = más cosas a la vez.
4. El reloj: marca el ritmo; 3.000 millones de tics por segundo = 3 GHz.
5. Memoria: caché (bolsillo), RAM (mesa), almacenamiento (mochila).
6. El GPU: el pintor; pinta la pantalla 60 veces por segundo.
7. Calor: tanto trabajo calienta; los ventiladores lo enfrían.

## Generarlo
```bash
python3 generar_video_procesador.py                 # crea procesador.mp4
python3 generar_video_procesador.py --preview 5 30  # guarda esos segundos como PNG
```
Usa el motor de `../video-fotosintesis/generar_video_vertical.py`.

## Añadir voz en off
Graba este guion, guárdalo como `voz.mp3` en esta carpeta y vuelve a generar el vídeo:
los cortes y subtítulos se sincronizan solos con tu voz.

> ¿Sabías que tu celular tiene un cerebro? ¡Mira adentro! ¡Aquí está!
> Se llama procesador. O CPU. Es más pequeño que una galleta, ¡pero súper listo!
> ¿Qué hace? Da todas las órdenes: pantalla, cámara, música, juegos...
> Tocas la cámara... el CPU piensa... ¡y se abre!
> Por dentro tiene miles de millones de interruptores. Cada uno solo sabe dos cosas: encendido es uno, apagado es cero. ¡Con ceros y unos hace todo!
> Tiene núcleos. ¡Como ocho cuartitos! Cada núcleo es un trabajador que hace una tarea. Más trabajadores... ¡más cosas a la vez!
> Tiene un reloj que marca el ritmo: tic, tac, tic, tac. ¡Hace tic tres mil millones de veces por segundo! ¡Más rápido que un parpadeo!
> Para trabajar necesita memoria. Tres lugares: Caché: su bolsillo. Pequeña, pero ¡súper rápida! RAM: su mesa. Se borra al apagar. Almacenamiento: su mochila. Aquí viven tus fotos y juegos.
> Su amigo el GPU: ¡el pintor! Pinta la pantalla sesenta veces por segundo. Por eso los juegos se ven ¡tan suaves!
> Tanto trabajo da calor. Por eso tu celular se calienta. Las computadoras usan ventiladores para enfriarlo.
> Resumen. El procesador es el cerebro. Tiene interruptores de cero y uno. Sus núcleos son trabajadores. Su reloj marca el ritmo. Usa su bolsillo, su mesa y su mochila. El GPU es el pintor. Y mucho trabajo da calor.
> Pregunta: ¿quién pinta la pantalla? ¿Uno o dos? ¡Coméntalo!
