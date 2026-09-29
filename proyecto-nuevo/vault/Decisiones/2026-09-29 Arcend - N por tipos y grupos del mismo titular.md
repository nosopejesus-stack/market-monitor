---
fecha: 2026-09-29
estado: aceptada
---
# Arcend - N por tipos y grupos del mismo titular

- **Contexto:** en el lote real (48 webs) `n_puntos_norma` contaba frases distintas y llegaba a cifras infladas (IME, N = 22, por un menú repetido en 15 páginas y cada frase con bótox). Además, la verificación en el Registro de centros sanitarios de la CAM mostró que ARC-001, 006 y 013 tienen el mismo titular (Elenpa Médico Estético S.L.). Ver [[Aprendizajes/2026-09-29 N por tipos de infracción, no por frases]] y [[Aprendizajes/2026-09-29 Verificar clínicas en el Registro de centros sanitarios de la CAM]].
- **Opciones consideradas:**
  - N: (a) frases distintas (lo que hacía el código); (b) páginas con infracción; (c) tipos de infracción distintos con norma concreta (lo que ya decía `PASO_A_PASO.md`).
  - Grupos: (a) llamar a cada clínica como independiente; (b) excluirlos; (c) marcarlos y aclarar el grupo antes o en la llamada.
- **Decisión:**
  1. **N = número de tipos de infracción distintos con norma concreta** (hoy: publicidad de toxina, promoción sobre acto médico). Las frases son evidencia, no puntos. Sustituye el criterio "deduplicados por regla y frase" de [[Decisiones/2026-09-28 Arcend - Informe previo y N calculado por la herramienta]].
  2. **Las clínicas del mismo titular en el Registro no se llaman como clínica independiente sin aclararlo.** Se marcan `cadena = "revisar"` en `prospectos/clinicas.csv` (hoy 001, 002, 006, 010, 013, 025, 037) y se aclara quién decide antes de ofrecer nada.
- **Consecuencias:** N baja y es defendible delante de un médico (cada punto es un tipo con su norma y su evidencia más concreta). Un grupo cuenta como una sola cuenta comercial con varias sedes; la oferta por sede queda por decidir con el usuario (SIN DECIDIR). Relacionado: [[Aprendizajes/2026-09-28 Prospección - comprobar direcciones y distinguir cadenas]].
