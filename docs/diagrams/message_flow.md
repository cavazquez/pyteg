# Diagrama de flujo de mensajes

A continuación, un diagrama de secuencia (Mermaid) que resume los flujos principales de mensajes entre Cliente(s) y Servidor.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario
    participant C as Cliente
    participant S as Servidor

    Note over C,S: Inicio de turno
    S->>C: MsgTurnoActual
    S->>C: MsgUnidadesDisponibles (solo jugador activo)
    C->>U: Actualiza barra de estado y GUI

    break Agregar Unidad
        U->>C: Click agregar unidad (UI)
        C->>S: MsgAgregarUnidad(pais, tipo)
        alt Validación OK
            S->>S: Aplica cambio (server/juego/game.py + server/juego/mapa.py)
            S->>C: MsgMapaActualizado (broadcast)
            S->>C: MsgUnidadesDisponibles (al jugador activo)
        else Error de validación
            S->>C: MsgChat(tipo=error, detalle)
        end
    end

    break Atacar
        U->>C: Click atacar (UI)
        C->>S: MsgAtacar(origen, destino, dados)
        alt Validación OK
            S->>S: Ejecuta batalla (server/juego/game.py)
            S->>C: MsgResultadoBatalla (broadcast)
            S->>C: MsgMapaActualizado (broadcast)
        else Error de validación
            S->>C: MsgChat(tipo=error, detalle)
        end
    end

    break Mover Unidad
        U->>C: Click mover (UI)
        C->>S: MsgMoverUnidad(origen, destino, cantidad)
        alt Validación OK
            S->>S: Aplica movimiento (server/juego/game.py + server/juego/mapa.py)
            S->>C: MsgMapaActualizado (broadcast)
        else Error de validación
            S->>C: MsgChat(tipo=error, detalle)
        end
    end

    break Finalizar Turno
        U->>C: Click finalizar turno (UI)
        C->>S: MsgFinalizarTurno()
        alt Validación OK
            S->>S: Avanza turno
            S->>C: MsgTurnoActual (broadcast)
            S->>C: MsgUnidadesDisponibles (jugador activo)
        else Error de validación
            S->>C: MsgChat(tipo=error, detalle)
        end
    end
```

Notas
- Los mensajes de error siempre se publican en el chat del cliente como `MsgChat` con tipo `error`.
- El orden en ataques exitosos es: resultado de batalla -> actualización de mapa.
- Algunas notificaciones son broadcast (a todos los clientes) y otras dirigidas (solo al jugador activo).
