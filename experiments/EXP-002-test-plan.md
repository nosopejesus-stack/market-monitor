# C. Plan de prueba con facturas reales — EXP-002 (Ciclo 02)

**Estado: preparado, NO ejecutado.** Necesita tu aprobación: supone obtener documentos de terceros y
gastar dinero en la API (≤10 €). Tras el Ciclo 02 la recomendación es **no ejecutarlo como piloto
comercial** (ver la decisión G en `reports/cycle-02.md`). Queda documentado por si decides validar la
tecnología de todos modos, o para reutilizarlo en otra vertical.

## 1. Objetivo

Medir, con facturas españolas reales, si el sistema:
1. extrae bien cada campo;
2. **no acepta automáticamente facturas con errores** (falsos aceptados);
3. envía a revisión una proporción asumible;
4. cuesta lo que dice el modelo económico.

**Qué NO puede probar:** un 97% de precisión con 20-50 facturas. Hacen falta ~430 facturas si la
precisión real es 98,5%, y ~1.000 si es 98% (`research/pilot_economics.md` §4).

## 2. Datos necesarios

| requisito | detalle |
|---|---|
| **Origen** | Opción A (preferida, **sin terceros**): tus propias facturas de proveedor y las de personas de confianza que te den su permiso por escrito. Opción B: una gestoría, **solo** con contrato de encargo de tratamiento (art. 28 RGPD) firmado antes de recibir nada |
| **Anonimización** | Las facturas de autónomos contienen datos personales (NIF y nombre de personas físicas). Pedir preferentemente facturas de sociedades. Si hay personas físicas: tratamiento como encargado, borrado al terminar y sin copias fuera de `samples/` (ignorado por git) |
| **Tamaño mínimo** | **Fase 1 (descarte rápido): 60 documentos.** Si hay más de 3 falsos aceptados → se para. **Fase 2 (estimación): 300 documentos** para un intervalo útil. 1.000 solo si se quiere afirmar ≥97% |
| **Estratificación de la fase 1** | 15 PDF nativos de grandes proveedores (luz, teléfono, combustible) · 10 PDF de pymes con plantillas distintas · 10 escaneados buenos · 8 fotos de móvil o escaneos malos · 5 con varios tipos de IVA · 3 con retención de IRPF · 3 con recargo de equivalencia · 2 con suplidos · 2 de inversión del sujeto pasivo o extranjeras · 2 IGIC (Canarias) · **2 duplicados deliberados** (misma factura dos veces, una con otro formato) · 2 documentos que no son factura (albarán, presupuesto) · 1 ticket o factura simplificada · 1 manuscrita, si existe |
| **Proveedores** | Al menos 30 emisores distintos en la fase 1 |
| **Verdad de terreno** | Un CSV (`ground_truth.csv`, formato en `invoice_pipeline/evaluate.py`) con lo que la gestoría **ya contabilizó**, revisado por una segunda persona. Si difieren, gana el documento original |
| **Etiqueta de categoría** | Columna `category` con el estrato (nativo, pyme, escaneo, foto, multi-IVA, etc.) para ver resultados por tipo |

## 3. Qué se mide

| métrica | definición | umbral de la fase 1 |
|---|---|---|
| Precisión por campo | Proveedor (similitud ≥0,85), NIF, nº de factura (normalizado), fecha, base, tipo(s) de IVA, cuota, total (±0,01 €) | Informe con conteos e IC al 95% por campo |
| Precisión por factura | Todos los campos clave correctos | Idem |
| **Falsos aceptados** | Aceptada automáticamente con algún campo clave incorrecto | **≤ 1 de 60** (si hay 2-3, investigar; si hay más de 3, parar) |
| Falsos negativos | Enviada a revisión estando todo correcto ("revisiones innecesarias") | Informativo: sube el coste, no el riesgo |
| Tasa de excepciones | Enviadas a revisión / total | Informativo; el modelo económico solo aguanta ≤15% |
| Duplicados | Detectados / reales; falsos positivos | 2/2 detectados, 0 falsos positivos |
| No-facturas | Albarán o presupuesto enviados a revisión, nunca aceptados | 2/2 |
| Tiempo de revisión humana | Segundos por excepción, **cronometrados** (columna `review_seconds`) | Informativo |
| Coste | Coste del modelo por documento, por factura aceptada y **total por factura aceptada** (modelo + revisión) | Comparar con `pilot_economics.md` |
| Latencia | p50 y p95 por documento | Informativo (<60 s es suficiente) |

## 4. Procedimiento

1. Aprobación tuya → clave `ANTHROPIC_API_KEY` en variable de entorno → presupuesto máximo **10 €** (60 documentos cuestan ~1 € estimado).
2. Colocar los documentos en `samples/fase1/` y la verdad de terreno en `samples/fase1/ground_truth.csv`.
3. `python -m invoice_pipeline.extract samples/fase1 runs/fase1.jsonl`
4. `python -m invoice_pipeline.evaluate runs/fase1.jsonl samples/fase1/ground_truth.csv --eur-per-hour 15`
5. Revisión manual de **cada** falso aceptado: ¿qué campo falló y por qué no lo detectó la validación?
6. Informe con conteos e intervalos, **nunca un porcentaje sin denominador**.
7. Borrar los documentos al terminar si son de terceros.

## 5. Criterio de lectura

- **Falsos aceptados >3 de 60 → la tecnología no está lista.** No hay piloto.
- Excepciones >30% → el coste por factura aceptada supera el valor para el cliente (D §2b).
- Si todo pasa, eso valida *la tecnología*, **no el negocio**: la competencia y la factura electrónica siguen ahí.

## 6. Limitaciones conocidas del sistema (del red team)

- La validación aritmética **no detecta errores de lectura coherentes**. Por ejemplo, leer todos los importes con el separador decimal equivocado cuadra igual. Por eso son obligatorios el muestreo de auditoría y la medición de falsos aceptados. Hay un test que lo demuestra.
- IGIC, IPSI y facturas extranjeras van a revisión humana por diseño: el validador del piloto no las comprueba.
- **No existe todavía un exportador** al formato de importación de ningún programa (a3 SUENLACE.DAT, ContaSol, Sage…). Los competidores ya los tienen.
