# Perfiles de reglas por tema

Cada tema puede declarar sus valores normativos en `themes/<tema>/reglas.toml`.
El servidor carga el archivo antes de abrir el socket y lo publica dentro del
snapshot público. El mismo archivo entra en `map_hash`, por lo que un cliente
con reglas distintas recibe el rechazo normal de handshake.

El perfil agrupa:

- objetivo de victoria y valores iniciales de las rondas;
- mínimo de refuerzos, divisor por países y bonos continentales;
- progresión de canjes, canje especial y límite de tarjetas;
- habilitación, costo, alcance y daño de misiles;
- límites de dados, objetivos y mazo de situaciones.

`classic` conserva el lobby histórico (0 significa controlar todos los países)
y declara 30 como objetivo configurable. `revancha` declara 45 países, 8 y 4
unidades para sus dos primeras rondas, sus siete bonos y misiles activos.

Los temas antiguos sin `reglas.toml` reciben un perfil compatible con las
constantes históricas. Un archivo presente se valida completo; los valores
negativos, rangos incompatibles y rulesets de situaciones desconocidos hacen
fallar el arranque para evitar partidas con reglas mezcladas.
