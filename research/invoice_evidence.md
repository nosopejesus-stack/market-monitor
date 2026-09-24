# B. Evidencia de mercado — automatización de facturas para gestorías (Ciclo 02)

Clasificación:
- **FACT**: publicado por una fuente primaria (BOE, organismo oficial, convenio).
- **SRC**: estimación respaldada por una fuente secundaria identificable.
- **WEAK**: blog de un proveedor o dato sin metodología.
- **ASM**: supuesto.
- **UNK**: desconocido.

Muchas páginas primarias (BOE, AEAT, Wolters Kluwer, ftmo.com, inmatic.ai, autoapunte.com…) están
**bloqueadas desde este entorno**. Solo he podido leer los resúmenes del buscador, así que las marco
como "vista en buscador".

## 1. Revisión de las cifras del ciclo 01

| cifra del ciclo 01 | clasificación ahora | qué dice la mejor fuente disponible | decisión |
|---|---|---|---|
| "~60.000 asesorías" | **SRC** (dato distinto) | Iberinform cifra el CNAE 692 (contabilidad, auditoría y asesoría fiscal) en **53.998 empresas**. Incluye auditores y asesores fiscales que no llevan contabilidad. El INE publica tablas oficiales del grupo 692 (no pude abrirlas) | Sustituir por "~54.000 empresas en CNAE 692 (SRC); el número que llevan contabilidad de pymes es **UNK**" |
| "77% con menos de 10 empleados" | **WEAK** | Solo aparece en un resumen de prensa (Channel Partner) | Retirada hasta ver las tablas de tramos de ocupación del INE |
| "23% usa IA" | **Contradicha → retirada** | El barómetro de Wolters Kluwer ("Barómetro Asesoría 2026") dice que **7 de cada 10 despachos ya usan IA** y que el uso creció un 66% en un año (vista en buscador). La cifra del 23% venía de un blog que citaba al CGE sin enlace | **Eliminada.** Implica que el mercado ya está adoptando herramientas: más competencia, no menos |
| "Implantaciones de 800-2.000 €" | **WEAK** | Blogs de proveedores de automatización (tuasesoriaia.com, copilotgestoria.com). Se refiere a montajes a medida con n8n/Make, no a software de facturas | Retirada como precio de referencia |
| "0,20 € por factura" | **ASM** | No hay referencia de precio verificable. Las páginas de precios de Inmatic, AutoApunte y Contarapid están bloqueadas aquí | Hipótesis a testar, no un precio |
| "59% de margen" | **Refutada por el propio modelo** | Suponía un 3% de excepciones y 2 min de revisión. Con un 15% de excepciones y 3 min, el modelo de servicio tiene **contribución negativa** con cualquier precio ≤0,30 € (ver `pilot_economics.md`) | **Eliminada** |
| "97% de precisión" | **UNK** | Nunca se ha medido con facturas reales. Además, demostrar ≥97% con un 95% de confianza requiere entre ~430 y 1.000 facturas (si la precisión real es 98,5% o 98%) | Solo puede afirmarse tras medirlo |
| Coste de IA "≈0,012 € por factura" | **SRC + ASM** | Precios de lista de los modelos (FACT) × tokens por página (ASM). Sin medición real | Mantener como estimación; se mide en la prueba |

## 2. Hechos nuevos que cambian el caso

