#!/usr/bin/env python3
"""Script para analizar el código del proyecto.

Ejecuta múltiples herramientas de análisis estático y genera un reporte consolidado.
"""

from __future__ import annotations

import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path

# Colores para output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


# Lista blanca de comandos seguros permitidos
_ALLOWED_COMMANDS = {
    "uv",
    "ruff",
    "mypy",
    "radon",
    "vulture",
    "coverage",
    "bandit",
    "python",
}


def _validate_command(cmd: list[str]) -> bool:
    """Valida que el comando esté en la lista blanca de comandos seguros.

    Args:
        cmd: Comando a validar.

    Returns:
        True si el comando es seguro, False en caso contrario.

    """
    if not cmd:
        return False
    # El primer elemento es el ejecutable
    executable = cmd[0]
    # Extraer el nombre base si es un path
    base_name = Path(executable).name
    return base_name in _ALLOWED_COMMANDS


def run_command(
    cmd: list[str],
    description: str,
    *,
    continue_on_error: bool = False,
) -> tuple[bool, str]:
    """Ejecuta un comando y retorna el resultado.

    Args:
        cmd: Comando a ejecutar como lista. Debe estar en la lista blanca.
        description: Descripción del comando.
        continue_on_error: Si True, no falla si el comando falla.

    Returns:
        Tupla (éxito, salida).

    Raises:
        ValueError: Si el comando no está en la lista blanca.

    """
    # Validar que el comando sea seguro
    if not _validate_command(cmd):
        error_msg = f"Comando no permitido: {cmd[0]}"
        raise ValueError(error_msg)

    print(f"{BOLD}{description}...{RESET}")
    try:
        # Resolver el path completo del ejecutable para seguridad
        executable = cmd[0]
        if "/" not in executable and "\\" not in executable:
            # Buscar el ejecutable en PATH
            full_path = shutil.which(executable)
            if full_path:
                cmd[0] = full_path

        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent,
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        if success:
            print(f"{GREEN}✓ {description} completado{RESET}")
        else:
            status = "continuando" if continue_on_error else "falló"
            print(f"{YELLOW}⚠ {description} {status}{RESET}")
    except FileNotFoundError:
        print(f"{RED}✗ {description}: comando no encontrado{RESET}")
        return False, ""
    else:
        return success, output


def main() -> int:
    """Función principal del script de análisis.

    Returns:
        Código de salida (0 = éxito, 1 = error).

    """
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}Análisis de Código - PyTeg{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    results: dict[str, tuple[bool, str]] = {}
    errors = []

    # 1. Ruff lint
    success, output = run_command(
        ["uv", "run", "ruff", "check", "src", "tests", "scripts"],
        "Ruff lint",
    )
    results["Ruff Lint"] = (success, output)
    if not success:
        errors.append("Ruff lint encontró problemas")

    # 2. Ruff format check
    success, output = run_command(
        ["uv", "run", "ruff", "format", "--check", "src", "tests", "scripts"],
        "Ruff format check",
    )
    results["Ruff Format"] = (success, output)
    if not success:
        errors.append("Ruff format encontró problemas de formato")

    # 3. MyPy type checking
    success, output = run_command(
        ["uv", "run", "mypy", "src", "tests", "scripts"],
        "MyPy type checking",
        continue_on_error=True,
    )
    results["MyPy"] = (success, output)

    # 4. Radon complexity
    success, output = run_command(
        ["uv", "run", "radon", "cc", "src", "-a", "-nb"],
        "Radon complexity analysis",
        continue_on_error=True,
    )
    results["Radon Complexity"] = (success, output)

    # 5. Radon maintainability
    success, output = run_command(
        ["uv", "run", "radon", "mi", "src", "-nb"],
        "Radon maintainability index",
        continue_on_error=True,
    )
    results["Radon Maintainability"] = (success, output)

    # 6. Vulture dead code
    success, output = run_command(
        ["uv", "run", "vulture", "src", "--min-confidence", "80"],
        "Vulture dead code detection",
        continue_on_error=True,
    )
    results["Vulture"] = (success, output)

    # 7. Coverage (si hay tests)
    success, output = run_command(
        [
            "uv",
            "run",
            "coverage",
            "run",
            "--branch",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
        ],
        "Coverage analysis",
        continue_on_error=True,
    )
    if success:
        # Generar reporte de coverage
        coverage_cmd = ["uv", "run", "coverage", "report", "-m"]
        if _validate_command(coverage_cmd):
            # Resolver path completo para seguridad
            if shutil.which("uv"):
                coverage_cmd[0] = str(shutil.which("uv"))
            subprocess.run(  # noqa: S603
                coverage_cmd,
                check=False,
                cwd=Path(__file__).parent.parent,
            )
    results["Coverage"] = (success, output)

    # 8. Bandit security
    success, output = run_command(
        ["uv", "run", "bandit", "-r", "src", "-f", "txt"],
        "Bandit security analysis",
        continue_on_error=True,
    )
    results["Bandit"] = (success, output)

    # Resumen
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}Resumen de Análisis{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    for tool, (success, _) in results.items():
        status = f"{GREEN}✓ OK{RESET}" if success else f"{YELLOW}⚠ Revisar{RESET}"
        print(f"{tool:30} {status}")

    if errors:
        print(f"\n{RED}{BOLD}Errores encontrados:{RESET}")
        for error in errors:
            print(f"  {RED}• {error}{RESET}")
        return 1

    print(f"\n{GREEN}{BOLD}✓ Análisis completado exitosamente{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
