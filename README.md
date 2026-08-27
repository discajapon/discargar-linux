# discargar

Descarga vídeo y audio de la web pegando un enlace. Sin anuncios, sin páginas
intermedias, sin cuentas ni telemetría: todo el tráfico va directo de tu
conexión al servidor de origen. No hay backend propio.

Este repositorio contiene la versión Linux. Existe un repositorio hermano
para Windows con la misma lógica común (ver [Sincronización con el
repositorio de Windows](#sincronización-con-el-repositorio-de-windows)).

## Cómo funciona

El motor de descarga es [yt-dlp](https://github.com/yt-dlp/yt-dlp). discargar
gestiona su propia copia privada en tu directorio de datos de usuario (no
usa ni modifica el yt-dlp del sistema si tuvieras uno), la mantiene
actualizada sola, y la invoca para descargar siempre a la mejor calidad
disponible, fusionando vídeo y audio con `ffmpeg` en un `.mp4` que se guarda
en tu carpeta de descargas. Desde la versión 2025.11.12 yt-dlp necesita
además un runtime de JavaScript externo para YouTube; discargar gestiona
igual de forma privada una copia de [deno](https://github.com/denoland/deno)
para eso.

## Instalación

### Nativa (venv aislado)

```sh
git clone https://github.com/discajapon/discargar-linux.git
cd discargar-linux
./scripts/install.sh
```

Esto crea un entorno virtual en `~/.local/share/discargar/venv` (nunca toca
el Python del sistema, así que funciona igual en distribuciones con PEP 668
como Debian/Ubuntu recientes), enlaza el lanzador en `~/.local/bin/discargar`,
e instala el icono y la entrada de menú. "Discargar" debería aparecer en el
buscador de aplicaciones.

Para desinstalar:

```sh
./scripts/uninstall.sh          # conserva el tema, los logs y el motor descargado
./scripts/uninstall.sh --purge  # borra también esos datos
```

### Flatpak

Manifiesto en [`packaging/flatpak/com.discajapon.Discargar.yml`](packaging/flatpak/com.discajapon.Discargar.yml).
Build local:

```sh
flatpak-builder --user --install --force-clean build \
    packaging/flatpak/com.discajapon.Discargar.yml
flatpak run com.discajapon.Discargar
```

### Dependencias del sistema

- Python 3.11 o más nuevo, con el módulo `venv` (en Debian/Ubuntu es el
  paquete aparte `python3-venv`) — solo para la instalación nativa.
- `ffmpeg`, instalado con el gestor de paquetes de tu distribución. discargar
  lo detecta y te avisa con claridad si falta.

yt-dlp y deno **no** son dependencias del sistema: discargar los gestiona
solo, en privado, en su propio directorio de datos.

## Editar el tema

Todo el aspecto visual (colores del degradado, opacidad y refracción del
cristal, tipografía, duración de las transiciones, etc.) vive en un archivo
de texto legible:

```
~/.config/discargar/theme.toml
```

Se crea con valores por defecto en el primer arranque. Edítalo con la app
abierta: los cambios se aplican al momento, sin reiniciar. Un valor
inválido o fuera de rango se ignora (queda registrado en el log de
`~/.local/state/discargar/discargar.log`) y se usa el valor por defecto de
esa clave concreta, sin afectar al resto del archivo.

Ahí mismo se elige el canal de actualización del motor
(`[engine] channel = "nightly"` o `"stable"`).

## Uso responsable

Descarga solo contenido que sea tuyo, que tenga una licencia libre, o que su
titular permita copiar. discargar es una herramienta; el uso que le des es
tu responsabilidad.

## Sincronización con el repositorio de Windows

Existe un repositorio hermano para Windows con la misma lógica común. Un
workflow ([`.github/workflows/sync-windows.yml`](.github/workflows/sync-windows.yml))
sincroniza automáticamente hacia ese repositorio, abriendo un *pull request*
ahí (nunca empuja directo a su rama principal) cada vez que cambia algo en:

- `src/discargar/engine/` — motor completo (instalación/actualización de
  yt-dlp y deno, invocación de descargas, progreso, errores).
- `src/discargar/ui/` — interfaz, **excepto** `ui/motion.py`: la detección
  de "reducir movimiento" en Linux usa el portal de escritorio de
  Linux/Flatpak; Windows implementa su propio equivalente con la misma
  interfaz pública (`ReducedMotion.active`), así que no se sobrescribe.
- `src/discargar/app.py` y `src/discargar/log.py`.

Explícitamente **fuera** de la sincronización, por ser específico de Linux:
`src/discargar/paths.py` (rutas XDG — Windows resuelve sus propias rutas con
la misma interfaz), todo lo de `scripts/`, `packaging/`, `data/icons/`,
`src/discargar/licenses/`, `pyproject.toml` y `LICENSE`.

Para activarlo hacen falta, en la configuración del repositorio:

- La variable de repositorio `WINDOWS_REPO` (`owner/nombre-del-repo`).
- El secreto `WINDOWS_REPO_TOKEN`: un token con permiso de escritura sobre
  ese repositorio.

Mientras no estén configurados, el workflow no hace nada (falla su propia
comprobación inicial con un mensaje claro, no se queda a medias).

## Licencia

GPL-3.0-or-later. Ver [LICENSE](LICENSE). Créditos y licencias de terceros
(PySide6/Qt, yt-dlp, deno) accesibles desde los ajustes de la propia app, y
en [`src/discargar/licenses/`](src/discargar/licenses/).