| hecho | clasificación | fuente | implicación |
|---|---|---|---|
| **Factura electrónica B2B obligatoria.** Real Decreto 238/2026, de 25 de marzo (BOE-A-2026-7295), publicado el 31 de marzo de 2026. Formatos estructurados (UBL, CII, EDIFACT o Facturae; modelo semántico EN 16931), plataformas privadas más una solución pública de la AEAT, y comunicación del estado de la factura (aceptación, rechazo, pago) | **FACT** (referencia BOE vista en buscador; varias fuentes coinciden) | [BOE-A-2026-7295](https://www.boe.es/buscar/act.php?id=BOE-A-2026-7295) · [AEAT, nota 31/03/2026](https://sede.agenciatributaria.gob.es/Sede/todas-noticias/2026/marzo/31/facturacion-electronica-obligatoria.html) · [Forvis Mazars](https://www.forvismazars.com/es/es/insights/alertas/alertas-fiscales/rd-238-2026-facturacion-electronica) | **La amenaza estructural más importante.** Cuando las facturas lleguen como datos estructurados, extraerlas de un PDF deja de ser necesario |
| **Calendario.** 12 meses desde la orden ministerial para empresas con más de 8 M€ de facturación y 24 meses para el resto. Fechas esperadas: **1 oct 2027 y 1 oct 2028**. Un PDF puede acompañar a la factura estructurada durante los primeros 12 meses. La orden ministerial estaba en proyecto en abril de 2026 | **SRC** (varias fuentes secundarias coinciden; el proyecto de orden es de Hacienda) | [proyecto de OM (hacienda.gob.es)](https://www.hacienda.gob.es/sgt/normativadoctrina/proyectos/16042026-proyecto-pom-factura-electronica.pdf) · [pymesyautonomos.com](https://www.pymesyautonomos.com/actualidad/hacienda-fija-calendario-definitivo-autonomos-tienen-fecha-para-implantar-factura-electronica-obligatoria-excepciones) · [lealtadis.es](https://www.lealtadis.es/factura-electronica-b2b-estados-pago-pymes/) | Las facturas de grandes proveedores (luz, teléfono, combustible, mayoristas) llegarían estructuradas desde oct. 2027. Son una parte grande del volumen de una pyme (**ASM**). La ventana de un producto de OCR puro es de unos 2-3 años y decreciente |
| Verifactu obligatorio desde el 1 ene 2027 (sociedades) y el 1 jul 2027 (autónomos) | **SRC** (ciclo 01) | [ECIJA](https://advisory.ecija.com/verifactu-2027/) | Todos los emisores pasan a software de facturación; eso acelera la emisión estructurada |
| **Coste laboral.** El IX Convenio estatal de gestorías administrativas (2024-2026) fija una jornada de 1.780 h/año; titulado superior 26.360 €/año y titulado medio 24.850 € en 2026 | **FACT** (convenio en BOE-A-2024-17575; cifras vistas en buscador) | [Iberley](https://www.iberley.es/noticias/publicado-ix-convenio-colectivo-estatal-gestorias-administrativas-33853) · [WageIndicator](https://wageindicator.org/es-es/trabajo-en-espana/convenios-colectivos/ix-convenio-colectivo-estatal-de-gestorias-administrativas-2024-2026/) | Coste cargado de un administrativo ≈ **15 €/h** (SRC: salario ~20.000 € (ASM) × 1,315 de Seguridad Social (ASM) / 1.780 h) |
| Tiempo de meter una factura a mano: "desde casi un minuto hasta varios minutos"; "3-5 min por documento" | **WEAK** (blogs de proveedores: DocuWare, Dost, mygestion) | vista en buscador | Es **el** supuesto que decide si el cliente ahorra dinero (ver D). Hay que medirlo en la propia gestoría |
| Uso de IA en empresas: 21,1% (≥10 empleados) y 13,4% (microempresas) en el T1 2025 | **SRC** (dato del INE citado por la prensa) | resumen del buscador | Contexto; no es un dato del sector |

## 3. Lo que sigue siendo desconocido y decide el caso

1. **Precios reales de la competencia** (Inmatic por créditos, AutoApunte por planes, Contarapid, Dext, AutoEntry). **UNK.** Las páginas existen pero están bloqueadas aquí. Puedes mirarlas tú en 10 minutos sin contactar a nadie.
2. **Tasa de excepciones real** con facturas de gestorías españolas. **UNK.** Es lo que más pesa en el coste.
3. **Minutos por factura manual** en una gestoría concreta. **UNK.**
4. **Cuántas gestorías no usan ya** Inmatic, AutoApunte, la contabilización automática de a3innuva o la IA de Sage. **UNK.** El barómetro de Wolters Kluwer sugiere que la mayoría ya usa algo de IA.
5. **Qué parte del volumen** de facturas de una pyme viene de emisores obligados a factura estructurada desde 2027. **UNK.**
