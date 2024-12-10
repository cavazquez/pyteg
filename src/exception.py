class MensajeNoValidoError(Exception):
    def __init__(self, msg):
        self._msg = f"MensajeNoValidoError: {msg}"
        super().__init__(self._msg)
