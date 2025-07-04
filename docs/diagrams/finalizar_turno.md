# Diagrama de Secuencia: Finalizar Turno

```mermaid
sequenceDiagram
    participant Usuario
    participant GUI as GUI (Cliente)
    participant Client as ClientTransmisor
    participant Server as Servidor
    participant Task as ServerTaskFinalizarTurno
    participant Game as Game
    participant STrans as ServerTransmisor

    Note over Usuario,GUI: Cliente
    Note over Server,STrans: Servidor

    Usuario->>+GUI: Click en "Finalizar Turno"
    GUI->>+Client: finalizar_turno()
    Client->>Client: Crea MsgFinalizarTurno()
    Client->>+Server: {"mensaje": "finalizar_turno"}
    
    Server->>+Task: Crea ServerTaskFinalizarTurno
    Server->>+Task: run()
    Task->>+Game: finalizar_turno()
    Game->>Game: Incrementa contador de turno
    Game->>Game: Actualiza estado del juego
    Game-->>-Task: 
    
    Task->>+STrans: enviar_turno_actual()
    STrans-->>-Client: Envía mensaje de turno actual
    Client->>+GUI: update_turno(num_turno, num_ronda)
    GUI->>GUI: Actualiza interfaz de usuario
    GUI-->>-Usuario: Muestra turno actualizado
```

## Cómo visualizar este diagrama

1. **En VS Code**: Instala la extensión "Mermaid Preview" o "Markdown Preview Mermaid Support".
2. **En GitHub/GitLab**: El diagrama se renderizará automáticamente al ver el archivo .md
3. **En línea**: Usa el [editor de Mermaid Live](https://mermaid.live/)

## Componentes principales

1. **Cliente**:
   - `GUI`: Maneja la interfaz de usuario
   - `ClientTransmisor`: Envía mensajes al servidor

2. **Servidor**:
   - `Server`: Recibe y procesa mensajes
   - `ServerTaskFinalizarTurno`: Maneja la lógica de finalizar turno
   - `Game`: Contiene la lógica principal del juego
   - `ServerTransmisor`: Envía actualizaciones a los clientes
