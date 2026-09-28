---
fecha: 2026-09-28
estado: aceptada
---
# Arcend - Informe previo y N calculado por la herramienta

- **Contexto:** la venta de Blindaje (ver [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]]) se apoya en un informe hecho antes de llamar y en la frase "hay N puntos que la normativa de publicidad sanitaria no permite". El informe completo con textos corregidos es el entregable de 390 €.
- **Opciones consideradas:** (a) enseñar el informe completo en la reunión; (b) informe previo de una página sin textos corregidos; (c) contar N a mano; (d) que N lo calcule la herramienta.
- **Decisión:** (b) + (d). `blindaje.py --previo` genera `informe_previo.html` (puntos, norma, gravedad y oferta; sin textos corregidos). El informe completo (sin `--previo`) solo se genera tras el cobro, entrega en 5 días hábiles. N = `n_puntos_norma` de `informe.json`: ALTA/MEDIA sin nada SIN VERIFICAR, deduplicados por regla y frase. Si N = 0, no se usa el anzuelo.
- **Consecuencias:** N es prudente (a 2026-09-28 solo cuentan toxina y promociones porque el resto de normas están SIN VERIFICAR); subirá al verificar normas en BOE/BOCM. Cada hallazgo del previo se revisa a mano antes de enseñarlo (cero falsos positivos delante de un médico). Lecciones: [[Aprendizajes/2026-09-28 Cifra comercial calculada por la herramienta]], [[Aprendizajes/2026-09-28 Documento previo a la venta sin entregable de pago]].
