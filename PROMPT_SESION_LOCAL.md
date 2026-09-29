# Prompt para la sesión local (en tu PC)

Copia y pega esto en una sesión nueva de Claude Code con entorno **local** (tu ordenador), abierta en `C:\Users\nitrpc\dev`:

---

Hola. Continuamos el proyecto Arcend en mi PC. Habla siempre en español, ve al grano y trabaja siempre con tools.

1. Configura:
   - Si no existe `C:\Users\nitrpc\dev\market-monitor`, clónalo: `git clone https://github.com/nosopejesus-stack/market-monitor.git`. Si existe, haz `git fetch` y `git pull`.
   - Cambia a la rama `claude/tender-cannon-ui4ixl`.
   - Lee `CLAUDE.md`, `EMPIEZA_AQUI.md` y `proyecto-nuevo/arcend/PASO_A_PASO.md` y sigue sus reglas: Obsidian (`proyecto-nuevo/vault/`), agentes de `.claude/agents/`, revisar siempre y cero gasto.
   - Comprueba que hay Python 3.10 o superior (`py --version`). Si falta, dime cómo instalarlo; no instales nada de pago.
2. Revisa mi risk-scanner antiguo en `C:\Users\nitrpc\dev\risk-scanner` (tiene el perfil CLÍNICA y `modulos_osint_v3.py`). Compáralo con `proyecto-nuevo/arcend/blindaje/`. Si tiene algo útil que Blindaje no tenga, intégralo en Blindaje con tests, respetando el límite legal (solo información pública; nada de escaneo de puertos ni pruebas de vulnerabilidades).
3. Ejecuta los tests de Blindaje (`py -m unittest discover -s tests` dentro de `proyecto-nuevo/arcend/blindaje`).
4. Ejecuta el lote con internet real: `py lote.py ..\prospectos\clinicas.csv --contacto-nombre "<mi nombre>" --contacto-telefono "<mi móvil>"`.
5. Revisa a mano, con el agente revisor, cada hallazgo del `RESUMEN.csv` y de los `informe.json`. Quita cualquier falso positivo y corrige las reglas con su test. No quiero decirle nada falso a un médico.
6. Verifica en las webs oficiales lo que está marcado como SIN VERIFICAR:
   - el teléfono, la dirección y el titular de las clínicas prioritarias;
   - su inscripción en el Registro de centros sanitarios de la Comunidad de Madrid;
   - la fuente de las sanciones (90.001 € y el caso rebajado a 6.000 €) en el BOE, el BOCM o la sentencia.
   Actualiza el CSV y los documentos.
7. Dame la lista final de las 10 primeras clínicas a llamar, cada una con la frase exacta, el hallazgo principal y el teléfono verificado.
8. Guarda las lecciones en Obsidian con el bibliotecario y haz commit y push en la misma rama.

Resume al final en pocas líneas: qué cambió, qué verificaste y qué me toca hacer.

---
