# Las 10 primeras clínicas a llamar (29-09-2026)

Fuente: lote de Blindaje sobre las webs reales (29-09-2026), revisado a mano hallazgo por hallazgo por el
agente revisor (996 hallazgos; los falsos positivos se corrigieron en las reglas con su test) y reanalizado.
Teléfono y dirección cotejados con la web de cada clínica; nº de registro y titular en el **Registro de centros
sanitarios de la Comunidad de Madrid** (buscador oficial, por dirección).

**N** = `n_puntos_norma`: tipos de infracción distintos con norma concreta (toxina / promoción sobre acto médico),
no frases. La frase la calcula la herramienta; no se cambia a mano.

Reglas de la llamada (ver `guion_llamada.md`): solo por teléfono; nunca "la Consejería le va a multar"; si
preguntan por consecuencias, "pueden dar lugar a un requerimiento"; 90.001 € es el mínimo legal de una infracción
muy grave (RDL 1/2015, art. 114.1.c), no una promesa de lo que le pasará.

| # | Clínica (id) | Teléfono verificado | Frase exacta | Hallazgo principal (dónde verlo) | Registro CAM |
|---|---|---|---|---|---|
| 1 | Medicina Estética Génova 10 (ARC-012) | 913 19 15 57 | "He revisado la publicidad de su web y hay 2 puntos que la normativa de publicidad sanitaria no permite." | Promoción sobre la toxina: «Promoción 280 € Neuromoduladores: tratamiento de arrugas tercio superior… Promoción válida hasta 05/10/2026» (portada, genova10.es) | CS4427 · Ana María Barranco Saiz |
| 2 | ODA Aesthetic (ARC-004) | 640 36 92 45 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | «Neuromoduladores (Bot\*x)… Ahora: 385 € Antes: 505 €» con peeling de regalo (odaaesthetic.com/promociones/) | CS17657 · Oda Aesthetic S.L. |
| 3 | Clínica Ibiza (ARC-018) | 915 57 25 40 / 600 75 10 10 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | «Promoción de Septiembre · Pack Tú Eliges Antiarrugas 445 € 350 € · Ahorras 95 €» y «bótox» en la portada (clinicaibiza.com) | CS11673 · Clínica-Ibiza, S.L. (lo publica en su web) |
| 4 | Doctora Bonina (ARC-023) | 91 590 63 63 / 689 16 92 90 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | «15% de descuento en aumento de labios utilizando el código VERANO26» (doctorabonina.com/aumento-de-labios/) y «Neuromoduladores» en la portada | CS19289 · Doctora Bonina, S.L.P. |
| 5 | Clínica Golden Estética España (ARC-003) | 910 44 68 09 / 653 55 05 57 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | «Tratamiento Antiarrugas en oferta por solo 199€» (goldenestetica.es/medicina-estetica/eliminar-arrugas-en-madrid/) y #botox en la portada | CS3947 · Golden Estética España, S.L. |
| 6 | Centro Médico López-Linares (ARC-033) | 914 58 16 60 / 611 55 83 84 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | Plan con descuento sobre la toxina: «Toxina botulínica 3 zonas 400€ (Ahorras 150€)» (doctoralopezlinares.com/bonos) | CS9965 · Clínica Dental López Linares, S.L. |
| 7 | Novo Clinic (ARC-014) | 911 41 49 03 | "…hay 2 puntos que la normativa de publicidad sanitaria no permite." | «BLACK FRIDAY: los mejores tratamientos de Medicina Estética hasta con un 40% de descuento» (portada; campaña de noviembre que sigue publicada) y «Neuromoduladores» | CS21858 (probable) · Derma Clear Belleza y Medicina Estética S.L. — confirmar titular |
| 8 | Clínica Vandermed (ARC-030) | 630 47 79 28 | "He revisado la publicidad de su web y hay 1 punto que la normativa de publicidad sanitaria no permite." | «Neuromoduladores» como tratamiento en el menú de toda la web (clinicavandermed.com) | CS21052 · Tienda Dermatocosmética S.L. (= titular de la web) |
| 9 | Clínicas Auramed (ARC-034) | 915 22 22 83 / 641 11 69 17 | "…hay 1 punto que la normativa de publicidad sanitaria no permite." | «Neuromoduladores» (clinicasauramed.com/medicinaestetica) | CS7921 · Vericlinic Consulting, S.L. (lo publica en su web) |
| 10 | Clínica Estética Oquendo (ARC-017) | 614 12 23 42 / 637 62 62 40 | "…hay 1 punto que la normativa de publicidad sanitaria no permite." | «Neuromoduladores» en la portada (dianaoquendo.com) | CS20940 · Sanitaria y Dra. Oquendo Medicina Estética, S.L. |

Antes de cada llamada: abre el informe previo (`blindaje/informes/<clínica>/informe_previo.html`) y mira en la web
la frase del hallazgo principal; si ya no está, no la uses.

## Avisos por clínica
- **López-Linares:** además, el formulario de su portada pide nombre y teléfono sin casilla ni texto de privacidad (RGPD art. 13; comprobado en el navegador el 29-09-2026). No cuenta en la frase de la llamada: úsalo en la reunión.
- **Génova 10:** la web menciona «Nuestra clínica en Bilbao»: tienen otro centro fuera de Madrid (sigue siendo de las doctoras). La promoción caduca el 05/10/2026: llamar esta semana.
- **Golden:** posible 2.º centro en Marbella (Instagram), SIN VERIFICAR.
- **Novo Clinic:** su web no publica el titular; el centro inscrito en Velázquez 46, 1.º izda. es Derma Clear: confírmalo en la llamada o no lo menciones.
- **López-Linares:** es una clínica dental con medicina estética.

## Descartadas del top 10 y por qué
- **IME (ARC-006), Clínica DA (ARC-001) y Dra. Elena Berezo (ARC-013):** mismo titular en el Registro (Elenpa Médico Estético S.L.) en 3 direcciones; la web de DA habla de «franquicia». Grupo, no clínica independiente. Además IME y Berezo publican un nº de registro (CS11259) que el Registro no devuelve.
- **Medicalesthetic (ARC-010), Blue Moon (ARC-002), CEME (ARC-025), ENEA (ARC-037):** varias sedes o grupo.
- **Eternal Beauty (ARC-020):** el «10 % de descuento» es por suscribirse a su lista (dudoso) y el fijo del CSV no está en su web.
- **Soria Vizcaíno (ARC-024) y Velassaru (ARC-044):** no hay ningún centro inscrito en la dirección del CSV. Aclarar antes de llamar.
- **Dra. Mirta Herrero (ARC-019):** su web publica el nº de registro de su otro centro (Atocha 57), no el de Menéndez Pelayo 61. Es un buen punto, pero conviene confirmarlo antes.
- **Felicidad Carrera, Olalla Álvarez, Aliyomar Rivero, Baobab, Mangata, CM Balboa, Clínica Álvarez:** N = 0 (solo puntos "conviene revisar").
