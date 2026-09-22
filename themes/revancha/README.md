# TEG La Revancha

Este directorio contiene la base de datos aislada de Revancha. El inventario y el grafo parten del auditado de `docs/revancha-map-audit.md`.

Las siluetas SVG de `countries/` y las cartas son assets estructurales provisionales para que `TomlReader.from_theme("revancha", strict=True)` pueda validar el tema sin importar archivos de `classic`. El diseño final del tablero, las rutas wrap-x y los assets definitivos quedan en #227. Las fronteras pendientes del auditado no se habilitan aquí.
