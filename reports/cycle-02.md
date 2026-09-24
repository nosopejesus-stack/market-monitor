# Money Engine — Ciclo 02: validación y red team (2026-09-24)

## Resumen en una tabla

| pregunta | respuesta |
|---|---|
| **XAUUSD** | **NO EDGE. No operarla.** Verificado de forma independiente y con red team. El único sesgo encontrado favorece a la estrategia, así que la realidad es probablemente algo peor. |
| **Automatización de facturas (piloto de pago)** | **NO-GO.** Mercado saturado de competidores con las mismas capacidades, obligación de factura electrónica estructurada desde 2027-2028, sin diferenciación ni moat verificables, y economía negativa en modelo de servicio. |
| Evidencia débil eliminada | 6 cifras del ciclo 01 retiradas o corregidas; una ("23% usa IA") estaba **contradicha** por una fuente mejor. |
| Errores de implementación encontrados | 5 en el sistema de facturas, corregidos y con test. 1 sesgo de medición en XAUUSD (H1 optimista), cuantificado. |
| Acciones externas | **Ninguna.** No se ha contactado a nadie, no se ha publicado nada y no se ha gastado dinero (API de IA: 0 €). |
| Ingresos | 0 € (ACTUAL). |

Entregables:
- **A.** [`quant/REPORT_XAUUSD_VERIFY.md`](../quant/REPORT_XAUUSD_VERIFY.md), con tablas en [`quant/results/xau_verify.md`](../quant/results/xau_verify.md).
- **B.** [`research/invoice_evidence.md`](../research/invoice_evidence.md).
- **C.** [`experiments/EXP-002-test-plan.md`](../experiments/EXP-002-test-plan.md).
- **D.** [`research/pilot_economics.md`](../research/pilot_economics.md) y §D de este informe.
- **E.** [`research/competitors.md`](../research/competitors.md).
- **F.** [`outreach/gestorias.md`](../outreach/gestorias.md).
- **G.** §G de este informe.

---

## A. XAUUSD: conclusión final

**NO EDGE.** Detalle completo en el informe A. Lo esencial:

- **Implementación verificada.**
  - Una reimplementación independiente coincide al **100% operación a operación** (921 señales).
  - No hay look-ahead: 40/40 comprobaciones con datos truncados, y todas las entradas ocurren después del cierre de la vela.
  - Los límites de la vela diaria son correctos: M5 reproduce H1 exactamente.
- **La tasa de aciertos del 68,8% es la de un paseo aleatorio.** 40 caminos aleatorios sintéticos con la misma regla dan exactamente un 68,8%.
- **Ningún intento de rescatarla funciona:**
  - 125 variantes de parámetros: 0 con t > 2.
  - Walk-forward: −0,013R.
  - 18 combinaciones de costes: todas negativas.
  - Ningún periodo o régimen significativo.
- **Sesgo encontrado.** Con velas de 5 minutos, 2026 pasa de +0,040R (H1) a −0,021R (M5). El −0,020R publicado es probablemente optimista.
- **Datos falsos detectados.** Desde abril de 2025 el feed trae 132 días de fin de semana que un bróker MT5 no cotiza. Estaban excluidos; ahora está documentado y comprobado.
- **Pendiente de ti.** La especificación del símbolo en tu MT5 (dígitos, spread, swap, huso horario). No cambia el veredicto: probé el punto a 0,001, 0,01 y 0,10 $.

---

## B. Evidencia de mercado (facturas): qué queda en pie

| cifra | antes (ciclo 01) | ahora |
|---|---|---|
| Nº de despachos | "~60.000" | ~54.000 empresas en el CNAE 692 (SRC, Iberinform). Incluye auditores; los que llevan contabilidad de pymes son **UNK** |
| Adopción de IA | "23%" | **Retirada**: contradicha por el barómetro de Wolters Kluwer ("7 de cada 10 despachos ya usan IA") |
| Precio de implantación | "800-2.000 €" | **Retirada** (WEAK, montajes a medida) |
| Precio por factura | "0,20 €" | **ASM**: sin referencia verificable |
| Margen | "59%" | **Retirada**: el propio modelo, con supuestos realistas, da margen negativo en servicio |
| Precisión | "97%" | **UNK**: no medida. Además, 20-50 facturas no pueden demostrarla |

Hecho nuevo decisivo (**FACT**, BOE-A-2026-7295): el **Real Decreto 238/2026** obliga a emitir factura
electrónica estructurada entre empresas. Según fuentes secundarias concordantes, se espera que sea
obligatoria desde el **1 de octubre de 2027** para empresas de más de 8 M€ y desde el **1 de octubre de
2028** para el resto, 12 y 24 meses después de la orden ministerial.

