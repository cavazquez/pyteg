from random import sample

from src.batalla import Batalla
from src.dados import Dados
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class Game:
    def __init__(self, mapa, mazo):
        self._mapa = mapa
        self._start = False
        self._turnos = [PrimerTurno("NUllJugador")]
        self._jugadores = {}
        self._num_turno = 0
        self._mazo = mazo
        self.cant_canjes = 0

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
        resultado = Batalla.ataquen(atacante, defensor, dados_atacante, dados_defensor)
        self._mapa.aplicar_resultado_batalla(resultado)

    def mazo(self):
        return self._mazo

    def dame_una_tarjeta(self):
        self._tarjetas_de_paises = sample(
            self._tarjetas_de_paises, k=len(self._tarjetas_de_paises)
        )
        return self._tarjetas_de_paises.pop()

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self._num_turno

    def canjear(self, tarjetas, cant_canjes):
        if cant_canjes == 0:
            self._turnos[self._num_turno].agregar_unidades_generales(4)
        if cant_canjes == 1:
            self._turnos[self._num_turno].agregar_unidades_generales(7)
        if cant_canjes >= 2:
            self._turnos[self._num_turno].agregar_unidades_generales(5 * cant_canjes)

        self._mazo.liberar_tarjetas(tarjetas)

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
