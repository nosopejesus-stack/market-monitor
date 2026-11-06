# Mi IA: tu asistente con memoria en Obsidian

Responde a tus preguntas usando **tu bóveda de Obsidian** (`../vault`) como memoria y aprende cuando le dices `/recordar`.
Funciona con un modelo **local y gratis** (Ollama) o con la API de Claude.
Plan y arquitectura: `vault/Mi IA/Mi IA - Plan.md`.

## Instalación en tu ordenador (Windows, macOS o Linux), unos 15 minutos

1. **Descarga el repo** (rama `claude/design-skills-setup`):
   ```bash
   git clone -b claude/design-skills-setup https://github.com/nosopejesus-stack/market-monitor.git
   cd market-monitor
   ```
2. **Obsidian:** instala Obsidian (obsidian.md) → *Open folder as vault* → elige la carpeta `vault`.
3. **Python 3.9+:** no necesita librerías extra.
4. **Ollama** (el "cerebro" local): instálalo desde ollama.com y descarga un modelo:
   ```bash
   ollama pull qwen3:8b      # recomendado: unos 5 GB, buen español. Alternativas: llama3.1:8b, gemma3:12b
   ```
5. **Habla con tu IA:**
   ```bash
   python mi-ia/mi_ia.py chat
   ```
   - Pregunta lo que quieras: busca en tus notas y responde citando `[[la nota]]`.
   - `/recordar Mi proveedor de hielo es X y entrega los martes` guarda una nota nueva en `vault/Memoria/Recuerdos`. Desde ese momento lo sabe, y tú también lo ves en Obsidian.
   - `salir` para terminar.

## Otros comandos
```bash
python mi-ia/mi_ia.py estado                        # cuántas notas conoce
python mi-ia/mi_ia.py buscar "leyes de escala"      # solo buscar, sin modelo
python mi-ia/mi_ia.py preguntar "¿qué es GRPO?"     # una pregunta suelta
python mi-ia/mi_ia.py --motor anthropic chat        # usar Claude (necesita ANTHROPIC_API_KEY)
```

## Configuración (variables de entorno)
| Variable | Por defecto | Para qué |
|---|---|---|
| `MI_IA_BOVEDA` | `../vault` | usar otra bóveda, por ejemplo tu panel de Obsidian ya existente |
| `MI_IA_MODELO` | `qwen3:8b` | el modelo de Ollama |
| `MI_IA_MOTOR` | `ollama` | `ollama`, `anthropic` o `ninguno` |
| `OLLAMA_HOST` | `http://localhost:11434` | si Ollama corre en otra máquina |

> **¿Ya tienes una bóveda de Obsidian?** Copia las carpetas de `vault/` dentro de la tuya, o apunta `MI_IA_BOVEDA` a la tuya.

## Cómo se probó (6 de noviembre de 2026)
- La búsqueda y la memoria (`buscar`, `recordar`) se probaron con las 23 notas de la bóveda.
- Prueba completa con un modelo real: `servidor_prueba.py` imita la API de Ollama con **Qwen2.5-0.5B-Instruct**.
  - Respondió bien a "¿cuántos tokens por parámetro recomienda Chinchilla?" (unos 20, sacado de las notas).
  - Respondió bien a la fecha de creación, aunque añadió un detalle inventado. Es normal con un modelo tan pequeño; con 8B es mucho más fiable.

## Próximos pasos
- **Búsqueda semántica** con *embeddings* (`ollama pull nomic-embed-text`) para encontrar por significado.
- **Afinar** un modelo pequeño con tus conversaciones (LoRA) para que hable a tu manera.
- **Darle manos:** conectar Agent Desktop y Playwright para que actúe en tu ordenador.
