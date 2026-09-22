# Cartas de Revancha

El tema `revancha` carga el reparto de cartas desde
[`themes/revancha/cartas.toml`](/home/cristian/repos/propios/pyteg/themes/revancha/cartas.toml)
y las equivalencias de canje desde
[`themes/revancha/reglas.toml`](/home/cristian/repos/propios/pyteg/themes/revancha/reglas.toml).

El reparto contiene 72 cartas de país y siete cartas de continente. Cada país
declara su símbolo de forma explícita, por lo que reconectar un cliente o
reiniciar una partida no vuelve a generar símbolos cíclicos. La carta marcada
como `Supertarjeta` pertenece al mazo de países y equivale por sí sola a un
canje. `Soldado` se trata como comodín al validar una combinación.

Las equivalencias de continente son datos del perfil. Una lista vacía significa
que la carta completa un canje por sí sola; una lista con símbolos aporta esas
variables y puede combinarse con cartas de país. Así, América del Sur aporta
`Avion + Tanque`, África `Avion + Barco`, América Central `Tanque` y Oceanía
`Barco`.

El servidor valida que todas las cartas seleccionadas pertenezcan al jugador,
que representen exactamente un canje y que no se haya canjeado antes en el
mismo turno. La progresión de Revancha es 6, 10, 15, 20…; Classic mantiene su
progresión histórica 4, 7, 10… mediante su perfil.

Al finalizar una conquista, el reclamo entrega la carta de país. Si la
conquista completa un continente, el servidor deja pendiente la carta de ese
continente y la entrega junto con el reclamo. Las cartas privadas se envían al
cliente que las posee; nunca se incluyen en el snapshot público.
