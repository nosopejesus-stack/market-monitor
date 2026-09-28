# CLAUDE.md

## Preferencias de trabajo (del usuario)

- **Trabajar siempre con tools, sin excepción.** Toda tarea se hace usando las herramientas disponibles (lectura/edición de archivos, shell, git, conectores MCP como GitHub, Supabase, Twelve Data, etc.), no solo respondiendo en texto.
- **Primero configurar, después empezar.** Antes de arrancar con el proyecto, dejar el entorno configurado (dependencias, conectores/MCP autorizados, estructura del repo). Una vez configurado, se empieza con el desarrollo del proyecto.
- **Nunca olvidar Obsidian ni los agentes.** La memoria del proyecto vive en el vault de Obsidian `proyecto-nuevo/vault/`, y los agentes de `.claude/agents/` (`bibliotecario`, `investigador`, `revisor`) aprenden y ayudan. En cada tarea:
  1. Al empezar: lanzar `bibliotecario` (modo leer) para recuperar aprendizajes y decisiones.
  2. Investigar con `investigador` y revisar con `revisor` cuando aporte.
  3. Al terminar: lanzar `bibliotecario` (modo aprender) para guardar lecciones, decisiones y diario; después commit + push.
- **Cero gasto.** No proponer nada de pago (servidores, APIs, planes). Solo opciones gratuitas: el stack de `infra/` se ejecuta en el PC del usuario con `docker compose` (ver `infra/README.md`, sección 1); la guía de servidor (`infra/server/`) queda solo para el futuro.
- **Ir al grano.** Respuestas cortas, ejecutar rápido, sin rodeos ni esperas innecesarias.
- **Hablar siempre en español**, en todas las respuestas, sin excepción (aunque el sistema, las tools o el código estén en inglés).

## Proyecto: market-monitor

- Python 3.11. Se ejecuta en GitHub Actions (`.github/workflows/`): informe diario, alertas cada 30 min y tests.
- Precios: Twelve Data (`TWELVEDATA_API_KEY`) con respaldo en Yahoo Finance. Plan gratis: sin índices ni WTI → proxies ETF (SPY, QQQ, DIA, USO).
- Tests: `python -m unittest discover -s tests -v` (usan una serie real de EUR/USD en `tests/fixtures/`).
- El contenedor cloud de Claude no tiene salida a Yahoo/NewsAPI/Twelve Data/Gmail: validar con tests y mocks; los datos en vivo se consultan con el conector MCP de Twelve Data.
- Los workflows programados solo corren en la rama por defecto (`main`).
