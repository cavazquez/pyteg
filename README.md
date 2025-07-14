![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff-uv.yml/badge.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# Pyteg

Implementación del juego Teg en Python

## ¿Qué es Teg?
Teg es un juego de mesa tradicional argentino para dos jugadores. Se juega en un tablero de 8x8 casillas y cada jugador tiene 12 fichas. El objetivo es capturar las fichas del oponente o bloquear sus movimientos.

## Requisitos
- Python 3.8 o superior
- Docker (opcional para el entorno de desarrollo)

## Instalación de UV

Este proyecto utiliza [UV](https://github.com/astral-sh/uv) para la gestión de dependencias y herramientas.  
Puedes consultar las instrucciones de instalación oficiales en:  
https://github.com/astral-sh/uv#installation

## Instalación
1. Clona el repositorio:
```bash
git clone https://github.com/cavazquez/pyteg.git
cd pyteg
```

2. Instala las dependencias:
```bash
uv sync
```



## Estructura del Proyecto
El proyecto está organizado de la siguiente manera:
- `src/`: Contiene el código fuente principal
- `tests/`: Contiene los tests unitarios
- [ejecutar_docker.sh](cci:7://file:///home/cristian/repos/propios/pyteg/ejecutar_docker.sh:0:0-0:0): Script para ejecutar el entorno Docker
- [run_test.sh](cci:7://file:///home/cristian/repos/propios/pyteg/run_test.sh:0:0-0:0): Script para ejecutar pruebas y linting

## Desarrollo

### Configuración del Entorno
Para configurar el entorno de desarrollo:
```bash
uv sync
```

### Entorno Docker (Opcional)
Para levantar el entorno en Docker:
```bash
./ejecutar_docker.sh
```

### Pruebas y Linting
Para ejecutar todas las pruebas y el linting:
```bash
./run_test.sh
```

#### Ejecutar pruebas individuales
- Solo el linter:
```bash
uvx ruff check .
```

- Solo el formateador:
```bash
uvx ruff format --check .
```

- Solo los tests con coverage:
```bash
uvx coverage run --branch -m unittest
```

- Ver el reporte de coverage:
```bash
uvx coverage report -m
```

## Mejoras Recientes

### Interfaz de Usuario Mejorada
- **Visualización de Unidades Disponibles**: Las unidades disponibles ahora se muestran automáticamente al inicio de cada turno y se actualizan en tiempo real
- **Estilo Visual Mejorado**: 
  - 🪖 **Unidades Generales**: Verde con fondo destacado cuando hay unidades disponibles
  - 🌍 **Unidades de Continentes**: Azul con fondo destacado para continentes con bonificación
  - 🚀 **Misiles**: Rojo con estilo distintivo (cuando estén disponibles)
  - Bordes coloreados y fondos sutiles para mejor visibilidad

### Funcionalidades
- **Actualización Automática**: Las unidades disponibles se actualizan automáticamente después de agregar unidades al mapa
- **Feedback Visual**: Colores y iconos distintivos para diferentes tipos de unidades
- **Soporte para Continentes**: Muestra unidades bonus por control de continentes

### Documentación
- Diagramas de secuencia actualizados en `docs/diagrams/`
- Documentación del flujo de agregar unidades
- Especificaciones de estilo visual

## Contribuir
¡Contribuciones son bienvenidas! Por favor, crea un issue o pull request para sugerir mejoras o reportar problemas.

