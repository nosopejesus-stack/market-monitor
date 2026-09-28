# Equipo de agentes

Definidos en `.claude/agents/` (raíz del repo). Todos leen el vault antes de trabajar
y dejan lo aprendido al terminar.

| Agente | Para qué | Nota |
|---|---|---|
| `bibliotecario` | Lee y escribe la memoria en Obsidian: aprendizajes, decisiones, diario | [[Bibliotecario]] |
| `investigador` | Investiga opciones, datos y documentación antes de construir | [[Investigador]] |
| `revisor` | Revisa código y resultados, busca errores y registra lecciones | [[Revisor]] |
| `prospector` | Lista y enriquece inmobiliarias de Madrid; pruebas de tiempo de respuesta | [[Prospector]] |
| `constructor` | Demos por agencia e instalaciones reales (n8n + WhatsApp + calendario) | [[Constructor]] |
| `ventas` | Guiones, propuestas, contratos, RGPD y embudo (no envía nada) | [[Ventas]] |

## Ciclo de trabajo
1. **Leer memoria** → `bibliotecario` resume lo relevante del vault.
2. **Investigar** (si hace falta) → `investigador`.
3. **Construir** → Claude principal, con tools.
4. **Revisar** → `revisor`.
5. **Aprender** → `bibliotecario` guarda lecciones, decisiones y diario. Commit + push.
