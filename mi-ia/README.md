# 🧠 Mi IA: tu IA personal, con memoria en Obsidian, que aprende de lo bueno y lo malo

```
                 ┌────────────── TU PC (funciona sin internet) ──────────────┐
  Tú ──▶ navegador http://localhost:8765  o  terminal (chat)
              │
              ▼
          mi_ia.py ──1. busca──▶ Bóveda de Obsidian (vault/)
              │                   ├─ notas, cursos (CS336), proyectos
              │                   ├─ Memoria/Lecciones: Reglas Hacer / No hacer  ◀─ /bien /mal /hacer /evitar
              │                   ├─ Memoria/Conversaciones (cada charla queda guardada)
              │                   └─ Memoria/Sesiones  ◀── Claude Code escribe aquí al terminar cada tarea
              │ 2. reglas + memoria + pregunta
              ▼
          CEREBRO (eliges uno):
              ├─ Ollama + qwen3:8b ........ red neuronal abierta de 8.000 millones de parámetros (recomendado)
              ├─ red_neuronal/ ............ TU red, creada desde cero como en CS336 (experimental)
              └─ API de Claude ............ la más lista; de pago y necesita internet
                 └──────────────────────────────────────────────────────────────┘
```

## 1. Instalar (una vez)

### Windows (lo más fácil)
1. Descarga el repo: `git clone -b claude/design-skills-setup https://github.com/nosopejesus-stack/market-monitor.git`
   (o desde GitHub: botón *Code* → *Download ZIP*, eligiendo la rama `claude/design-skills-setup`).
2. Clic derecho en `mi-ia\instalar_windows.ps1` → **Ejecutar con PowerShell**. El instalador:
   - instala Python, Git, **Ollama** y **Obsidian**;
   - descarga los modelos `qwen3:8b` y `nomic-embed-text` (unos 5 GB);
   - instala PyTorch para tu red propia;
   - crea el acceso directo **"Mi IA"** en el escritorio;
   - configura Claude Code para que guarde lo aprendido en tu bóveda.
3. En Obsidian: **Open folder as vault** → carpeta `vault`.

### macOS / Linux
```bash
git clone -b claude/design-skills-setup https://github.com/nosopejesus-stack/market-monitor.git && cd market-monitor
# Instala Ollama (ollama.com) y Obsidian (obsidian.md), luego:
ollama pull qwen3:8b && ollama pull nomic-embed-text
pip install torch regex          # solo para la red propia
cat mi-ia/claude_global_CLAUDE.md | sed "s#{{BOVEDA}}#$PWD/vault#" >> ~/.claude/CLAUDE.md
```

## 2. Usarla (cada día)
- **Windows:** doble clic en **"Mi IA"** del escritorio (o en `mi-ia\MiIA.bat`). Se abre el navegador.
- **macOS/Linux:** `./mi-ia/mi-ia.sh`
- **Terminal:** `python mi-ia/mi_ia.py chat`

| Escribe | Qué pasa |
|---|---|
| una pregunta | busca en tu bóveda, cumple tus reglas y responde citando `[[la nota]]` |
| `/recordar Mi proveedor de hielo entrega los martes` | lo guarda en `Memoria/Recuerdos` y desde ese momento lo sabe |
| 👍 o `/bien` | guarda la respuesta como buen ejemplo |
| 👎 o `/mal no me inventes precios` | lo guarda como error **y crea una regla en "No hacer"** |
| `/hacer responde con listas cortas` | nueva regla en "Hacer" |
| `/evitar usar inglés` | nueva regla en "No hacer" |
| `/reglas` | muestra lo que ha aprendido |

## 3. Cómo aprende cada vez que usas Claude
- El instalador añade a tu `~/.claude/CLAUDE.md` unas instrucciones. Con ellas, **Claude Code, en cualquier proyecto**:
  - lee tus reglas al empezar;
  - al terminar cada tarea, escribe en tu bóveda lo que salió bien (Hacer), lo que salió mal (No hacer) y un resumen de la sesión.
- Mi IA lee esas notas en la siguiente pregunta. **Lo que aprende Claude contigo, lo sabe tu IA.**
- Tus 👍 y 👎 quedan también en `mi-ia/datos/preferencias.jsonl`, en el mismo formato que se usa para afinar modelos con **DPO**. Con el tiempo servirán para entrenar tu modelo con tus gustos (ver la nota "Clase 15 - Mid y post-training").

## 4. Tu red neuronal propia (`red_neuronal/`)
Un Transformer construido **desde cero** con lo aprendido en CS336:
- tokenizador BPE;
- RMSNorm, RoPE, SwiGLU y atención causal;
- AdamW con warmup y coseno.

Se entrenó igual que los modelos grandes, en dos fases:
1. **Preentrenamiento** con 12 MB de Wikipedia en español.
2. **Mid-training** con tu bóveda.

```bash
python mi-ia/red_neuronal/generar.py "La tokenización"            # hazla escribir
python mi-ia/red_neuronal/entrenar.py --continuar --minutos 10    # que aprenda tus notas nuevas
python mi-ia/mi_ia.py --motor propia chat                         # usarla como cerebro (experimental)
```

**Siendo honestos:** tiene unos 5 millones de parámetros. Escribe con el estilo y las palabras de tus notas, pero **no razona**. Por eso el cerebro diario es `qwen3:8b`, que tiene 1600 veces más parámetros. Tu red es la demostración de que sabes crear una IA desde cero y la base para crecer: con una GPU y más datos puedes entrenarla más grande.

## 5. Configuración
| Variable | Por defecto | Para qué |
|---|---|---|
| `MI_IA_BOVEDA` | `vault/` | apuntar a otra bóveda (por ejemplo tu panel de Obsidian) |
| `MI_IA_MODELO` | `qwen3:8b` | otro modelo de Ollama (`gemma3:12b`, `llama3.1:8b`…) |
| `MI_IA_EMBED` | `nomic-embed-text` | el modelo para buscar por significado |
| `MI_IA_MOTOR` | `ollama` | `ollama`, `anthropic`, `propia` o `ninguno` |

## Probado (6 de noviembre de 2026, en un servidor Linux)
- La búsqueda híbrida, las reglas, `/recordar`, `/bien`, `/mal`, `/hacer` y `/evitar`, y la página web (probada con Playwright).
- Las respuestas con un modelo real se probaron con `servidor_prueba.py`, que imita a Ollama usando Qwen2.5-0.5B.
- La red propia se entrenó en este servidor (solo CPU) y sus pesos van incluidos en `red_neuronal/pesos/`.
- **No se ha podido probar en Windows:** el instalador `.ps1` y el `.bat` están escritos con cuidado, pero si algo falla, dile a Claude qué error sale.
