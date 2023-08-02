import unittest

from src.read_toml import ReadToml

class TestReadToml(unittest.TestCase):
    def test_init(self):
        self.assertTrue(ReadToml('src/paises.toml'))

