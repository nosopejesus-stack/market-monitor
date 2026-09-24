# Flujo de entrega — memoria técnica exprés (EXP-006)

Objetivo: **≤180 min de trabajo humano por encargo** en el primer cliente y ≤100 min a partir del segundo encargo del mismo cliente (el perfil de empresa se reutiliza).

| paso | quién | tiempo humano | herramienta | salida |
|---|---|---|---|---|
| 0. Encargo aceptado y plazo pactado | tú | 5 min | email del cliente | confirmación por escrito (precio, plazo, lote) |
| 1. Descargar pliegos (PCAP + PPT + anexos) | tú o el script | 2 min | enlace de la Plataforma | PDFs en `jobs/<id>/pliegos/` |
| 2. Análisis de criterios | agente | 0 | `agent.analyze` + `validate_spec` | `criteria.json`. Si la validación falla → leer la cláusula (10 min) |
| 3. **Go/no-go de valor** | tú | 5 min | `criteria.json` | Si el juicio de valor pesa <15 puntos, avisar al cliente de que la memoria cuenta poco y ofrecer una versión corta o no hacerla |
| 4. Cuestionario de empresa | cliente + tú | 20 min | `tender_agent/intake.md` | `profile.json` |
| 5. Borrador | agente | 0 | `agent.draft` | `memoria.md` con marcadores pendientes |
| 6. QA automático | código | 0 | `python -m tender_agent.qa` | informe: bloquea CRITICAL/MAJOR |
| 7. Revisión humana | tú | 60-90 min | lectura contra el pliego | correcciones; sin CRITICAL; marcadores pendientes enviados al cliente |
| 8. Cliente completa datos | cliente | — | — | marcadores rellenados |
| 9. QA final y entrega (Word/PDF con el formato del pliego) | tú | 20 min | QA + maquetación | memoria entregada; factura |
| 10. Una ronda de cambios | tú | 20-30 min | — | versión final |
| 11. Registro | tú | 3 min | `experiments/EXP-006-jobs.csv` | minutos, coste de IA, pago, resultado |

**Escalado a humano** (siempre): pliego sin criterios claros, validación de puntos fallida, lotes con memorias distintas, requisitos de formato no estándar, cualquier CRITICAL del QA.

**Qué nunca hace el sistema:** inventar datos de la empresa, prometer puntuación, presentar la oferta en nombre del cliente ni firmar nada.