---

## C. Plan de prueba con facturas reales

Diseñado y con herramienta de medición construida (`invoice_pipeline/evaluate.py`), **no ejecutado**:
- **Fase 1:** 60 documentos estratificados (incluye duplicados deliberados, no-facturas, escaneos malos, IGIC y suplidos). Se para si hay más de 3 falsos aceptados.
- **Fase 2:** 300 documentos para estimar con intervalos útiles.
- La métrica principal es el **falso aceptado**: una factura aceptada automáticamente con algún dato mal. La validación aritmética no puede detectar una lectura errónea pero coherente, y hay un test que lo demuestra.

---

## D. Economía del piloto

Fuente: [`research/pilot_economics.md`](../research/pilot_economics.md), generado por script. Todas las
entradas están etiquetadas.

**Coste total por factura aceptada** (1.000 facturas al mes; incluye IA, infraestructura, revisión humana, auditoría por muestreo, reprocesado y soporte):

| quién revisa | 5% excepciones | 15% excepciones | 30% excepciones |
|---|---|---|---|
| Tú (servicio, 40 €/h ASM) | 0,20-0,27 € | 0,38-0,61 € | 0,74-1,31 € |
| Personal de la gestoría (15 €/h SRC) | 0,14-0,16 € | 0,21-0,30 € | 0,36-0,57 € |

**La IA cuesta menos de 13 € al mes. El coste es la revisión humana y tu tiempo de soporte.**

**Contribución según el modelo de precio:**
- **Servicio (revisas tú):** negativa con cualquier precio de hasta 0,30 € por factura y con suscripciones de 99-349 €.
- **Software (revisa la gestoría):** unos 107 € al mes por cliente a 0,20 € por factura. Pero el cliente **solo ahorra** si meter una factura a mano le cuesta unos 3 minutos. Con 1 minuto pierde dinero con cualquier precio probado.

**Embudo** (todo ASM, 25 conversaciones):

| escenario | pilotos pagados | tus horas | CAC por piloto | retorno (modelo software) |
|---|---|---|---|---|
| bajo | 1 | 62 | ~2.490 € | ~23 meses |
| base | 2,8 | 75 | ~1.065 € | ~10 meses |
| alto | 6 | 100 | ~665 € | ~6 meses |

Con la factura electrónica recortando el volumen de PDF desde oct. 2027 y oct. 2028, un retorno de
10-23 meses deja muy poca vida útil al cliente.

**¿Qué significan los umbrales?**
- **2 pilotos de 25** → la conversión real está entre el **2,2% y el 25%** (IC 95%). Demuestra que alguien paga, no una tasa con la que se pueda planificar.
- **0 de 25** → sigue siendo compatible con hasta un 13%. Matar en 0/25 es una decisión de negocio, no una prueba estadística.
- **97% de precisión** → demostrarlo exige entre ~430 y 1.000 facturas. Con 20-50 solo se puede *refutar*.

**Experimento de precios, si algún día hubiera GO.** No declarar un precio. Primero, mirar los precios
publicados de Inmatic, AutoApunte, Contarapid y Dext (10 minutos tuyos; desde aquí están bloqueados).
Después, ofrecer por sorteo uno de tres formatos a cada gestoría calificada:
1. 0,15 € por factura;
2. 49 €/mes + 0,08 € por factura;
3. 149 €/mes hasta 1.500 facturas.

Registrar las aceptaciones y la pregunta de disposición a pagar ("¿a qué precio le parecería caro? ¿Y demasiado barato para fiarse?"). Con 25 conversaciones solo detectarías diferencias enormes entre formatos: es una exploración, no una medición.

---

## E. Competencia

Detalle en [`research/competitors.md`](../research/competitors.md). **Cada capacidad del sistema ya
existe en el mercado:**
- OCR;
- asientos contables automáticos;
- validación fiscal;
- duplicados y detección de anomalías;
- más de 20 integraciones con programas contables españoles;
- gestor documental;
- ayudas Kit Digital para comprarlo.

Quién lo ofrece: Inmatic, AutoApunte, Contarapid, Dext, AutoEntry, y de forma **nativa** a3innuva y Sage.
Inmatic ya vende también factura electrónica. **No encontré un hueco verificable y no me lo invento.**
**Moat:** ninguno alcanzable. Los costes de cambio protegen a quien ya está dentro.

---

## F. Paquete comercial

