---
fecha: 2026-09-28
etiquetas: [entorno]
origen: proyecto market-monitor
---
# El contenedor cloud no tiene internet libre

- **Qué pasó:** Yahoo, NewsAPI, Twelve Data (API REST) y Gmail están bloqueados desde el contenedor de Claude Code en la nube.
- **Lección:** validar con tests y datos de ejemplo; los datos en vivo se piden por los conectores MCP (p. ej. Twelve Data); lo que necesita internet se ejecuta en GitHub Actions.
- **Cómo aplicarla:** no perder tiempo reintentando llamadas de red; si un dominio es imprescindible, pedir al usuario que lo añada en *Network access* del entorno.
