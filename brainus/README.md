# 🧠 Brainus: tu IA personal, con memoria en Obsidian, que aprende de lo bueno y lo malo

```
              ┌───────────────────── TU PC (funciona sin internet y sin Claude) ─────────────────────┐
  Tú ──▶ icono "Brainus" → navegador http://localhost:8765   (o: python brainus/brainus.py chat)
              │
              ▼
         brainus.py ──1. busca──▶ Bóveda de Obsidian (vault/)
              │                    ├─ todo lo aprendido: CS336, herramientas, tus proyectos
              │                    ├─ Memoria/Lecciones: Reglas Hacer / No hacer ◀── 👍 👎 /hacer /evitar
              │                    ├─ Memoria/Recuerdos ◀── /recordar
              │                    └─ Memoria/Sesiones ◀── Claude Code apunta lo bueno y lo malo de cada sesión
              │ 2. reglas + memoria + pregunta
              ▼
         CEREBRO (eliges):
              ├─ ollama ...... el modelo abierto más potente que aguanta tu PC (lo elige el instalador)
              ├─ propia ...... la red neuronal de Brainus, creada DESDE CERO como en CS336
              └─ anthropic ... Claude por API (opcional, de pago)
              └──────────────────────────────────────────────────────────────────────────────────────┘
```

## Instalar (Windows, una vez)
1. Descarga el repo, rama `claude/design-skills-setup`:
   `git clone -b claude/design-skills-setup https://github.com/nosopejesus-stack/market-monitor.git`
   (o en GitHub: *Code* → *Download ZIP*).
2. Clic derecho en `brainus\instalar_windows.ps1` → **Ejecutar con PowerShell**. El instalador:
   - instala Python, Git, Ollama y Obsidian;
   - **mira tu RAM y tu tarjeta gráfica y elige el cerebro más potente que tu PC puede mover**:

     | Tu PC | Cerebro |
     |---|---|
     | GPU de 24 GB | `qwen3:32b` |
     | GPU de 16 GB | `qwen3:14b` |
     | 32 GB de RAM | `qwen3:30b-a3b` (MoE: listo y rápido incluso sin GPU) |
     | 16 GB de RAM o GPU de 8 GB | `qwen3:8b` |
     | menos | `qwen3:4b` |

   - descarga el modelo de búsqueda por significado (`nomic-embed-text`);
   - instala PyTorch para la red propia (versión CUDA si tienes GPU NVIDIA);
   - configura Claude Code para que **siempre** apunte en tu bóveda lo bueno y lo malo;
   - crea el icono **Brainus** en el escritorio.
3. Obsidian → *Open folder as vault* → carpeta `vault`.

**macOS / Linux:** instala Ollama y Obsidian. Después:
```bash
ollama pull qwen3:8b && ollama pull nomic-embed-text
pip install torch numpy regex
./brainus/brainus.sh
```

## Usar (cada día, con o sin Claude)
Doble clic en **Brainus**, o `python brainus/brainus.py chat`.

| Escribe | Qué pasa |
|---|---|
| una pregunta | busca en tu bóveda, cumple tus reglas y responde citando `[[la nota]]` |
| `/recordar …` | lo guarda en `Memoria/Recuerdos`; desde ese momento lo sabe |
| 👍 o `/bien` | guarda la respuesta como buen ejemplo |
| 👎 o `/mal <por qué>` | lo guarda como error **y crea una regla en "No hacer"** |
| `/hacer …` / `/evitar …` | añade una regla |
| `/reglas` | lo que ha aprendido |

**Sin Claude:** Brainus funciona sola, sin internet.
**Con Claude:** cada vez que uses Claude Code, escribirá en tu bóveda lo aprendido. Brainus lo lee en la siguiente pregunta.

## La red neuronal de Brainus (`red_neuronal/`)
Escrita **100 % desde cero** siguiendo las especificaciones de CS336 (tarea 1). Sin `nn.Linear`, sin el softmax ni la atención de PyTorch; todo programado a mano:

| Pieza | Archivo |
|---|---|
| Tokenizador BPE de bytes con tokens especiales (`<\|endoftext\|>`), entrenamiento incremental | `tokenizador.py` |
| Linear, Embedding (inicialización normal truncada), RMSNorm, SiLU, SwiGLU | `modelo.py` |
| softmax estable, atención escalada con máscara causal, RoPE, atención multi-cabeza | `modelo.py` |
| Bloque Transformer pre-norm, TransformerLM, generación con temperatura y **top-p** | `modelo.py` |
| cross-entropy estable, **AdamW**, LR coseno con calentamiento, recorte de gradientes | `entrenamiento.py` |
| lotes aleatorios, checkpoints (modelo + optimizador + iteración) | `entrenamiento.py` |

**Verificada:** `python -m pytest brainus/red_neuronal/test_red.py` lanza **23 tests**. Cada pieza se compara con la referencia oficial de PyTorch (por ejemplo, mi AdamW frente a `torch.optim.AdamW` durante 25 pasos), y todos pasan.

> **Sobre la tarea oficial:** el repo del curso pide a las IAs no resolver las tareas por los alumnos. Por eso Brainus es un proyecto independiente y **no** se ha conectado a los tests de `stanford-cs336/assignment1-basics`. Si quieres hacer la tarea tú, Claude te hace de tutor.

### Entrenar y hacerla crecer
```bash
python brainus/red_neuronal/generar.py "La ciudad de Madrid"                # hazla escribir
python brainus/red_neuronal/entrenar.py --continuar                          # aprende tus notas nuevas (3 min)
python brainus/red_neuronal/descargar_corpus.py --mb 500                     # más español (Wikipedia)
python brainus/red_neuronal/entrenar.py --perfil medio --minutos 120         # ~45M parámetros
python brainus/red_neuronal/entrenar.py --perfil potente --minutos 480       # ~125M (tamaño GPT-2), con GPU
python brainus/brainus.py --motor propia chat                                # usarla como cerebro
```
- Siempre se guarda **la mejor versión** (validación), así que re-entrenar no la estropea.
- El historial de entrenamientos queda en `red_neuronal/pesos/historial.json`.

**Siendo claros:** la red que viene entrenada (14M parámetros, 40 minutos de CPU) escribe español con tu vocabulario, pero **no razona**. Para conversar de verdad, el cerebro es el de Ollama. Tu red es el proyecto que puedes ir haciendo crecer: con una GPU, el perfil `potente` y unos cientos de MB de texto se acerca a un GPT-2.

## Configuración
`brainus/config.json` lo escribe el instalador. Cualquier valor se puede cambiar con variables de entorno:

| Variable | Para qué |
|---|---|
| `BRAINUS_MODELO` | el cerebro de Ollama (`qwen3:14b`, `gemma3:12b`…) |
| `BRAINUS_MOTOR` | `ollama`, `propia`, `anthropic` o `ninguno` |
| `BRAINUS_BOVEDA` | usar otra bóveda (por ejemplo tu panel de Obsidian) |
| `BRAINUS_EMBED` | el modelo de búsqueda por significado |

## Qué está probado
- **En Linux (servidor de Claude):**
  - los 23 tests de la red;
  - el entrenamiento completo y la generación;
  - el asistente: búsqueda, reglas, 👍/👎, recuerdos y la web, con un modelo real pequeño a través de `servidor_prueba.py`.
- **Sin probar en Windows:** `instalar_windows.ps1` y `Brainus.bat`. Si algo falla, pásale el error a Claude.
