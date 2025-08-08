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
                    log_file = None
                elif "client" in script_name:
                    self.process_type = "CLIENT"
                    # Unificado: usar archivo compartido configurado
                    log_file = None
                else:
                    self.process_type = "OTHER"
                    log_file = None
            else:
                log_file = None

        # Resolver directorio de logs (configurable via env)
        log_dir_env = os.getenv("PYTEG_LOG_DIR", "logs")
        log_dir = Path(log_dir_env)
        log_dir.mkdir(exist_ok=True)
        # Nombre con fecha y hora local si no está configurado por env
        date_hour = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H")
        default_name = f"pyteg_{date_hour}.log"
        log_filename = os.getenv("PYTEG_LOG_FILE", default_name)
        self.log_file = str(log_dir / log_filename)

        # Escribir encabezado de sesión sin truncar el archivo
        with Path(self.log_file).open("a", encoding="utf-8") as f:
            f.write(f"=== DEBUG SESSION {datetime.datetime.now().astimezone()} ===\n")
            f.write(f"=== PROCESO: {self.process_type} PID: {self.pid} ===\n\n")

    def log(self, message):
        timestamp = datetime.datetime.now().astimezone().strftime("%H:%M:%S.%f")[:-3]
        full_message = f"[{self.process_type}:{self.pid}] {message}"

        with Path(self.log_file).open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {full_message}\n")

        # También imprimir en consola pero más limpio (solo mensajes importantes)
        if "user_id" in message or "MI user_id" in message:
            print(f"[DEBUG] {full_message}")


# Instancia global
debug_logger = DebugLogger()
