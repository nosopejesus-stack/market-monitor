# E. Panorama competitivo — automatización de facturas para gestorías (Ciclo 02)

Todo lo que sigue se ha visto a través de resultados de búsqueda. Las páginas de precios de los
competidores están bloqueadas desde este entorno, así que sus **precios son UNK** y ninguna de sus
afirmaciones de marketing se ha verificado.

## ¿Quién resuelve ya cada parte del problema?

| capacidad | ¿existe ya? | quién (según su propia web o reseñas) |
|---|---|---|
| OCR de facturas | **Sí, commodity** | Inmatic, AutoApunte, Contarapid, Dext, AutoEntry, Holded, Quipu, Billtonic, STEL Order, Matrix AutoForm, Lido… |
| Extracción contable (generar asientos) | **Sí** | Inmatic ("genera asientos contables en segundos"), AutoApunte (exporta a ERP), Contarapid (facturas emitidas y recibidas), a3innuva Contabilidad ("contabilización automática de facturas y asientos inteligentes"), Sage 50/200 con IA ("generación automática de asientos a partir de facturas escaneadas") |
| Validación fiscal / IVA | **Sí (declarada)** | AutoApunte ("validación fiscal") y otros. **No verificado** qué comprueban exactamente |
| Integración con software contable español | **Sí, amplia** | Inmatic: "integración directa con más de 20 programas contables", incluidos a3innuva y Reviso. AutoApunte: ContaSol, Sage 200, Holded, Quipu, a3asesor (fichero SUENLACE.DAT). Sage y a3 lo integran de forma nativa |
| Contabilidad automática | **Sí** | Inmatic ("automatiza hasta el 70% del trabajo contable"), a3innuva, Sage |
| Detección de anomalías / duplicados | **Sí** | Inmatic ("localiza facturas duplicadas"), a3innuva ("detecta duplicados y previene errores"), Sage 200 ("detección de anomalías en asientos") |
| Ingesta de documentos (portal, email, gestor documental) | **Sí** | Inmatic (gestor documental y portal de cliente), a3innuva (entorno colaborativo despacho-cliente) |
| Ayudas Kit Digital para comprarlo | **Sí** | Inmatic tiene página de Kit Digital para asesorías: parte del precio lo subvenciona el Estado |
| Factura electrónica B2B (lo que viene) | **Ya se vende** | Inmatic aparece en el marketplace de despachos como "Inmatic Factura Electrónica". Los editores contables (Sage, Wolters Kluwer) están obligados a soportarla |

## ¿Dónde está el hueco real?

Busqué uno concreto y verificable. Esto es lo que encontré:

| posible diferenciación | ¿es real? |
|---|---|
| "Validación determinista de NIF, IVA y totales" | **No.** Los competidores declaran validación fiscal y detección de duplicados. Mi implementación es honesta y está probada, pero no es única |
| "Precio por factura más bajo" | **No se puede afirmar.** No conozco sus precios, y los costes de IA (~0,01 €) son iguales para todos. El coste real es la revisión humana, que tienen todos |
| "IA más nueva" | **No es una ventaja duradera.** Cualquiera cambia de modelo en días |
| "Servicio (nosotros revisamos) en vez de software" | **Existe demanda de servicio**: las gestorías ya subcontratan y hay freelancers. Pero en mi modelo el servicio tiene **margen negativo** a precios de software (ver `pilot_economics.md`) |
| "Casos que los demás fallan" (IGIC, suplidos, facturas extranjeras, escaneos malos) | **UNK.** Sería el único hueco con sentido, pero hay que demostrarlo con facturas reales y comparando con un competidor |
| **Transición a factura electrónica B2B** (recibir XML, estados de pago, conciliación, la mezcla de PDF y XML durante 2027-2028) | **Posible hueco temporal, no verificado.** Los editores y plataformas ya se están posicionando (Inmatic lo vende). Merece un ciclo de investigación, no un piloto |

**Conclusión: no encuentro una diferenciación real y verificable para un producto de OCR o
contabilización de facturas.** No me la invento.

## ¿Hay moat?

| candidato | valoración |
|---|---|
| Integración en el flujo contable | Los competidores ya la tienen (más de 20 integraciones); llegar tarde no crea moat |
| Dataset propio de excepciones | Solo existiría tras procesar decenas de miles de facturas; los incumbentes ya lo acumulan |
| Aprendizaje por proveedor | Estándar en el sector (Dext, AutoEntry e Inmatic aprenden por proveedor) |
| Motor de validación | Reproducible en días; no es moat |
| Flujo de trabajo de la gestoría / costes de cambio | Juega **a favor de quien ya está dentro** (a3, Sage, Inmatic), no de un nuevo entrante |
| Conocimiento acumulado de errores | Moat real solo a escala; no se alcanza antes de que la factura electrónica reduzca el volumen de PDF |

**No hay un moat alcanzable: esto sería, como mucho, un envoltorio de OCR más.**

Fuentes (vistas en buscador):
[Inmatic](https://inmatic.ai/) · [Inmatic–a3innuva](https://inmatic.ai/compatibilidad/wolters-kluwer-a3innuva/) · [Inmatic Kit Digital](https://inmatic.ai/kit-digital) ·
[Inmatic Factura Electrónica (marketplace)](https://marketplace.innovaciondespachos.com/en/products/inmatic-factura-electronica) ·
[AutoApunte](https://autoapunte.com/precios) · [AutoApunte a3asesor](https://autoapunte.com/blog/automatizar-facturas-a3asesor) ·
[Contarapid](https://www.contarapid.com/contabilizar-automaticamente) · [a3innuva Contabilidad](https://www.wolterskluwer.com/en/solutions/a3innuva-contabilidad) ·
[Sage + IA (tuasesoriaia)](https://tuasesoriaia.com/ia-contabilidad/) · [Quipu: comparativa OCR](https://getquipu.com/blog/mejores-software-ocr-para-facturas/) ·
[Lido: OCR para despachos](https://www.lido.app/blog/best-ocr-software-for-accounting-firms)
