import unittest

from src.read_toml import ReadToml

class TestReadToml(unittest.TestCase):
    def test_init(self):
        with open('src/paises.toml') as f:
            toml_string = f.read()
            #print(toml_string)
        self.assertTrue(ReadToml(toml_string))

    def test_continente(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        '''
        self.assertEqual(ReadToml(toml_string).continente('Argentina'), 'Pangea')


    def test_todos_los_paises(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        [Pangea.Brasil]

        [Africa]
        pos_x = 50
        pos_y = 23

        [Africa.Francia]
        '''
        self.assertListEqual(
                ReadToml(
                    toml_string).todos_los_paises(), ['Argentina', 'Brasil', 'Francia'])

    def test_get_paises(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        [Pangea.Brasil]

        [Africa]
        pos_x = 50
        pos_y = 23

        [Africa.Francia]
        '''
        self.assertDictEqual(
                ReadToml(
                    toml_string).get_paises('Pangea'), {'Argentina': {}, 'Brasil': {} })
        self.assertDictEqual(
                ReadToml(
                    toml_string).get_paises('Africa'), {'Francia': {}})


    def test_get_continentes(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        [Pangea.Brasil]

        [Africa]
        pos_x = 50
        pos_y = 23

        [Africa.Francia]
        '''
        self.assertListEqual(
                ReadToml(toml_string).get_continentes(), ['Pangea', 'Africa'])


    def test_coordenadas_continente(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30
        '''
        self.assertTupleEqual(
                ReadToml(toml_string).coordenadas_continente('Pangea'), (20, 30))


    def test_coordenadas(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        pos_x = 100
        pos_y = 120
        army_x = 200
        army_y = 300
        '''
        self.assertTupleEqual(
                ReadToml(toml_string).coordenadas('Argentina'), (100, 120, 200, 300))


    def test_get_cartas(self):
        toml_string = '''
        [Cartas]
        ballon = 'ballon.png'
        '''
        self.assertDictEqual(
                ReadToml(toml_string).get_cartas(), {'ballon': 'ballon.png'})


    def test_img_path(self):
        toml_string = '''
        [Cartas]
        [Pangea]
        pos_x = 20
        pos_y = 30

        [Pangea.Argentina]
        file = 'argentina.png'
        '''
        self.assertEqual(
                ReadToml(toml_string).img_path('Argentina'), 'argentina.png')

