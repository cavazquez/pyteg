import unittest

from src.toml_reader import TomlReader, TomlReaderError


class TestTomlReaderValidation(unittest.TestCase):
    """Tests específicos para validación de errores en TomlReader."""

    def test_toml_syntax_error(self):
        """Test que TOML con sintaxis inválida lance TomlReaderError."""
        toml_invalido = """
        [Cartas
        jocker = "test.png"
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_invalido)
        self.assertIn("Error al parsear TOML", str(context.exception))

    def test_toml_no_es_diccionario(self):
        """Test que TOML que no sea diccionario lance error."""
        toml_invalido = "string_simple"
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_invalido)
        self.assertIn("Error al parsear TOML", str(context.exception))

    def test_seccion_cartas_faltante(self):
        """Test que TOML sin sección Cartas lance error."""
        toml_sin_cartas = """
        [Continente]
        pos_x = 10
        pos_y = 20
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_sin_cartas)
        self.assertIn("Cartas", str(context.exception))

    def test_cartas_no_es_diccionario(self):
        """Test que sección Cartas que no sea diccionario lance error."""
        toml_cartas_invalidas = """
        Cartas = "string_instead_of_dict"
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_cartas_invalidas)
        self.assertIn("debe ser un diccionario", str(context.exception))

    def test_carta_no_es_string(self):
        """Test que carta que no sea string lance error."""
        toml_carta_invalida = """
        [Cartas]
        jocker = 123
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_carta_invalida)
        self.assertIn("debe ser una cadena", str(context.exception))

    def test_continente_sin_coordenadas(self):
        """Test que continente sin pos_x o pos_y lance error."""
        toml_continente_sin_coords = """
        [Cartas]
        jocker = "test.png"

        [Continente]
        pos_x = 10
        # Falta pos_y

        [Continente.Pais]
        continente = "Continente"
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_continente_sin_coords)
        self.assertIn("debe tener pos_x y pos_y", str(context.exception))

    def test_coordenadas_continente_no_enteras(self):
        """Test que coordenadas de continente no enteras lancen error."""
        toml_coords_invalidas = """
        [Cartas]
        jocker = "test.png"

        [Continente]
        pos_x = "string"
        pos_y = 20
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_coords_invalidas)
        self.assertIn("deben ser enteros", str(context.exception))

    def test_pais_continente_inconsistente(self):
        """Test que país con continente inconsistente lance error."""
        toml_continente_inconsistente = """
        [Cartas]
        jocker = "test.png"

        [Continente1]
        pos_x = 10
        pos_y = 20

        [Continente1.Pais]
        continente = "Continente2"
        file = "test.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_continente_inconsistente)
        self.assertIn("declara continente", str(context.exception))

    def test_pais_file_no_string(self):
        """Test que campo file de país no string lance error."""
        toml_file_invalido = """
        [Cartas]
        jocker = "test.png"

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais]
        continente = "Continente"
        file = 123
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_file_invalido)
        self.assertIn("debe ser string", str(context.exception))

    def test_pais_coordenadas_no_enteras(self):
        """Test que coordenadas de país no enteras lancen error."""
        toml_coords_pais_invalidas = """
        [Cartas]
        jocker = "test.png"

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais]
        continente = "Continente"
        file = "test.png"
        pos_x = "string"
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_coords_pais_invalidas)
        self.assertIn("debe ser entero", str(context.exception))

    def test_adyacencias_no_diccionario(self):
        """Test que sección Adyacencias que no sea diccionario lance error."""
        # Crear un TOML donde Adyacencias no sea diccionario requiere
        # manipulación directa porque tomllib parsea "Adyacencias = string"
        # como string, no como sección

        # Simular el caso modificando directamente parsed_toml
        # Test con adyacencias como string en lugar de diccionario
        adyacencias_invalidas = """
        [Adyacencias]
        # Forzar que Adyacencias sea string manipulando después del parsing
        """
        reader = TomlReader(
            '[Cartas]\njocker = "test.png"', None, adyacencias_invalidas
        )
        reader.adyacencias = "string_instead_of_dict"

        with self.assertRaises(TomlReaderError) as context:
            reader._validar_adyacencias()  # noqa: SLF001
        self.assertIn("debe ser un diccionario", str(context.exception))

    def test_adyacencias_pais_no_lista(self):
        """Test que adyacencias de país que no sea lista lance error."""
        toml_adyacencias_no_lista = """
        [Cartas]
        jocker = "test.png"

        [Adyacencias]
        Pais1 = "string_instead_of_list"

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais1]
        continente = "Continente"
        file = "test.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_adyacencias_no_lista)
        self.assertIn("deben ser una lista", str(context.exception))

    def test_adyacente_no_string(self):
        """Test que país adyacente que no sea string lance error."""
        toml_adyacente_no_string = """
        [Cartas]
        jocker = "test.png"

        [Adyacencias]
        Pais1 = [123]

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais1]
        continente = "Continente"
        file = "test.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_adyacente_no_string)
        self.assertIn("debe ser string", str(context.exception))

    def test_pais_en_adyacencias_no_existe(self):
        """Test que país en adyacencias que no existe lance error."""
        toml_pais_inexistente = """
        [Cartas]
        jocker = "test.png"

        [Adyacencias]
        PaisInexistente = ["Pais1"]

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais1]
        continente = "Continente"
        file = "test.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_pais_inexistente)
        self.assertIn("no existe en el mapa", str(context.exception))

    def test_pais_adyacente_no_existe(self):
        """Test que país adyacente que no existe lance error."""
        toml_adyacente_inexistente = """
        [Cartas]
        jocker = "test.png"

        [Adyacencias]
        Pais1 = ["PaisInexistente"]

        [Continente]
        pos_x = 10
        pos_y = 20

        [Continente.Pais1]
        continente = "Continente"
        file = "test.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4
        """
        with self.assertRaises(TomlReaderError) as context:
            TomlReader(toml_adyacente_inexistente)
        self.assertIn("no existe en el mapa", str(context.exception))

    def test_toml_valido_completo(self):
        """Test que TOML válido completo no lance errores."""
        toml_valido = """
        [Cartas]
        jocker = "jocker.png"
        ballon = "ballon.png"

        [Adyacencias]
        Pais1 = ["Pais2"]
        Pais2 = ["Pais1"]

        [Continente1]
        pos_x = 10
        pos_y = 20

        [Continente1.Pais1]
        continente = "Continente1"
        file = "pais1.png"
        pos_x = 1
        pos_y = 2
        army_x = 3
        army_y = 4

        [Continente2]
        pos_x = 50
        pos_y = 60

        [Continente2.Pais2]
        continente = "Continente2"
        file = "pais2.png"
        pos_x = 5
        pos_y = 6
        army_x = 7
        army_y = 8
        """
        # No debe lanzar excepción
        reader = TomlReader(toml_valido)

        # Verificar que los datos se procesaron correctamente
        self.assertEqual(reader.continente("Pais1"), "Continente1")
        self.assertEqual(reader.continente("Pais2"), "Continente2")
        self.assertEqual(reader.obtener_paises_adyacentes("Pais1"), ["Pais2"])
        self.assertEqual(len(reader.todos_los_paises()), 2)


if __name__ == "__main__":
    unittest.main()
