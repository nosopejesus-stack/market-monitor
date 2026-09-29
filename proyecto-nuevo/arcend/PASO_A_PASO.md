# Arcend · Paso a paso (tú + el equipo)

Producto: **Blindaje** para clínicas de medicina estética independientes de Madrid.
390 € revisión + corrección de la publicidad (web y redes) · 190 €/mes vigilancia mensual · sin permanencia.
Todo está en `proyecto-nuevo/arcend/`. Lo que marca 🙋 lo haces tú; lo demás lo hace el equipo.

---

## Día 0 · Preparar tu PC (30 min, una vez)
1. 🙋 Instala Python desde https://www.python.org/downloads/ (marca **"Add python.exe to PATH"**).
2. 🙋 Descarga el repositorio: en GitHub, rama `claude/tender-cannon-ui4ixl` → **Code → Download ZIP**, y descomprímelo.
3. 🙋 Abre PowerShell en `proyecto-nuevo\arcend\blindaje` y prueba:
   ```powershell
   python blindaje.py https://www.ejemplo-de-clinica.es --nombre "Prueba"
   ```
   Se crea `informes\prueba\informe.html`. Ábrelo con el navegador (Ctrl+P → Guardar como PDF).
   Detalles en `blindaje/README.md`.

## Día 1 · Informes de todas las clínicas (1 comando + 1 h de comprobaciones)
0. 🙋 En PowerShell, dentro de `Documentos\arcend\blindaje`:
   ```powershell
   py lote.py ..\prospectos\clinicas.csv --contacto-nombre "Tu nombre" --contacto-telefono "Tu móvil"
   start .\informes\RESUMEN.html
   ```
   El resumen ordena las clínicas por prioridad de llamada y trae **la frase exacta** para cada una
   (columna `frase_llamada`). Si una sale "revisar a mano", guarda su web con Ctrl+S y usa `--html-local`.
   Pásame `informes\RESUMEN.csv` y los `informe.json`: reviso cada hallazgo antes de que llames.
1. 🙋 Abre `prospectos/clinicas.csv` (49 clínicas). Empieza por las de tu ruta **menos** Face Clinic (es un grupo de 4 centros) y usa la IME de **Vallehermoso 9** (la de Lagasca 95 es Clínica Londres, una cadena).
2. 🙋 Para cada una: comprueba en su web que el teléfono y la dirección del CSV son correctos (los datos salen de un buscador y están SIN VERIFICAR).
3. 🙋 Comprueba en el **Registro de centros sanitarios de la Comunidad de Madrid** (buscador público de la Comunidad) que la clínica está inscrita. Si no aparece, no se llama hasta aclararlo; anótalo en `notas`.
4. 🙋 Genera el informe **PREVIO** (el que se enseña antes de pagar: puntos con norma y gravedad, sin textos corregidos):
   ```powershell
   python blindaje.py https://web-de-la-clinica.es --nombre "Nombre Clínica" --previo --contacto-nombre "Tu nombre" --contacto-telefono "Tu móvil"
   ```
5. 🙋 Pásame (sube a GitHub o pega aquí) los `informe.json`. El equipo:
   - revisa cada hallazgo a mano para que no haya **ningún** falso positivo delante de un médico;
   - confirma el **N de la llamada = `n_puntos_norma`** de `informe.json` (lo calcula la herramienta: reglas distintas con norma concreta, deduplicadas; no se cuenta a mano). Si es 0, no se usa el anzuelo de la llamada;
   - ordena las clínicas por gravedad (ALTA primero: toxina, promesas, sin nº de registro).
6. Si una web no carga: guarda sus páginas con el navegador (Ctrl+S) en una carpeta y usa `--html-local CARPETA`.

## Días 2-10 · Llamadas (1-2 h/día)
1. 🙋 Llama siguiendo `ventas/guion_llamada.md`. Objetivo: 10-15 min con el médico titular.
   - Frase de la llamada: "hay N puntos que la normativa de publicidad sanitaria no permite". Si preguntan por consecuencias: "pueden dar lugar a un requerimiento". **Nunca** digas que la Consejería sanciona ni que habrá multa.
   - Solo por teléfono. **Nada de emails comerciales en frío** (LSSI). Si piden email, envías solo el informe previo o el resumen de una página a la dirección que te den.
   - Si dicen "no vuelvan a llamar", se anota `no_llamar` y no se vuelve a llamar.
2. 🙋 Anota cada llamada en `ventas/embudo.csv` (o dímelo y lo anoto yo).
3. Meta: **40 llamadas en 2 semanas**.

## Reunión (15 min cada una)
1. Lleva el informe **PREVIO impreso** (generado con `--previo`: N puntos con norma y gravedad, sin textos corregidos). Si quieres enseñar la página afectada, haz tú la foto con el móvil (la herramienta no genera capturas). El informe completo con los textos corregidos es lo que se paga.
2. 🙋 Sigue `ventas/guion_reunion.md`: 3 hallazgos → caso real → oferta → **pide la decisión en la reunión**.
3. Reglas: nunca digas "IA" ni expliques cómo está montado; no prometas que no habrá multa; no es asesoramiento jurídico.

## Cuando alguien dice que sí
1. 🙋 Alta de autónomo (24 h), fechada el día de la primera factura. Consulta con un gestor el epígrafe, el IVA y la retención.
2. 🙋 Firma `ventas/contrato_blindaje.md` (plantilla: que la revise un profesional antes del primer uso) y cobra **390 €** por transferencia.
3. **Solo tras el cobro**, 🙋 generas el informe completo (el mismo comando **sin** `--previo`) y el equipo prepara los textos corregidos listos para publicar. Plazo: **5 días hábiles desde el cobro**.
4. 🙋 Se los entregas; la clínica (o su web) los publica. El equipo comprueba que están publicados y deja constancia fechada.
5. 🙋 Ofreces la vigilancia mensual (190 €/mes). El equipo la hace cada mes y te pasa el aviso para la clínica.
6. Solo con ≥ 3 clientes contentos (semana 4-8): ofrecer la subida a Atención (paquetes de tu Notion).

## Condiciones de muerte (se miran al acabar las 40 llamadas)
- < 3 reuniones con el titular → cambiar guion o pasar a visitas en persona.
- 0 firmas tras 8 reuniones → parar y revisar la oferta.
- Caja neta ≤ 0 en la semana 4 → se da por fallida.

## Qué esperar (sin ilusiones)
- 10.000 € en 30 días: poco probable (≤ 10 %).
- Con cifras de mercado: ~4.000-9.000 € de caja neta en 13 semanas. Con las de tu Notion: bastante más.
- Tus primeras 40 llamadas dirán cuál es la real. Pásame los números y recalculo la simulación.
