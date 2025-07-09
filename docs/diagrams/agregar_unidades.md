# Diagrama de Secuencia: Agregar Unidades

```mermaid
sequenceDiagram
    participant Usuario
    participant GUI as GUI (Cliente)
    participant Client as ClientTransmisor
    participant Server as Servidor
    participant Task as ServerTaskAgregarUnidad
    participant Mapa as Mapa
    participant STrans as ServerTransmisor

    Note over Usuario,GUI: Cliente
    Note over Server,STrans: Servidor

    Usuario->>+GUI: Click en país para agregar unidad
    GUI->>+Client: agregar_unidad(pais, tipo_unidad)
    Client->>Client: Crea MsgAgregarUnidad()
    Client->>+Server: {"mensaje": "agregar_unidad", "pais": "...", "tipo_unidad": "infanteria"}
    
    Server->>+Task: Crea ServerTaskAgregarUnidad
    Server->>+Task: run()
    
    Task->>Task: Verificar permisos del jugador
    Task->>Task: Verificar unidades disponibles
    Task->>+Mapa: agregar_una_unidad(pais)
    Mapa->>Mapa: Incrementa unidades en el país
    Mapa-->>-Task: 
    
    Task->>Task: Decrementar unidades disponibles
    Task->>+STrans: enviar_mapa()
    STrans-->>-Client: Envía estado actualizado del mapa
    
    Task->>+STrans: enviar_unidades_disponibles()
    STrans->>STrans: Calcula unidades disponibles actualizadas
    STrans-->>-Client: Envía unidades disponibles actualizadas
    
    Client->>+GUI: update_mapa()
    GUI->>GUI: Actualiza visualización del mapa
    Client->>+GUI: update_unidades_disponibles(unidades)
    GUI->>GUI: Actualiza panel con estilo mejorado
    Note over GUI: - Iconos para cada tipo de unidad<br/>- Colores distintivos<br/>- Bordes destacados<br/>- Fondo coloreado
    GUI-->>-Usuario: Muestra mapa y unidades actualizadas
```

## Mejoras en el Estilo Visual

### Unidades Generales (Infantería)
- **Icono**: 🪖 (casco militar)
- **Color**: Verde (#2E7D32) cuando hay unidades disponibles
- **Fondo**: Verde claro (#E8F5E8) con borde verde (#4CAF50)

### Unidades de Continentes
- **Icono**: 🌍 (globo terráqueo)
- **Color**: Azul (#1565C0) cuando hay unidades disponibles
- **Fondo**: Azul claro (#E3F2FD) con borde azul (#2196F3)

### Misiles (si están disponibles)
- **Icono**: 🚀 (cohete)
- **Color**: Rojo (#D32F2F)
- **Fondo**: Rojo claro (#FFEBEE) con borde rojo (#F44336)

### Estados Sin Unidades
- **Color**: Gris (#666666)
- **Sin fondo especial**: Estilo minimalista

## Cómo visualizar este diagrama

Para ver este diagrama renderizado, puedes usar:
1. **GitHub/GitLab**: El diagrama se renderiza automáticamente
2. **VS Code**: Instala la extensión "Markdown Preview Mermaid Support"
3. **Online**: Copia el código en [mermaid.live](https://mermaid.live)
