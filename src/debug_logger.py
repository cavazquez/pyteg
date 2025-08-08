import datetime
import os
import sys
from pathlib import Path


class DebugLogger:
    def __init__(self, log_file=None):
        self.pid = os.getpid()
        self.process_type = "UNKNOWN"

        if log_file is None:
            # Determinar el tipo de proceso basado en los argumentos
            if len(sys.argv) > 0:
                script_name = Path(sys.argv[0]).name
                if "server" in script_name:
                    self.process_type = "SERVER"
                    log_file = "debug_server.log"
                elif "client" in script_name:
                    self.process_type = "CLIENT"
                    # Usar timestamp y PID para diferenciar clientes
                    timestamp = datetime.datetime.now(datetime.UTC).strftime("%H%M%S")
                    log_file = f"debug_client_{timestamp}_{self.pid}.log"
                else:
                    self.process_type = "OTHER"
                    log_file = f"debug_{self.pid}.log"
            else:
                log_file = f"debug_{self.pid}.log"

        # Resolver directorio de logs (configurable via env)
        log_dir_env = os.getenv("PYTEG_LOG_DIR", "logs")
        log_dir = Path(log_dir_env)
        log_dir.mkdir(exist_ok=True)

        self.log_file = str(log_dir / log_file)
        # Limpiar el archivo al inicio
        with Path(self.log_file).open("w", encoding="utf-8") as f:
            f.write(
                f"=== DEBUG LOG INICIADO {datetime.datetime.now(datetime.UTC)} ===\n"
            )
            f.write(f"=== PROCESO: {self.process_type} PID: {self.pid} ===\n")
            f.write(f"=== ARCHIVO: {self.log_file} ===\n\n")

    def log(self, message):
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%H:%M:%S.%f")[:-3]
        full_message = f"[{self.process_type}:{self.pid}] {message}"

        with Path(self.log_file).open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {full_message}\n")

        # También imprimir en consola pero más limpio (solo mensajes importantes)
        if "user_id" in message or "MI user_id" in message:
            print(f"[DEBUG] {full_message}")


# Instancia global
debug_logger = DebugLogger()
