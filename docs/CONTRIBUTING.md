# Contribuir a Pyteg

¡Gracias por tu interés en contribuir! Este documento resume cómo configurar el entorno, el estilo de código y el flujo de trabajo recomendado.

## Requisitos
- Python 3.11+
- [UV](https://github.com/astral-sh/uv)

## Configuración
```bash
uv sync
```

## Comandos canon
```bash
# Lint
uvx ruff check .

# Formato (verificar)
uvx ruff format --check .

# Formato (aplicar)
uvx ruff format .

# Tests + coverage
uvx coverage run --branch -m unittest
uvx coverage report -m

# mypy (foco en aridad de llamadas)
uvx mypy --ignore-missing-imports --explicit-package-bases --no-error-summary \
  --disable-error-code=import --disable-error-code=attr-defined \
  --disable-error-code=assignment --disable-error-code=return-value \
  --disable-error-code=operator --disable-error-code=index \
  --disable-error-code=misc --disable-error-code=type-arg \
  --disable-error-code=union-attr --disable-error-code=override \
  --disable-error-code=var-annotated --disable-error-code=valid-type \
  --disable-error-code=name-defined --disable-error-code=has-type \
  --disable-error-code=abstract --disable-error-code=no-untyped-def \
  --disable-error-code=no-untyped-call src/

# Todo en una pasada
./run_test.sh
```

## Estilo y convenciones
- Límite de línea: 88 caracteres.
- Ruff como linter y formateador.
- Docstrings y type hints en módulos clave.
- Mantener `README.md` y `docs/` actualizados (arquitectura, decisiones, cambios).

## Flujo de trabajo
1. Crear rama desde `main`.
2. Hacer cambios con commits atómicos y mensajes claros.
3. Asegurarse de que `./run_test.sh` pase localmente.
4. Abrir PR describiendo el cambio y motivación; enlazar issues cuando aplique.
5. Actualizar `docs/DECISIONS.md` si hay cambios arquitectónicos; `docs/CHANGELOG.md` si es un cambio visible para usuarios.

## Guía de protocolo
Para extender el protocolo o agregar mensajes:
- Ver `docs/como_crear_mensaje_cliente_a_servidor.md`.
- Ver `docs/como_crear_mensaje_servidor_a_cliente.md`.
- Ver `docs/como_crear_mensaje_bidireccional.md`.

## Contacto
Abrir un issue en GitHub para preguntas o discutir cambios.
