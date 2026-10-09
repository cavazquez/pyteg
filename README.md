# Pyteg

Juego de estrategia por turnos en Python.

## 🧰 Herramientas y tecnologías

![CI Ruff y unittest](https://github.com/cavazquez/pyteg/actions/workflows/ruff-uv.yml/badge.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![🐍 Python](https://img.shields.io/badge/🐍_Python-3.14-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![📐 mypy](https://img.shields.io/badge/📐_mypy-tipos_estrictos-2C5282?style=flat)](https://github.com/python/mypy)
[![🧪 unittest](https://img.shields.io/badge/🧪_unittest-suite_tests-0F9D58?style=flat)](https://docs.python.org/3/library/unittest.html)

[![📊 coverage](https://img.shields.io/badge/📊_coverage-ramas-00796B?style=flat)](https://coverage.readthedocs.io/)
[![🖥️ PySide6](https://img.shields.io/badge/🖥️_PySide6-Qt_6-41CD52?style=flat&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![🔌 TCP](https://img.shields.io/badge/🔌_TCP-LAN_cliente_servidor-E65100?style=flat)](docs/ARCHITECTURE.md#seguridad-y-modelo-de-amenaza)
[![🥚 Hatch](https://img.shields.io/badge/🥚_Hatch-build_paquetes-3775A9?style=flat)](https://github.com/pypa/hatch)
[![⚙️ Nuitka](https://img.shields.io/badge/⚙️_Nuitka-binario_onefile-303030?style=flat)](https://nuitka.net/)

[![🐳 Docker](https://img.shields.io/badge/🐳_Docker-opcional-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![🌍 gettext](https://img.shields.io/badge/🌍_gettext-es_y_en-2980B9?style=flat)](https://www.gnu.org/software/gettext/)
[![🔄 GitHub Actions](https://img.shields.io/badge/🔄_GitHub_Actions-CI-2088FF?style=flat&logo=githubactions&logoColor=white)](https://github.com/cavazquez/pyteg/actions)
[![📜 Licencia](https://img.shields.io/badge/📜_Licencia-GPL--3.0-2980B9?style=flat)](LICENSE)

Organización modular del **cliente GUI** (toolbar, mapa/país, internacionalización): ver la tabla en [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md#toolbar-y-país-en-el-mapa-descomposición).

## ¿Qué es Pyteg?
Pyteg es un juego de estrategia por turnos en el que
los jugadores conquistan países, atacan con dados y cumplen objetivos.
Este proyecto implementa una versión cliente-servidor con interfaz
gráfica en Python.

## Características clave
- Cliente gráfico con 🖥️ PySide6 y animación de dados en las batallas
- Inicio común para jugar localmente con bots, en LAN o por archivos; acceso a partidas recientes.
- **Efectos visuales inmersivos**: Atacante ve animación completa, espectadores ven titilación de países y pérdidas flotantes
- **Sistema de sonidos**: Efectos de audio para batallas, movimientos, turnos y eventos del juego con controles de volumen
- Modo multijugador con servidor 🔌 TCP y validación de estados (sin cifrado; pensado para redes de confianza, p. ej. LAN). Detalle del modelo de amenaza: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#seguridad-y-modelo-de-amenaza) y [ADR-009](docs/DECISIONS.md#adr-009-tcp-sin-cifrado-y-red-de-confianza).
- Crear una partida desde el cliente y recuperar automáticamente el anfitrión en otro jugador si se cae.
- Descubrir salas en la LAN, guardar/reabrir partidas y revisar su historial.
- Jugar sin conexión mediante archivos de turno compartidos por cualquier medio.
- Restricción de ataques en los dos primeros turnos
- Elección de cantidad de unidades para atacar (1 a 3)
- Validación de nombres de usuario duplicados (con desconexión)
- Estado del juego visible en la barra de estado (ronda, turno, color)
- Bloqueo de nuevas conexiones cuando la partida está en curso
- **Condición de victoria configurable**: Por defecto 30 países (`DEFAULT_VICTORY_COUNTRIES` en `pyteg/config.py`; configurable al crear partida)
- **Objetivos secretos**: Sistema opcional de objetivos secretos del mapa clásico
- **Ventana de configuración**: Muestra duración de turno, objetivo de países y objetivos secretos
- **Verificación automática de condición de victoria al final de cada ronda**
- **Soporte multiidioma 🌍 (i18n)**: Español e inglés con selector en la interfaz
- Suite 🧪 `unittest`, 🪶 Ruff, 📐 mypy estricto y 📊 cobertura en CI y en `./run_tests.sh`

## Requisitos
- 🐍 Python 3.14 (se aceptan actualizaciones de parche dentro de la serie 3.14)
- ⚡ [UV](https://github.com/astral-sh/uv) para dependencias

La versión local está fijada en [`.python-version`](.python-version). Después de
instalar uv, `uv sync --group dev` instalará o seleccionará Python 3.14.
- 🐳 Docker (opcional)

## ⚡ Instalación rápida
```bash
git clone https://github.com/cavazquez/pyteg.git
cd pyteg
uv sync
```

## Jugar en red local desde el cliente

1. Ejecutá `uv run pyteg-client`, elegí **LAN** en el inicio y continuá.
2. Elegí **Crear partida**, tu nombre, mapa, perfil de reglas y puerto. La
   ventana muestra las direcciones locales que podés compartir.
3. Los demás jugadores eligen **Unirme a una partida** y seleccionan la sala
   en **Salas en la red**. El cliente completa dirección, puerto y mapa.
   También se puede ingresar la dirección manualmente.
4. El administrador configura las reglas y comienza la partida. El mapa y el
   perfil de reglas siguen siendo elecciones independientes.

Si se cierra o cae el anfitrión, los clientes intentan reconectarse y luego
recuperan el motor en otro participante por orden de ingreso. La partida se
pausa durante las reconexiones y reserva ocho segundos para que vuelvan los
jugadores. Se conservan países, unidades, misiles, cartas, objetivos, turnos y
el tiempo pendiente del jugador que sigue en turno. La barra de estado indica
**Anfitrión**, **Conectado** o **Recuperando partida…**; su tooltip muestra el
destino actual y las direcciones para unirse.

Las acciones se confirman después de guardar la transición en una mayoría de
participantes. Si falta esa mayoría, se pausan acciones y reloj. La elección de
un sucesor también requiere mayoría y conserva los votos en disco para evitar
que un reinicio permita votar por dos candidatos en la misma época. Con cuatro
participantes, perder dos al mismo tiempo deja la partida esperando; no crea dos
partidas independientes. Los cambios de participantes requieren mayorías tanto
del grupo anterior como del nuevo.

Cada cliente habilitado conserva una copia completa y privada del motor en
disco. Usá esta modalidad con participantes y red de confianza: esas copias
incluyen cartas, objetivos y credenciales. Los equipos deben poder conectarse
entre sí a los puertos TCP del juego y de recuperación (asignado automáticamente).
El descubrimiento utiliza UDP 45471, multicast local y broadcast. Si la red
bloquea esos anuncios, se puede usar la dirección manual.

### Inicio y partidas locales con bots

Al abrir el cliente aparece **Jugar Pyteg**. También podés volver con
**Partida → Nueva partida…** (`Ctrl+N`) o con el botón **Jugar**.

- **Local**: elegí tu nombre y entre 0 y 7 bots de dificultad básica. El valor
  inicial es un humano contra tres bots; cero bots permite jugar solo.
- **LAN**: continuá para crear una sala o unirte a una descubierta en tu red.
- **Por archivos**: escribí los nombres de los participantes; cada uno juega
  su turno en su propia copia sin un reloj de turno.

El **mapa** y el **perfil de reglas** se eligen por separado: por ejemplo,
mapa Clásico con reglas Revancha. Después, el administrador puede personalizar
mecánicas, objetivos y cartas individuales desde la configuración existente.
En modo local, la duración predeterminada sigue siendo 20 segundos; el
administrador puede cambiarla antes de empezar.

Los bots colocan refuerzos, usan cartas y misiles y atacan con ventaja usando
sus propios eventos del protocolo. Juegan desde la interfaz a un ritmo visible.
Los guardados conservan los bots y sus decisiones pendientes para retomar una
partida interrumpida. La dificultad disponible es básica.

La pantalla de inicio ofrece **partidas y archivos recientes**, incluidos los
autoguardados. Para abrir un documento también podés arrastrar un `.pyteg`,
`.pyturn` o `.pyreplay` sobre la ventana principal, usar `Ctrl+O`, o iniciar
`pyteg-client --open /ruta/al/archivo.pyteg`.

### Guardar y reabrir partidas

- **Partida → Guardar partida…** (`Ctrl+S`) exporta un archivo `.pyteg`.
- **Partida → Abrir partida o turno…** (`Ctrl+O`) abre un guardado, incluso
  después de cerrar todos los clientes. El mapa, las reglas y el modo se
  recuperan del archivo. Una partida local retoma sus bots; una partida LAN
  crea otra sala para poder retomar esa copia.
- Los demás jugadores eligen la nueva sala y **Recuperar mi jugador desde un
  guardado…**, usando su propio archivo. El reloj espera a que vuelvan todos;
  el anfitrión puede usar **Reanudar partida guardada** para continuar antes.
- Los autoguardados se conservan en el directorio de datos del usuario,
  `pyteg/autosaves` (normalmente `~/.local/share/pyteg/autosaves` en Linux).
  El diálogo de apertura comienza en ese directorio. Se conservan autoguardados
  distintos por sala y jugador.

### Jugar por archivos, sin servidor central

1. Elegí **Por archivos** en el inicio, mapa, perfil de reglas y nombres
   de 1 a 8 jugadores. El primer jugador administra la configuración de reglas,
   objetivos y situaciones usando los mismos controles que en red.
2. Iniciá la partida y jugá tu turno. Este modo no tiene límite de tiempo.
3. Al finalizar, usá **Partida → Exportar turno…** y compartí el `.pyturn`
   con el jugador al que le toca. El archivo incluye el destinatario.
4. Ese jugador abre el archivo con `Ctrl+O` o lo arrastra a la ventana. Antes
   de importar ve autor, destinatario, ronda, países controlados y los cambios
   respecto de su copia. Puede cancelar sin modificar la partida. Después
   juega y exporta la continuación.
   Cuando vuelve a tocarte, abrí el nuevo archivo en tu copia anterior.

Al exportar aparece la ruta del archivo y botones para **Copiar ruta** o
**Abrir carpeta**. También queda disponible **Partida → Abrir carpeta de
exportaciones**. El archivo se comparte manualmente por el medio elegido.

El trabajo local se autoguarda. Exportar repetidamente produce la misma entrega;
el cliente reconoce archivos duplicados, atrasados, dirigidos a otro jugador
o pertenecientes a una rama distinta. Los archivos contienen estado privado:
esta modalidad también está pensada para participantes de confianza.

### Historial y repetición

**Partida → Historial y repetición…** abre otro mapa de sólo lectura, con
navegación por acción o turno y reproducción automática. No modifica la partida.
**Exportar repetición…** genera un `.pyreplay` que se puede abrir desde el mismo
menú. Incluye estados públicos y resultados de combate; omite credenciales,
cartas privadas y objetivos secretos asignados.

## Ejecutar con servidor independiente

También se conserva la modalidad de servidor separado:
- Con entry points instalados (recomendado):
  ```bash
  # Instala el paquete y scripts
  uv sync

  # Servidor
  uv run pyteg-server

  # Cliente
  uv run pyteg-client
  ```

- Terminal 1 (servidor):
```bash
uv run pyteg-server
```

- Terminal 2..8 (clientes):
```bash
uv run pyteg-client
```

Consejos:
- Para esta modalidad, primero inicia el servidor. Luego abre uno o más clientes
  y elegí **Unirme a una partida**.
- Si el juego ya está en curso, el servidor rechazará nuevas conexiones.

### Elegir Clásico o Revancha

El servidor define el tema de la partida. Para jugar **Clásico**, iniciá
`uv run pyteg-server --theme classic` (es el valor predeterminado). Para jugar
**Revancha**, iniciá `uv run pyteg-server --theme revancha`.

En cada cliente elegí el mismo tema en el diálogo **Conectar** antes de entrar
a la sala. También podés abrir el cliente con `uv run pyteg-client --theme classic`
o `uv run pyteg-client --theme revancha` para dejar esa opción seleccionada de
entrada. El cliente comprueba que el tema y el mapa coincidan con el servidor;
si elegís otro tema, la conexión se rechaza.

Para ejecutar automáticamente un servidor y varios bots por TCP hasta verificar
una victoria, consultá [la guía de simulación](docs/SIMULATION.md). El diagnóstico,
las prioridades y los issues para completar el proyecto están en
[la revisión técnica](docs/PROJECT_REVIEW.md).

## Build de binarios (⚙️ Nuitka)
Requiere dependencias de desarrollo:
```bash
uv sync --group dev
```

Compilar binarios (modo onefile + standalone) para servidor y cliente:
```bash
# ⚙️ Nuitka; las entradas y los recursos se validan antes de compilar
uv run python scripts/build_binaries.py --version 0.2.3
```

Los ejecutables quedarán en `dist/`.

Build de wheel/sdist (empaquetado Python estándar):
```bash
# wheel / sdist
uv build --wheel --sdist
uv run python scripts/verify_wheel.py dist/pyteg-*.whl
uv run python scripts/verify_sdist.py dist/pyteg-*.tar.gz
uv run python scripts/smoke_wheel.py dist/pyteg-*.whl
```

Los verificadores exigen recursos de `classic`, `test` y `revancha`. El smoke
arranca el servidor extraído con ambos temas, por lo que no depende del
checkout. El workflow de release también ejecuta `scripts/smoke_binaries.py`
sobre los ejecutables Nuitka antes de archivarlos.

## Estructura del proyecto
- `pyteg/`: Código fuente principal
- `tests/`: Tests unitarios
- `themes/`: Temas visuales y mapas
  - `classic/`: Tema clásico con mapa mundial completo (50 países)
    - `paises.toml`: Configuración de países y continentes
    - `cartas.toml`: Configuración de cartas del juego
    - `*.png`: Archivos de imagen de países y cartas
  - `test/`: Tema de prueba con mapa reducido (6 países)
  - `revancha/`: Tema Revancha con mapa de 72 países, cartas y reglas propias
- `locales/`: Archivos de traducción (español/inglés)
- `docs/`: Documentación técnica
- `ejecutar_docker.sh`: entorno en Docker (opcional)

### Estructura de archivos de configuración

El juego utiliza archivos TOML para la configuración:

- `themes/classic/paises.toml`: Configuración de países, continentes y sus propiedades visuales
- `themes/classic/cartas.toml`: Configuración de cartas del juego (separado desde v1.x)
- `themes/classic/adyacencias.toml`: Configuración de adyacencias entre países y conexiones visuales opcionales (separado desde v1.x)
- `themes/classic/objetivos_secretos.toml`: Configuración de objetivos secretos del mapa clásico

Las conexiones visuales se declaran con tablas `[[ConexionesVisuales]]` y los
campos `origen`, `destino` y `puntos`. Se dibujan detrás de los países; no
modifican las adyacencias que usa el servidor para validar ataques y
movimientos.

### Arquitectura modular de la GUI
La interfaz vive en el paquete **`pyteg/gui/`** (subdominios: `managers/`, `widgets/`, `dialogs/`, `windows/`, `mapa/`, `toolbar/`, `tarjetas/`, `status_bar/`):

- **`pyteg/gui/main_window.py`**: clase `Gui` (ventana principal) y coordinación de gestores
- **`pyteg/gui/managers/layout.py`**, **`theme.py`**, **`players.py`**, **`status.py`**, **`units.py`**, **`game_actions.py`**, etc.: gestores especializados

El código histórico importaba módulos planos `pyteg/gui_*`; esos shims se eliminaron: usar siempre rutas bajo `pyteg.gui.<dominio>`.

## Desarrollo
Formateo y estilo:
- Límite de línea: 88 caracteres (en todo el proyecto)
- 🪶 Ruff para lint y formato

Comandos útiles (tras `uv sync --group dev`; detalle en `docs/CONTRIBUTING.md`):
```bash
# 🪶 Lint / formato · 📐 mypy · 🧪 tests (versiones fijadas en el proyecto)
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run coverage run --branch -m unittest discover
uv run coverage report -m

# Todo en una pasada (incluye auto-fix de Ruff y compilación gettext → .mo)
./run_tests.sh
```

## Logs y retención
Los logs se guardan en `logs/` con rotación automática y limpieza periódica. Puedes ajustar límites mediante variables de entorno (tamaño por archivo, cantidad de backups, tamaño total, días de retención y cantidad de logs de cliente). Consulta la sección correspondiente en `docs/CONTRIBUTING.md` para ver los nombres de variables y ejemplos.

## 🐳 Docker (opcional)
Puedes levantar un entorno de desarrollo con:
```bash
./ejecutar_docker.sh
```

## 🌍 Soporte multiidioma (i18n)

PyTeg incluye soporte completo para múltiples idiomas usando gettext:

### Idiomas soportados
- **Español** (es) - Idioma por defecto
- **English** (en) - Inglés

### Cambiar idioma
- El idioma se detecta automáticamente del sistema al iniciar
- Usa el selector de idioma en la barra de estado de la interfaz
- Los cambios se aplican inmediatamente

### Para desarrolladores

Los archivos **`.mo` no van al repositorio** (están en `.gitignore`): son binarios generados a partir de los `.po`. Sin ellos, el idioma **inglés** puede no cargar correctamente hasta compilar.

- Tras un **`git pull`** que cambie `locales/`, compilá una vez:
  ```bash
  uv run python scripts/manage_translations.py compile
  ```
  (equivalente: `python3 scripts/manage_translations.py compile` si no usás `uv`.)
- **`./run_tests.sh`** ejecuta al inicio ese mismo `compile`, así que correr la suite completa deja los catálogos actualizados en tu máquina.
- En **CI** (GitHub Actions) también se compilan los catálogos antes de los tests.

```bash
# Extraer strings para traducir
python3 scripts/manage_translations.py extract

# Compilar traducciones (.po → .mo)
python3 scripts/manage_translations.py compile

# Ejecutar todas las tareas de traducción
python3 scripts/manage_translations.py all
```

Para marcar texto como traducible en el código:
```python
from pyteg.i18n import _

# Texto simple
label = QLabel(_("Texto a traducir"))

# Texto con formato
message = _("Jugador {} ganó").format(player_name)
```

## Documentación y diagramas
 - Documentación central:
   - Arquitectura: `docs/ARCHITECTURE.md`
   - Decisiones (ADR): `docs/DECISIONS.md`
   - Guía de contribución: `docs/CONTRIBUTING.md`
   - Cambios: `docs/CHANGELOG.md`
 - Protocolos y mensajes:
   - `docs/como_crear_mensaje_cliente_a_servidor.md`
   - `docs/como_crear_mensaje_servidor_a_cliente.md`
   - `docs/como_crear_mensaje_bidireccional.md`
 - Diagramas y notas en `docs/diagrams/`
 - El código incluye docstrings y type hints en módulos clave

## Releases y Binarios

### Descargar binarios compilados
Los binarios compilados para múltiples plataformas están disponibles en la [página de releases](https://github.com/cavazquez/pyteg/releases):

- **Linux x86_64**: `pyteg-<version>-linux-x86_64.tar.gz`
- **Windows x86_64**: `pyteg-<version>-windows-x86_64.zip`
- **macOS x86_64**: `pyteg-<version>-macos-x86_64.tar.gz`
- **macOS ARM64**: `pyteg-<version>-macos-arm64.tar.gz`

Los binarios son standalone (no requieren Python instalado) e incluyen todos los assets necesarios.
Los nombres usan la versión sin el prefijo `v` del tag, por ejemplo
`pyteg-0.2.3-linux-x86_64.tar.gz` para `v0.2.3`.

### Crear un nuevo release
Para crear un nuevo release con binarios compilados:

1. **Actualizar la versión** en `pyproject.toml`:
   ```toml
   [project]
   version = "1.0.0"  # Nueva versión
   ```

2. **Actualizar el CHANGELOG** en `docs/CHANGELOG.md` con los cambios de la nueva versión.

3. **Crear y pushear el tag**:
   ```bash
   git add pyproject.toml uv.lock docs/CHANGELOG.md
   uv lock
   git commit -m "release: 0.2.3"
   git tag v0.2.3
   git push origin master
   git push origin v0.2.3
   ```

4. **🔄 GitHub Actions automáticamente**:
   - Construirá binarios para todas las plataformas
   - Ejecutará los tests en cada plataforma
   - Creará un **borrador de release sin publicar** con los binarios adjuntos
   - Generará archivos comprimidos para cada plataforma

5. **Publicar el release manualmente**:
   - Ve a la [página de releases](https://github.com/cavazquez/pyteg/releases) en GitHub
   - Encontrarás un borrador con todos los binarios adjuntos
   - Revisa los binarios y la descripción del release
   - Haz clic en **"Publish release"** para hacerlo público

El workflow se ejecuta solo cuando se pushea un tag que comience con `v` (ej: `v1.0.0`, `v2.1.3`).

## Contribuir
¡Contribuciones son bienvenidas! Por favor, crea un issue o pull request para sugerir mejoras o reportar problemas.
