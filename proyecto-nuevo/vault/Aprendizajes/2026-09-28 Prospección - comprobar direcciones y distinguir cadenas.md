---
fecha: 2026-09-28
etiquetas: [arcend, prospeccion, datos]
origen: arcend/prospectos/clinicas.csv
---
# Prospección - comprobar direcciones y distinguir cadenas

- **Qué pasó:** Al preparar la lista de 49 clínicas: la dirección de la ruta para IME (Lagasca 95) era en realidad Clínica Londres, una cadena; IME aparece en Vallehermoso 9 (Chamberí). Face Clinic resultó ser un grupo de 4 centros (Madrid, Aravaca-Pozuelo, Salamanca ciudad, Badajoz) en el que decide el grupo.
- **Lección:** Cada dirección de la ruta se comprueba una a una: una dirección errónea lleva a llamar a otra empresa. Una cadena nacional se excluye; un grupo local de 2-3 centros se incluye con aviso en `notas` (quién decide).
- **Cómo aplicarla:**
- Columna `cadena` y nota de aviso en el CSV.
- Face Clinic (4 centros): prioridad baja. IME: usar Vallehermoso 9; sede en Lagasca SIN VERIFICAR.
- Datos del buscador siguen SIN VERIFICAR hasta que el usuario los compruebe en la web de la clínica y en el Registro de centros sanitarios de la Comunidad de Madrid.

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
