import secrets

from src.batalla import Batalla
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class Game:
    def __init__(self, mapa, mazo, jugadores, server):
        self._mapa = mapa
        self._start = False
        self._turnos = [PrimerTurno("NUllJugador")]
        self._jugadores = jugadores
        self._num_turno = 0
        self._num_ronda = 1
        self._mazo = mazo
        self._cant_canjes = {}
        self._server = server  # Referencia al servidor para notificar cambios

    def empezar(self):
        self._turnos = [PrimerTurno(j) for j in self.lista_jugadores()]
        self._mapa.asignar_paises(self.lista_jugadores())
        self._cant_canjes = dict.fromkeys(self.lista_jugadores(), 0)
        self._start = True

    def empezo(self):
        return self._start

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
        if self._num_turno >= len(self._turnos):
            return self.turnos()[-1]
        return self.turnos()[self.id_turno_actual()]

    def id_turno_actual(self):
        return self._num_turno

    def num_ronda(self):
        return self._num_ronda

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
            # Rotar la lista de jugadores para la nueva ronda
            jugadores = self.lista_jugadores()
            if len(jugadores) > 1:
                jugadores = jugadores[1:] + jugadores[:1]  # Rotar a la izquierda

            if isinstance(self.turno_actual(), PrimerTurno):
                self._turnos = [SegundoTurno(j) for j in jugadores]
            else:
                self._turnos = [SiguientesTurnos(j, self.mapa()) for j in jugadores]
            self._num_turno = 0
            self._num_ronda += 1

            # Notificar al servidor que se completó una ronda
            # para que actualice los colores de los jugadores
            self._server.enviar_colores_asignados()

    def jugadores(self):
        return self._jugadores

    def lista_jugadores(self):
        return self.jugadores()

    def lista_jugadores_orden_turno(self):
        """Devuelve la lista de jugadores en el orden actual de los turnos."""

        # Obtener los jugadores en el orden de los turnos actuales
        jugadores_orden = []
        for turno in self._turnos:
            jugador = turno.jugador_actual()
            if jugador not in jugadores_orden:
                jugadores_orden.append(jugador)

        # Si por alguna razón no hay jugadores
        # en los turnos, devolver la lista normal
        if not jugadores_orden:
            return self.lista_jugadores()

        return jugadores_orden

    def atacar(self, pais_atacante, pais_defensor):
        """
        Realiza un ataque entre dos países.

        Args:
            pais_atacante (str): País que inicia el ataque
            pais_defensor (str): País que recibe el ataque
        """
        # Obtener las unidades de cada país
        unidades_atacante = self.mapa().cantidad_unidades(pais_atacante)
        unidades_defensor = self.mapa().cantidad_unidades(pais_defensor)

        # Calcular cuántos dados usar
        dados_atacante_count = Batalla.calcular_cant_dados_atacante(unidades_atacante)
        dados_defensor_count = Batalla.calcular_cant_dados_defensor(unidades_defensor)

        # Generar dados aleatorios
        dados_atacante = sorted(
            [secrets.randbelow(6) + 1 for _ in range(dados_atacante_count)],
            reverse=True,
        )
        dados_defensor = sorted(
            [secrets.randbelow(6) + 1 for _ in range(dados_defensor_count)],
            reverse=True,
        )

        # Obtener nombres de los jugadores
        atacante_nombre = self.mapa().ocupado_por(pais_atacante).username()
        defensor_nombre = self.mapa().ocupado_por(pais_defensor).username()

        # Realizar la batalla
        resultado = Batalla.ataquen(
            atacante_nombre, defensor_nombre, dados_atacante, dados_defensor
        )

        # Aplicar las pérdidas
        for perdedor in resultado["restar"]:
            if perdedor == atacante_nombre:
                self.mapa().restar_una_unidad(pais_atacante)
            else:
                self.mapa().restar_una_unidad(pais_defensor)

        # Verificar si el país defensor fue conquistado
        if self.mapa().cantidad_unidades(pais_defensor) == 0:
            # El atacante conquista el país
            atacante = self.mapa().ocupado_por(pais_atacante)
            self.mapa().asignar_pais(atacante, pais_defensor)
            # Mover una unidad del atacante al país conquistado
            self.mapa().restar_una_unidad(pais_atacante)
            self.mapa().agregar_una_unidad(pais_defensor)

            print(f"{atacante_nombre} ha conquistado {pais_defensor}")
        else:
            print(f"El ataque de {atacante_nombre} a {pais_defensor} fue repelido")

        print(f"Ataque: {atacante_nombre} vs {defensor_nombre}")
        print(f"Dados atacante: {dados_atacante}, Dados defensor: {dados_defensor}")
        print(f"Resultado: {resultado}")

        return resultado
