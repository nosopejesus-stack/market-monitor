---
fecha: 2026-09-29
etiquetas: [arcend, prospeccion, registro, verificacion]
origen: verificación de las 49 clínicas de arcend/prospectos/clinicas.csv desde el PC del usuario, 2026-09-29
---
# 2026-09-29 Verificar clínicas en el Registro de centros sanitarios de la CAM

- **Qué pasó:** se consultaron las 49 direcciones del CSV en el Registro oficial de la Comunidad de Madrid. Salieron cosas que ni la web ni el buscador decían:
  - ARC-001, ARC-006 y ARC-013 tienen el mismo titular (Elenpa Médico Estético S.L.) → son un grupo.
  - IME y Berezo publican el CS11259, que el Registro no devuelve.
  - La Dra. Mirta Herrero publica el CS-13529, que es de su otro centro (Atocha 57).
  - Soria Vizcaíno (Maudes 64) y Velassaru (Feijóo 4): sin centro inscrito en esa dirección.
  - CEME publica el CS21415, que pertenece a otra sociedad en Calle Murcia 4.
  - Teléfonos cotejados con la web de cada clínica: varios del CSV no aparecen en la web (Blue Moon, Eternal, Lotus, MG).
- **Lección:** el Registro de la CAM es la fuente que manda para dirección, titular y número de registro. Cómo se consulta:
  - Buscador: https://gestiona.comunidad.madrid/cyes_web_reg/ , tipo "Centros y Servicios Sanitarios".
  - Por vía + número + CP, o por nº de registro con un POST a `ConsultarCS.icm`.
  - Solo desde el PC del usuario (desde el contenedor cloud no hay acceso: [[2026-09-28 Fuentes oficiales bloqueadas en el contenedor]]).
- **Cómo aplicarla:**
  - Antes de llamar: columnas `registro_sanitario`, `titular_registro`, `telefono_verificado` y `verificacion` del CSV rellenas.
  - Mismo titular en varias filas → `cadena = "revisar"` (hoy 001, 002, 006, 010, 013, 025, 037) y no se llama como clínica independiente sin aclararlo: [[Decisiones/2026-09-29 Arcend - N por tipos y grupos del mismo titular]].
  - Un número publicado que el Registro no devuelve, o que es de otro centro, es un hallazgo del informe, pero se presenta como "no coincide con el Registro", no como "no está inscrito".
  - Un teléfono que no aparece en la web se trata como SIN VERIFICAR.
  - Relacionado: [[2026-09-28 Prospección - comprobar direcciones y distinguir cadenas]].
