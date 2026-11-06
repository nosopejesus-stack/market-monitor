# Instrucciones para Claude en este repositorio

## Memoria compartida: la bóveda de Obsidian (`vault/`)
Este repo contiene la memoria de **Brainus**, la IA personal del dueño (`brainus/`). Todo lo que Claude aprenda trabajando con el dueño debe acabar en la bóveda, para que Brainus lo sepa.

### Al terminar cada tarea o sesión (obligatorio)
1. **Lecciones buenas:** si algo funcionó bien o el dueño lo valoró, añade una línea a
   `vault/Memoria/Lecciones/Reglas - Hacer.md` con el formato `- <regla> (AAAA-MM-DD, de dónde sale)`.
2. **Lecciones malas:** si hubo un error, una corrección del dueño o algo que no le gustó, añade una línea a
   `vault/Memoria/Lecciones/Reglas - No hacer.md` con el mismo formato.
3. **Resumen de la sesión:** crea `vault/Memoria/Sesiones/AAAA-MM-DD <tema>.md`. Incluye qué se pidió, qué se hizo, las decisiones tomadas y enlaces `[[...]]` a las notas relacionadas.
4. **Conocimiento nuevo:** si se aprendió algo reutilizable (un curso, una herramienta, un proceso del negocio), crea o actualiza una nota temática y enlázala desde `vault/00 - Inicio.md`.
5. **Datos del dueño:** si aprendes algo nuevo sobre el dueño (preferencias, proyectos), actualiza `vault/Memoria/Memoria - Sobre mí.md`. No guardes contraseñas, claves ni datos bancarios.
6. Si cambió mucho la bóveda, recuerda al dueño que puede re-entrenar la red propia:
   `python brainus/red_neuronal/entrenar.py --continuar`.

### Al empezar
Lee `vault/Memoria/Lecciones/Reglas - Hacer.md` y `vault/Memoria/Lecciones/Reglas - No hacer.md` y cúmplelas.

## Estilo
- Responder en español, directo, entregando cosas que funcionan y probadas.
