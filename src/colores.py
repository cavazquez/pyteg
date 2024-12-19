import json
from abc import ABC, abstractmethod


class IColor(ABC):
    @abstractmethod
    def __init__(self, r, g, b):
        self._validate_rgb(r, g, b)
        self._r = r
        self._g = g
        self._b = b

    def to_json(self):
        return json.dumps({"r": self._r, "g": self._g, "b": self._b})

    def __str__(self):
        return f"r: {self._r}, g: {self._g}, b: {self._b}"

    def to_hex(self):
        return "".join(["#", ("{:02X}" * 3).format(self._r, self._g, self._b).lower()])

    def __eq__(self, otro):
        return self._r == otro._r and self._g == otro._g and self._b == otro._b

    def __hash__(self):
        return hash(self.to_hex())

    @staticmethod
    def _validate_rgb(r, g, b):
        if not all(isinstance(v, int) and 0 <= v <= 255 for v in (r, g, b)):
            msg = "Los valores RGB deben ser enteros entre 0 y 255"
            raise ValueError(msg)

    @classmethod
    def from_rgb(cls, r, g, b):
        return cls(r, g, b)

    @classmethod
    def from_hex(cls, hex_value):
        hex_value = hex_value.lstrip("#")
        if len(hex_value) != 6:
            msg = "El valor hexadecimal debe tener 6 caracteres"
            raise ValueError(msg)
        r, g, b = tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
        return cls(r, g, b)


class Rojo(IColor):
    def __init__(self):
        super().__init__(255, 0, 0)


class Verde(IColor):
    def __init__(self):
        super().__init__(0, 255, 0)


class Azul(IColor):
    def __init__(self):
        super().__init__(0, 0, 255)


class Amarillo(IColor):
    def __init__(self):
        super().__init__(255, 255, 0)


class Cian(IColor):
    def __init__(self):
        super().__init__(0, 255, 255)


class Magenta(IColor):
    def __init__(self):
        super().__init__(255, 0, 255)


class Negro(IColor):
    def __init__(self):
        super().__init__(0, 0, 0)


class Blanco(IColor):
    def __init__(self):
        super().__init__(255, 255, 255)
