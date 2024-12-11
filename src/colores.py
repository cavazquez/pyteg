import json
from abc import ABC, abstractmethod


class IColor(ABC):
    @abstractmethod
    def __init__(self):
        pass

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


class Rojo(IColor):
    def __init__(self):
        self._r = 255
        self._g = 0
        self._b = 0


class Verde(IColor):
    def __init__(self):
        self._r = 0
        self._g = 255
        self._b = 0


class Azul(IColor):
    def __init__(self):
        self._r = 0
        self._g = 0
        self._b = 255


class Amarillo(IColor):
    def __init__(self):
        self._r = 255
        self._g = 255
        self._b = 0


class Cian(IColor):
    def __init__(self):
        self._r = 0
        self._g = 255
        self._b = 255


class Magenta(IColor):
    def __init__(self):
        self._r = 255
        self._g = 0
        self._b = 255


class Negro(IColor):
    def __init__(self):
        self._r = 0
        self._g = 0
        self._b = 0


class Blanco(IColor):
    def __init__(self):
        self._r = 255
        self._g = 255
        self._b = 255
