# Inicio

Memoria compartida del proyecto entre tú y los agentes. **Todo lo importante vive aquí.**

## Cómo se usa
1. Antes de cualquier tarea, los agentes leen esta nota, [[Aprendizajes/Índice de aprendizajes]] y las [[Decisiones/Índice de decisiones|decisiones]].
2. Al terminar, el agente [[Agentes/Bibliotecario|bibliotecario]] guarda lo aprendido, las decisiones y la entrada del [[Diario]].
3. Tú puedes editar cualquier nota desde Obsidian: los agentes la leerán en la próxima sesión.

## Estado del proyecto
- **Nombre:** _(pendiente)_
- **Objetivo:** _(pendiente — definir en [[Proyecto/Visión]])_
- **Fase actual:** Arcend · validación por teléfono (primeras 40 llamadas)
- **Infraestructura:** stack en `infra/` (n8n, Chatwoot, Ollama, Umami, ComfyUI + Postgres 17/pgvector + Redis) probado en el contenedor cloud. Preparación del servidor (solo futuro, cero gasto) en `infra/server/` (endurecimiento, firewall DOCKER-USER, backups diarios con restauración probada, `GUIA.md`), probada en simulación; destino: Hetzner Cloud (UE) con Coolify. Públicos con HTTPS: n8n, Chatwoot, Umami; el resto privado (panel de Coolify por túnel SSH). Claude usará los servicios a través del MCP de instancia de n8n. Ver [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]] y [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]].
- **Arcend (proyecto principal):** Blindaje continuo para clínicas de medicina estética independientes de Madrid: informe 390 € + vigilancia 190 €/mes, captación por teléfono con el informe hecho; Atención solo como subida. 10k en 30 días no es realista. Ver [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]] y [[Proyecto/Arcend - clínicas estéticas Madrid]].
- **Blindaje (listo):** herramienta `proyecto-nuevo/arcend/blindaje/` (79 tests, `--previo`, `n_puntos_norma`), kit de ventas en `arcend/ventas/`, 49 clínicas en `arcend/prospectos/clinicas.csv` (SIN VERIFICAR) y guía `arcend/PASO_A_PASO.md`. Ver [[Decisiones/2026-09-28 Arcend - Informe previo y N calculado por la herramienta]].
- **Pendiente del usuario (Arcend):** empezar por `EMPIEZA_AQUI.md` (raíz). Día 0-1 de `PASO_A_PASO.md` (instalar Python, generar los informes previos en lote con `blindaje/lote.py` el Día 1, verificar teléfono, dirección e inscripción de cada clínica) y las primeras 40 llamadas.
- **Negocio:** respuesta inmediata a leads para inmobiliarias de Madrid (objetivo: 10.000 €). Plan, lista de 111 agencias (54 prospectables, SIN VERIFICAR), kit de ventas, demo e investigación listos en `proyecto-nuevo/negocio/`, revisados dos veces. Promesa: respuesta automática en minutos (objetivo < 2 min, se mide en el piloto) por email con botón wa.me; asistente automático identificado; servidor y costes de Meta a cargo del cliente. Fase: validación (criterio de muerte: 25 conversaciones con decisores y 0 segundas reuniones). Ver [[Decisiones/2026-09-28 Negocio respuesta inmediata a leads inmobiliarios]].
- **Pendiente del usuario (negocio):** validar fuera la investigación de WhatsApp/Meta/Ley de IA; verificar agencias y sacar decisores desde su PC; decidir el alta de autónomo antes del primer contrato (~80 €/mes, SIN VERIFICAR); consultas de prueba, visitas, firma y cobro.
- **Pendiente del usuario (infra):** contratar el servidor en Hetzner, llave SSH, dominios, cuentas admin (con 2FA) y token MCP de n8n.

## Mapa
- [[Proyecto/Visión]] — qué construimos y para quién
- [[Aprendizajes/Índice de aprendizajes]] — lo que ya sabemos (no repetir errores)
- [[Decisiones/Índice de decisiones]] — por qué hicimos las cosas así
- [[Agentes/Equipo de agentes]] — quién hace qué