[`outreach/gestorias.md`](../outreach/gestorias.md). Incluye ICP, geografía, calificación, guion
telefónico, mensaje de LinkedIn, preguntas de descubrimiento, demo, objeciones y oferta de piloto.
**No se ha enviado nada.** Está reorientado a *descubrimiento* y marca como inciertos:
- **las llamadas comerciales** (art. 66.1.b de la Ley General de Telecomunicaciones y Circular 1/2023 de la AEPD);
- **el email en frío** (art. 21 LSSI);
- **el tratamiento de facturas** (art. 28 RGPD).

Recomiendo consulta legal antes de cualquier contacto.

---

## G. Decisión GO / NO-GO: piloto de pago de automatización de facturas

### **NO-GO.**

| criterio | evidencia | resultado |
|---|---|---|
| ¿Existe demanda pagada? | Sí: hay muchos proveedores cobrando por esto | ✔, pero ya está servida |
| ¿Hay un hueco que no cubran? | No encontrado (E) | ✘ |
| ¿Tenemos una ventaja verificable? | No: todas las capacidades existen; el coste de IA es igual para todos | ✘ |
| ¿Es sostenible el mercado? | Factura electrónica B2B estructurada obligatoria desde 2027 y 2028 (RD 238/2026) | ✘ en declive estructural para el OCR |
| ¿La economía funciona? | Servicio: negativa. Software: positiva solo si las excepciones son ≤15% y la entrada manual cuesta ~3 min; retorno de 10-23 meses | ✘ / frágil |
| ¿Hay moat alcanzable? | No | ✘ |
| ¿La tecnología está validada? | No medida con facturas reales | ? |

**Por qué no "GO condicionado".** Aunque la prueba técnica saliera perfecta, no cambiaría ninguna de las
cuatro razones de mercado (competencia, factura electrónica, ausencia de diferenciación y de moat).
Gastar tiempo o dinero en la fase 1 del plan C no reduce la incertidumbre que decide el caso.

**Qué sí puede merecer un Ciclo 03 (solo investigación, sin contactos):** la **transición a la factura
electrónica B2B**. Durante 2027-2029 cada gestoría tendrá que adaptar a todos sus clientes: formatos,
plataformas, estados de pago, convivencia de PDF y XML, e informes de morosidad. Es una fuente nueva
de dolor con fecha fija.
- Antes de proponerlo como oportunidad hay que verificar quién la está cubriendo ya: editores, plataformas privadas e Inmatic.
- También hay que confirmar la orden ministerial con fuente primaria.
- Hoy está en **UNVERIFIED**.

---

## Errores corregidos en este ciclo

| área | error | corrección |
|---|---|---|
| Facturas | IGIC, IPSI y facturas extranjeras siempre fallaban y además se escalaban a Opus (se pagaba dos veces para acabar en revisión) | Campo `tax_regime`; los regímenes no soportados van directos a revisión con el motivo |
| Facturas | Los suplidos (importes no sujetos) hacían fallar el cuadre del total | Campo `non_taxable_amount` incluido en el cuadre |
| Facturas | No había detección de duplicados | `invoice_pipeline/duplicates.py`, con coincidencia fuerte (NIF + número) y débil (NIF + fecha + total) |
| Facturas | Error en la normalización del número de factura ("F-2026/001" ≠ "f2026 0001") | Corregido con test |
| Facturas | Formatos no soportados (tiff, heic…) provocaban una excepción | Van a revisión con el motivo |
| Facturas | No había forma de medir falsos aceptados, precisión por campo ni coste total | `invoice_pipeline/evaluate.py`, con intervalos de Wilson y tamaño de muestra |
| XAUUSD | H1 sobreestima la estrategia en periodos muy volátiles | Cuantificado con M5 (V4); la conclusión se refuerza |
| XAUUSD | Velas de fin de semana del feed (desde abril de 2025) | Excluidas; ahora documentado y comprobado (V1) |
| Informe ciclo 01 | Seis cifras débiles o contradichas | Retiradas o reclasificadas (B) |

Tests: 29 pasan (quant, auditoría de energía, facturas).

## Aprobaciones pendientes (no voy a hacer nada de esto sin tu OK)
1. Ninguna para facturas: la decisión es NO-GO.
2. Si quieres el Ciclo 03 (investigar la transición a factura electrónica), dímelo. Es solo investigación.
3. Si aun así quieres validar la tecnología con tus propias facturas: aprobar la fase 1 del plan C (≤10 € de API, clave en variable de entorno, sin terceros).
4. XAUUSD: nada que aprobar. Si me pasas la especificación del símbolo, la dejo documentada.
