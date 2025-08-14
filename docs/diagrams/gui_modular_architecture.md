# Arquitectura Modular de la GUI - PyTeg

Este diagrama muestra la nueva arquitectura modular de la interfaz gráfica tras la refactorización completa.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        gui.py (366 líneas)                     │
│                     Ventana Principal                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Coordinación de gestores                              │   │
│  │ • Eventos de Qt (keyPressEvent, closeEvent)            │   │
│  │ • Ventanas auxiliares (conectar, admin, esperar)       │   │
│  │ • Configuración de partida                             │   │
│  │ • Cambio de idioma                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ coordina
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gestores Especializados                     │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  LayoutManager  │  │  ThemeManager   │  │ PlayersManager  │ │
│  │   (313 líneas)  │  │   (115 líneas)  │  │   (92 líneas)   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Estructura    │  │ • Temas claro/  │  │ • Lista de      │ │
│  │   visual        │  │   oscuro        │  │   jugadores     │ │
│  │ • Widgets base  │  │ • Estilos CSS   │  │ • Widgets de    │ │
│  │ • Layout de     │  │ • Toggle de     │  │   jugador       │ │
│  │   ventana       │  │   modo          │  │ • Indicadores   │ │
│  │ • Iconos        │  │ • Aplicación    │  │   de color      │ │
│  │                 │  │   por componente│  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ StatusManager   │  │  UnitsManager   │  │GameActionsManager│ │
│  │   (125 líneas)  │  │   (111 líneas)  │  │   (79 líneas)   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Barra de      │  │ • Panel de      │  │ • Atacar        │ │
│  │   estado        │  │   unidades      │  │ • Finalizar     │ │
│  │ • Información   │  │   disponibles   │  │   turno         │ │
│  │   de jugador    │  │ • Efectos       │  │ • Cálculo de    │ │
│  │ • Mensajes      │  │   visuales      │  │   unidades      │ │
│  │ • Estado del    │  │ • Flash effects │  │   máximas       │ │
│  │   juego         │  │ • Estilos       │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo de Responsabilidades

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Usuario       │    │  Eventos Qt     │    │   Mensajes      │
│   Interactúa    │────│   (gui.py)      │────│   del Servidor  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │ delega a
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gestores Especializados                     │
│                                                                 │
│  Layout ──► Estructura visual y widgets                        │
│  Theme ───► Aplicación de estilos y temas                      │
│  Players ─► Gestión de lista de jugadores                      │
│  Status ──► Actualización de barra de estado                   │
│  Units ───► Gestión de unidades disponibles                    │
│  Actions ─► Procesamiento de acciones de juego                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ actualiza
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Interfaz de Usuario                       │
│                                                                 │
│  • Widgets actualizados                                        │
│  • Estados sincronizados                                       │
│  • Funcionalidad completa preservada                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Beneficios de la Arquitectura Modular

### 🎯 **Separación de Responsabilidades**
- Cada gestor tiene una función específica y bien definida
- Reducción de acoplamiento entre componentes
- Código más organizado y comprensible

### 🔧 **Mantenibilidad**
- Fácil localización de funcionalidad por área de responsabilidad
- Modificaciones aisladas sin impacto en otros módulos
- Reducción significativa de la complejidad del archivo principal

### 📈 **Escalabilidad**
- Nuevas funcionalidades pueden agregarse fácilmente
- Cada gestor puede evolucionar independientemente
- Arquitectura extensible para futuras mejoras

### 🧪 **Testabilidad**
- Cada gestor puede ser probado independientemente
- Facilita la creación de tests unitarios específicos
- Mejor cobertura de código y detección de errores

## Métricas de Impacto

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Líneas en gui.py** | ~1039 | 366 | **65% reducción** |
| **Archivos de GUI** | 1 monolítico | 7 modulares | **7x organización** |
| **Responsabilidades** | Todas mezcladas | 6 especializadas | **Separación clara** |
| **Tests pasando** | 121 | 121 | **100% funcionalidad** |
| **Warnings linting** | 0 | 0 | **Calidad mantenida** |

## Patrón de Diseño

La arquitectura sigue el patrón **Manager/Coordinator**:

1. **gui.py** actúa como **Coordinator** - orquesta y coordina
2. **Gestores** actúan como **Managers** - especializados en áreas específicas
3. **Comunicación** bidireccional entre coordinator y managers
4. **Estado compartido** a través de referencias al main window
5. **Responsabilidades claras** sin solapamiento entre gestores

Esta refactorización transforma un archivo monolítico de más de 1000 líneas en una arquitectura modular, mantenible y escalable, sin perder funcionalidad ni introducir regresiones.
