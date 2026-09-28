---
> **Nota de uso (2026-09-28):** documento de investigación interna. En venta NO se usan "reduce la sanción ~93 %" ni "desde 90.001 €": la fórmula única es la de `ventas/` con [VERIFICAR fuente antes de usar].
fecha: 2026-09-28
autor: investigador
proyecto: Arcend (clínicas de medicina estética independientes, Madrid)
metodo: solo WebSearch (WebFetch bloqueado para comunidad.madrid, boe.es, bocm.es, seme.org, elconfidencialdigital.com). Todo lo que viene de extractos del buscador o de webs de terceros va marcado SIN VERIFICAR hasta leer la fuente original.
---
# Mercado Arcend: datos para calibrar la simulación Monte Carlo

## 0. Corrección previa
- El código de medicina estética en el registro de centros sanitarios es **U.48 "Medicina estética"** (anexo II del RD 1277/2003), no U.90. U.90 es el cajón "otras unidades asistenciales" (SIN VERIFICAR el literal; boe.es bloqueado). Fuente: [BOE RD 1277/2003](https://www.boe.es/buscar/act.php?id=BOE-A-2003-19572); [SEME: "La Medicina Estética es U.48"](https://www.seme.org/comunicacion/notas-de-prensa/la-medicina-estetica-es-u48-busca-el-sello-digital-seme-de-garantia-medica).
- En Madrid la clínica estética se autoriza como C.2.x/C.3 sin internamiento con U.48 y se inspecciona con la "Lista de verificación para medicina estética" de la Consejería: [PDF Comunidad de Madrid](https://www.comunidad.madrid/sites/default/files/doc/sanidad/orde/lista_de_verificacion_para_medicina_estetica_c3.pdf).

## 1. Nº de clínicas en Madrid capital e independientes vs cadenas
**Dato oficial por municipio: NO ENCONTRADO.** El buscador público del registro ([Registro de centros, Comunidad de Madrid](https://www.comunidad.madrid/servicios/salud/registro-centros-servicios-establecimientos-sanitarios)) no se pudo consultar desde aquí; hay que sacarlo a mano en el PC del usuario (filtro por municipio Madrid + oferta U.48).

Lo que sí hay:
- España: **6.305 centros con U.48 en 2021** (+20,2 % vs 2019), facturación 3.586 M€ y ~900.000 tratamientos. [SEME, nota 2021](https://www.seme.org/comunicacion/notas-de-prensa/crece-el-interes-y-el-uso-de-la-medicina-estetica-en-espana-en-2021-se-realizaron-cerca-de-900.000-tratamientos-medico-esteticos); [elEconomista](https://www.eleconomista.es/salud/noticias/11953406/09/22/La-medicina-estetica-recupera-cifras-prepandemia-y-factura-3585-millones-de-euros-en-Espana.html). (Extractos: SIN VERIFICAR el texto íntegro.)
- La Comunidad de Madrid es la 1.ª en nº de centros U.48 y concentra ~25 % de la actividad (SIN VERIFICAR, extracto del estudio SEME/Hamilton 2021 vía buscador).
- Además hay >1.000 centros sin autorizar en España (SEME 2022): [elEconomista Sanidad](https://revistas.eleconomista.es/sanidad/2022/noviembre/mas-de-1000-centros-sin-autorizar-de-medicina-estetica-operan-en-espana-BA12476124).
- Cifra de directorio: "~500 clínicas de estética en Madrid" (SIN VERIFICAR, extracto de directorios tipo [salir.com](https://www.salir.com/centros-de-medicina-estetica-en-madrid-art-2109.html); mezcla estética y medicina estética).

**Estimación propia (SIN VERIFICAR, extrapolación):** 6.305 × ~20-25 % → ~1.250-1.600 centros U.48 en la Comunidad; Madrid capital ~55-60 % → **~700-950 centros con U.48** en la capital. Muchos son policlínicas, dermatología, dental o cirugía con U.48 añadida; las **clínicas cuyo negocio principal es la medicina estética** serían ~350-550.
- Cadenas: Dorsia (>160 clínicas en España, grupo WM Clinics; [dorsia.es](https://www.dorsia.es/clinicas/)), Clínicas Origen, Trevi (4 centros en Madrid; [clinicatrevi.com](https://www.clinicatrevi.com/)), Svenson, Menorca, etc. **Estimación: 10-20 % de los locales de la capital son cadena/franquicia; 80-90 % independientes** (SIN VERIFICAR; no hay estudio público).

## 2. Publicidad sanitaria en Madrid ("Blindaje")
### Normativa
| Norma | Qué exige | Fuente |
|---|---|---|
| RD 1907/1996 (publicidad con pretendida finalidad sanitaria), art. 4 | Prohíbe publicidad que prometa curación/resultados garantizados, "sin riesgo", testimonios/aval de profesionales en publicidad al público, etc. | [BOE-A-1996-18085](https://www.boe.es/buscar/act.php?id=BOE-A-1996-18085) |
| RD 1416/1994 (publicidad de medicamentos), art. 7 + RDL 1/2015 (Ley de garantías) | **Prohibida la publicidad al público de medicamentos con receta**: toxina botulínica (Vistabel, Azzalure, Bocouture), también por alusiones indirectas ("neuromoduladores", siglas, hashtags) y ofertas/bonos ligados a ellos. Es la infracción que más se sanciona. | [E&J, TSJ Madrid](https://www.economistjurist.es/actualidad-juridica/multada-una-clinica-estetica-con-90-000-euros-por-publicitar-medicamentos-sujetos-a-prescripcion-medica/) |
| RD 1277/2003 + **Decreto 51/2006** de la Comunidad de Madrid (autorización y registro) | Solo los centros autorizados pueden usar términos sanitarios en publicidad y **deben consignar el nº de registro sanitario (NICA/CS)** en la publicidad; mostrar la autorización en lugar visible. | [INAP, Decreto 51/2006](https://laadministracionaldia.inap.es/noticia.asp?id=1235680); [PDF BOCM 26-6-2006](https://www.aucatel.com/documentacion%20web%202016/madrid/Sanidad%20y%20Salud/31-Decreto%2051%202006%20regula%20Regimen%20Juridico%20y%20Procedimiento%20de%20Autorizacion%20y%20Registro%20de%20%20centros%20y%20establecimientos%20sanitarios%20de%20la%20CAM.pdf) |
| Ley 12/2001 de Ordenación Sanitaria de Madrid | Régimen sancionador autonómico (leve/grave/muy grave; hasta cierre temporal) | [BOE-A-2002-4375](https://www.boe.es/buscar/act.php?id=BOE-A-2002-4375) |
| RGPD / AEPD | Fotos "antes/después" sin consentimiento específico: sancionado. | [Infobae 25-9-2024, multa 10.000 €](https://www.infobae.com/espana/2024/09/25/una-clinica-estetica-sancionada-con-una-multa-de-10000-euros-por-publicar-imagenes-del-antes-y-despues-sin-consentimiento/) |
| Orden 1158/2018 de la Consejería (criterios de publicidad) | Citada por el buscador como criterio propio de Madrid. | **SIN VERIFICAR** (puede ser una confusión) |

- **Nº de colegiado en la publicidad:** no he encontrado norma de Madrid que lo exija con carácter general en la publicidad del centro; lo exigen códigos deontológicos/colegios y es buena práctica. **SIN VERIFICAR.**
- **Antes/después:** no está prohibido per se por una norma específica en Madrid; el riesgo real es (a) RGPD sin consentimiento y (b) que induzca a garantía de resultado. **SIN VERIFICAR** la postura escrita de la Consejería.
- **Promociones:** ofertas tipo "Bótox 3 zonas 99 €" son infracción (incentivo al consumo de medicamento con receta). Fuente secundaria: [Mola Crear 2026](https://molacrear.com/blog/actualizaciones-legales-en-publicidad-sanitaria-para-2026/) (SIN VERIFICAR).
- **Cambio normativo en curso:** proyecto de RD estatal de publicidad de productos sanitarios (ácido hialurónico es producto sanitario): [Sanidad, texto en audiencia pública DG 52-23](https://www.sanidad.gob.es/normativa/audiencia/docs/DG_52-23_PRD_publicidad_productos_sanitarios.pdf). Estado de aprobación a 2026: SIN VERIFICAR.

### Quién vigila y sanciona
- **Consejería de Sanidad de la Comunidad de Madrid**, Área de Control Farmacéutico y Productos Sanitarios (D. G. de Inspección y Ordenación): revisa webs y RRSS de forma continuada y envía requerimientos de cese. [Vigilancia de publicidad sanitaria](https://www.comunidad.madrid/servicios/salud/vigilancia-publicidad-sanitaria) (página bloqueada aquí; contenido por extracto: SIN VERIFICAR literal).
- Ayuntamiento de Madrid (inspección municipal/consumo) comprueba en clínicas que la publicidad lleve el nº de registro: [COEM, campaña de inspección de clínicas dentales](https://www.coem.org.es/content/index/186) (dental, pero mismo criterio).
- AEPD para imágenes de pacientes.

### Importes y casos reales
- Publicidad de medicamentos con receta: **muy grave desde 90.001 €** (RDL 1/2015; tramos leve ≤30.000, grave 30.001-90.000, muy grave 90.001-1.000.000; SIN VERIFICAR el artículo exacto, boe.es bloqueado).
- **Desde 2020 hasta 2023 la Consejería requirió a 58 clínicas retirar publicidad de toxina/PRP y propuso sanción a 13**, con multas de 90.001 €: [El Confidencial Digital, 31-3-2023](https://www.elconfidencialdigital.com/articulo/vivir/multas-90001-euros-clinicas-esteticas-madrilenas-que-publicitan-botox/20230331142754547336.html) (dato por extracto).
- TSJ de Madrid confirma 90.000 € a Body Clinic Madrid (web + 10 publicaciones en Facebook): [E&J](https://www.economistjurist.es/actualidad-juridica/multada-una-clinica-estetica-con-90-000-euros-por-publicitar-medicamentos-sujetos-a-prescripcion-medica/); [Miguel Ortego](https://miguelortego.com/multa-de-90-000-e-a-una-clinica-estetica-por-publicitar-medicamentos-sujetos-a-prescripcion-medica/).
- Caso de reposición: 90.001 € rebajados a **6.000 €** (leve) porque la clínica ya había retirado contenidos y consultado a la Consejería: [JL Casajuana Abogados](https://jlcasajuanaabogados.com/caso-exito-reduccion-sancion-publicidad-medicamentos-clinica/). **Esto es el mejor argumento de venta del Blindaje: la corrección previa documentada reduce la sanción ~93 %.**
- Campañas 2024-2026: SEME comunicó a sus socios los avisos recibidos de las autoridades ([SEME](https://www.seme.org/comunicacion/notas-de-prensa/la-sociedad-espanola-de-medicina-estetica-informa-a-sus-socios-y-a-las-clinicas-sobre-la-normativa-en-materia-de-publicidad-de); fecha SIN VERIFICAR); [Miguel Jara, 7-3-2025](https://www.migueljara.com/2025/03/07/el-botox-en-el-punto-de-mira-por-su-promocion-ilegal-en-clinicas-de-medicina-estetica/). **No he encontrado una nota oficial de campaña de inspección 2025-2026 con cifras.** SIN VERIFICAR.

### ¿Es un dolor real y caro?
Sí en **severidad** (90.001 € por un post; cierre posible) y es **fácil de detectar** (hashtags "#botox", precios por zona, "sin riesgo"). Pero la **frecuencia** es baja: ~13 propuestas de sanción en ~3 años en Madrid (≈4/año) frente a cientos de clínicas → probabilidad anual de sanción por clínica ≈ 0,5-1 %; de requerimiento ≈ 2-4 %. Es un dolor de "seguro": se vende con el caso concreto (captura de su propia web) y con el dato 90.001 € → 6.000 €, no como riesgo abstracto.

## 3. Competencia y precios
### (a) Recepcionistas automáticas / chatbots (España)
| Producto | Precio | Fuente |
|---|---|---|
| Ringuno | desde 29 €/mes, sin permanencia | [ringuno.com](https://ringuno.com/es/dental-clinics) |
| Clinicbot (Sofía IA) | gratis / 55 €/mes + consumo | [clinicbot.es](https://clinicbot.es/recepcionista-virtual-clinica/) ; tiene página específica [estética](https://clinicbot.es/ia-clinicas-esteticas/) |
| Clara Assistant | desde 49,95 €/mes (WhatsApp, Google) | [claraassistant.com](https://claraassistant.com/dentistas/) |
| Habla (Carla) | desde 49 €/mes | [myhabla.com](https://myhabla.com/clinicas) |
| Recepcionista.com | desde 29 €/mes | [reseña](https://ai-answering-review.com/es/reviews/recepcionista-com/) |
| Ganexity | desde 79,99 €/mes | [ganexity.com](https://ganexity.com/es/recepcionista-virtual-clinicas-valencia) |
| Minute Call (humano o IA) | desde 250 €/mes | [minute-call.com](https://www.minute-call.com/articulos/mejores-empresas-recepcionista-virtual-espana) |
| Doctoralia Phone | precio no público | [Doctoralia](https://pro.doctoralia.es/productos/doctoralia-phone) |
Precios por extracto de buscador: SIN VERIFICAR a fecha de hoy. Conclusión: **el bot solo está en 29-100 €/mes; humano externalizado ~250 €/mes.** Confirma el riesgo ya anotado en la ficha del proyecto.

### (b) Agencias de marketing para clínicas estéticas (Madrid)
- Allora (Madrid): Meta Ads 950 €/mes, Google Ads 1.350 €/mes, CRM+automatizaciones 1.500 €/mes, plan con vídeo 2.000 €/mes (+IVA, inversión aparte): [allora.es](https://allora.es/agencia-marketing-clinicas-estetica-madrid/).
- Rangos genéricos: SEO médico 500-1.500 €/mes, RRSS 600-2.500 €/mes; clínica total 1.000-5.000 €/mes: [Medical Marketing](https://medicalmarketing.digital/es/blog/cuanto-cuesta-marketing-clinica-dental/). Gestión básica web+RRSS 300-600 €/mes ([GrupArts](https://www.gruparts.com/marketing-digital/gestion-redes-sociales-clinicas/)).
- Coste por primera visita en estética 40-110 € con campañas bien llevadas (extracto, SIN VERIFICAR).
Todo SIN VERIFICAR (extractos). **Implicación:** 890-1.290 €/mes compite en presupuesto con la agencia, no con el bot. La clínica ya paga ~1.000-2.000 €/mes a alguien; Arcend tiene que entrar como sustituto o complemento claro.

### (c) Consultoras de cumplimiento de publicidad sanitaria
- Existen despachos que defienden sanciones (JL Casajuana, [Proluco](https://www.proluco.com/clinica-estetica), [Priscila Giraldo](https://www.priscilagiraldo.com/una-auditoria-legal-para-que-sirven/)) y agencias que venden "marketing que cumple" ([Mola Crear](https://molacrear.com/), [Proinda](https://proinda.es/advertencia-sobre-publicidad-sanitaria/)).
- **No he encontrado ninguna tarifa pública en España para auditoría de publicidad sanitaria de web/RRSS.** Referencias indirectas: "pack auditoría digital" de agencias ([The Hub](https://www.thehubmarketingservices.com/packs/auditoria/)). Rango razonable de mercado (SIN VERIFICAR, estimación): revisión puntual 300-1.500 € por abogado/consultor. Hueco de mercado: nadie vende "vigilancia continua" productizada a clínicas pequeñas.

## 4. Llamadas perdidas y valor de paciente
- Doctoralia: **35 % de las llamadas no se atienden; ≥20 % de ellas son para pedir cita; solo 1 de cada 3 se devuelve** ([Doctoralia Pro](https://pro.doctoralia.es/blog/clinicas/como-atender-todas-las-llamadas-de-telefono)). Top Doctors 2015: **15 %** sin atender (53.600 llamadas a 1.500 clínicas) ([iSanidad](https://isanidad.com/55723/el-15-de-llamadas-de-pacientes-a-las-consultas-no-se-atienden/)). Cifras de 45 % aparecen en blogs de vendedores (no fiables).
- Precios Madrid (webs de clínicas, SIN VERIFICAR a hoy): toxina 1 zona ~100-150 €, tercio superior 250-350 €; ácido hialurónico 250-400 €/vial ([Génova 10](https://www.genova10.es/botox-madrid-precio-neuromoduladores-toxina-botulinica/); [Medicalesthetic](https://medicalesthetic.es/precios/); [De Felipe](https://madrid.defelipe.com/dermatologia-estetica-madrid/toxina-botulinica-madrid/)). **Ticket primera visita típico: 250-600 €.**
- Gasto medio anual por paciente en España: **~1.027 €/año (mujer), ~800 € (hombre)** (SEME, vía extracto; SIN VERIFICAR literal) ([SEME](https://www.seme.org/comunicacion/notas-de-prensa/el-50-por-ciento-de-la-poblacion-espanola-se-ha-realizado-un-tratamiento-de-medicina-estetica)). Madrid barrio Salamanca/Chamberí probablemente por encima: 1.000-2.500 €/año (estimación).
- **Alerta sobre la ficha del proyecto:** "valor por paciente 1.500-5.000 €" y "4 pacientes → 8.000 €/mes" están por encima de los datos. Recalculado: 20 llamadas perdidas × 20-50 % de intención de cita × 50-70 % que no reintenta ≈ 2-7 pacientes/mes × 300-600 € primer ticket ≈ **600-4.000 €/mes de primer ticket** (valor anual 1.000-2.500 €/paciente). El argumento sigue valiendo frente a 890 €, pero la cifra de 8.000 € no se puede defender con datos públicos.

## 5. Ciclo de venta y decisor
**Sin estudios públicos específicos (SIN VERIFICAR todo este apartado; inferencia).**
- Clínica independiente pequeña (1-3 médicos): decide el **médico titular/propietario**; a veces con socio/pareja que lleva gestión. Con gerente solo en clínicas de 5+ empleados. La recepcionista es filtro, no decisor, y puede ver la "Atención" como amenaza.
- Ciclo esperable: 1.ª visita/llamada → reunión con el médico (a menudo entre pacientes o fuera de horario) → informe → decisión: **2-6 semanas**; cierre en la 1.ª reunión solo con compromisos pequeños (auditoría one-off). Picos de disponibilidad baja: agosto y diciembre.
- El one-off de auditoría (bajo, tangible, con el riesgo de 90.001 € delante) es la puerta de entrada lógica; la cuota mensual se vende después.

## Parámetros para la simulación
| Parámetro | Bajo | Medio | Alto | Base |
|---|---|---|---|---|
| Nº clínicas objetivo (independientes, Madrid capital, medicina estética como negocio principal) | 250 | 450 | 700 | Extrapolación SEME 6.305 × cuota Madrid; 80-90 % independientes (SIN VERIFICAR) |
| Tasa de conversación con decisor (por "puerta" contactada) | 10 % | 20 % | 35 % | Inferencia; el plan asume 40 % (16/40), optimista |
| Tasa de cierre (sobre conversaciones con decisor) | 3 % | 8 % | 15 % | Inferencia; el plan asume 12,5 % (2/16) |
| Precio aceptable one-off auditoría de cumplimiento | 150 € | 400 € | 900 € | Sin tarifas públicas; abogados 300-1.500 € (estimación) |
| Precio aceptable mensual | 150 € | 400 € | 900 € | Bot 29-100 €; humano 250 €; agencia 950-2.000 €. 890-1.290 € solo si sustituye parte de la agencia |
| Churn mensual | 2 % | 4 % | 8 % | Inferencia SaaS pyme sin permanencia (competidores sin permanencia) |
Extra para el modelo: probabilidad anual de requerimiento por clínica 2-4 %, de sanción 0,5-1 %; sanción 6.000-90.001 €.
Chequeo del embudo: 40 puertas × 20 % × 8 % ≈ **0,6 firmas/mes** (rango 0,1-2,1), frente a las 2 del plan.

## Pendiente de verificar en el PC del usuario (sin red bloqueada)
1. Registro de centros de la Comunidad de Madrid: contar U.48 en municipio Madrid (dato clave).
2. Página "Vigilancia de publicidad sanitaria" y existencia/contenido de la Orden 1158/2018.
3. RDL 1/2015, artículos de infracciones/sanciones de publicidad de medicamentos (tramos exactos).
4. Precios actuales de Ringuno/Clinicbot/Clara en sus webs.
5. Si hay nota oficial de campaña de inspección de publicidad 2025-2026.
