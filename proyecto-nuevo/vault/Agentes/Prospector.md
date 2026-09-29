# Prospector

Definición: `.claude/agents/prospector.md`. Volver a [[Equipo de agentes]].

## Historial de aprendizajes de este agente
- 2026-09-28: desde el contenedor solo WebSearch; nombre/dirección/teléfono quedan SIN VERIFICAR y el decisor se saca desde el PC del usuario. ~La mitad de las agencias de los 5 distritos prioritarios son franquicias. Ver [[Aprendizajes/2026-09-28 Prospección desde el contenedor cloud]].
- 2026-09-28 (Arcend, 49 clínicas): comprobar cada dirección de la ruta una a una (IME: Lagasca 95 era Clínica Londres; la real está en Vallehermoso 9). Cadena nacional → excluir; grupo local de 2-3 centros → incluir con aviso (Face Clinic, 4 centros: prioridad baja). Ver [[Aprendizajes/2026-09-28 Prospección - comprobar direcciones y distinguir cadenas]].
- 2026-09-29 (Arcend, 49 clínicas): verificar cada clínica en el Registro de centros sanitarios de la CAM (gestiona.comunidad.madrid/cyes_web_reg, por vía+número+CP o por nº de registro) y cotejar el teléfono con su web. Mismo titular en varias filas → `cadena = "revisar"`, no se llama como independiente sin aclararlo. Ver [[Aprendizajes/2026-09-29 Verificar clínicas en el Registro de centros sanitarios de la CAM]] y [[Decisiones/2026-09-29 Arcend - N por tipos y grupos del mismo titular]].
