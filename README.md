# discargar

Descarga vídeo y audio de la web pegando un enlace. Sin anuncios, sin páginas
intermedias, sin cuentas ni telemetría: todo el tráfico va directo de tu
conexión al servidor de origen.

Este repositorio contiene la versión Linux. Existe un repositorio hermano para
Windows con la misma lógica común.

## Estado

En construcción. Por ahora solo existe el gestor del motor de descarga
(`src/discargar/engine/`): la parte que descarga, verifica y actualiza la
copia privada de [yt-dlp](https://github.com/yt-dlp/yt-dlp) y del runtime
[deno](https://github.com/denoland/deno) que usa la app, y que invoca las
descargas leyendo su progreso. Todavía no hay ventana ni instalador.

## Licencia

GPL-3.0-or-later. Ver [LICENSE](LICENSE).
