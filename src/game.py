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
        self._cant_canjes = {}

    def empezar(self):
        self._turnos = [PrimerTurno(j) for j in self.lista_jugadores()]
        self._mapa.asignar_paises(self.lista_jugadores())
        self._cant_canjes = {jugador: 0 for jugador in self.lista_jugadores()}

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

    def dame_una_tarjeta(self, jugador):
        cant_tarjetas_asignadas = self.mazo().cant_tarjetas_asignadas(jugador)
        if cant_tarjetas_asignadas == 5:
            lista_3_tarjetas = self.mazo().dame_3_tarjetas_para_canje(jugador)
            self.canjear(jugador, lista_3_tarjetas)
        self.mazo().asignar_tarjeta(jugador)

    def turnos(self):
        return self._turnos

    def turno_actual(self):
        return self.turnos()[self.id_turno_actual()]

    def id_turno_actual(self):
        return self._num_turno

    def cant_canjes(self, jugador):
        return self._cant_canjes[jugador]

    def canjear(self, jugador, tarjetas):
        cant_canjes = self.cant_canjes(jugador)
        turno = self._turnos[self._num_turno]
        cantidad_a_agregar = 0
        if cant_canjes == 0:
            cantidad_a_agregar = 4
        if cant_canjes == 1:
            cantidad_a_agregar = 7
        if cant_canjes >= 2:
            cantidad_a_agregar = 5 * cant_canjes

        turno.agregar_unidades_generales(cantidad_a_agregar)
        self._mazo.desasignar_tarjetas(tarjetas)
        self._cant_canjes[jugador] += 1

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
