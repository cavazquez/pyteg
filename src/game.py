from src.batalla import Batalla
from src.dados import Dados
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from src.tarjeta_de_pais import TarjetaDePais
from itertools import cycle
from random import sample

def build_tarjetas_de_paises(mapa, simbolos):
    #return [TarjetaDePais(pais, "Galeon") for pais in mapa.paises()]
    return [TarjetaDePais(*tupla) for tupla in zip(mapa.paises(), cycle(simbolos))]

class Game:
    def __init__(self, mapa, tarjetas):
        self._mapa = mapa
        self._start = False
        self._turnos = [PrimerTurno("NUllJugador")]
        self._jugadores = {}
        self._num_turno = 0
        self._tarjetas_de_paises = tarjetas

    def empezar(self):
        self._turnos = [PrimerTurno(j) for j in self.lista_jugadores()]
        self._mapa.asignar_paises(self.lista_jugadores())
        self._start = True

    def empezo(self):
        return self._start

    def atacar(self, atacante, defensor):
        dados_atacante = Dados.tirar_dados_ordenados(
            Batalla.calcular_cant_dados_atacante(
                self.mapa().cantidad_unidades(atacante)
            )
        )
        dados_defensor = Dados.tirar_dados_ordenados(
            Batalla.calcular_cant_dados_defensor(
                self.mapa().cantidad_unidades(defensor)
            )
        )
        resultado = Batalla.ataquen(
            self.mapa(), atacante, defensor, dados_atacante, dados_defensor
        )
        self._mapa.aplicar_resultado_batalla(resultado)

    def tarjetas_de_paises(self):
        return self._tarjetas_de_paises

    def dame_una_tarjeta(self):
        self._tarjetas_de_paises = sample(
                self._tarjetas_de_paises, k=len(self._tarjetas_de_paises))
        return self._tarjetas_de_paises.pop()

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self._num_turno

    def cant_jugadores(self):
        return len(self.lista_jugadores())

    def mapa(self):
        return self._mapa

    def finalizar_turno(self):
        self._num_turno += 1
        num = self._num_turno
        cant_jugadores = self.cant_jugadores()
        if num == cant_jugadores:
            self._turnos = [SegundoTurno(j) for j in self.lista_jugadores()]
            return

        if num % (cant_jugadores) == 0:
            self._turnos = [
                SiguientesTurnos(j, self.mapa()) for j in self.lista_jugadores()
            ]

    def jugadores(self):
        return self._jugadores

    def lista_jugadores(self):
        return list(self.jugadores().values())

    def agregar_jugador(self, id_j, nombre):
        if id_j not in self._jugadores:
            self._jugadores[id_j] = nombre
