# Demo: respuesta inmediata a leads (email + WhatsApp)

Página estática (un solo `index.html`, sin librerías ni peticiones externas) que simula el flujo:
1. llega el lead de Idealista por email;
2. el sistema responde con un **email automático** (objetivo < 2 min) con un botón "Seguir por WhatsApp";
3. el comprador **abre él** la conversación de WhatsApp;
4. el asistente automático se identifica, da la info de privacidad y la opción BAJA, cualifica y agenda la visita;
5. el agente recibe la ficha (rama CALIENTE o REVISAR PRESUPUESTO).

**Es una simulación:** no envía nada ni se conecta a ningún servicio. El banner "SIMULACIÓN · conversación y
comprador inventados; tiempos orientativos" se ve siempre (y añade "· agencia ficticia" si `ejemplo` es `true`).
No hay WhatsApp saliente como primer mensaje.

## Generar la demo de una agencia
```bash
cd proyecto-nuevo/negocio/demo
cp agencias/ejemplo.json agencias/mi-agencia.json   # ejemplo=false y sus pisos (1-3), con su permiso
python3 build_demo.py agencias/mi-agencia.json       # -> salida/<slug>/index.html
```
Campos:
- `agencia.nombre`, `agencia.color` (#RRGGBB), `agencia.agente`.
- `agencia.url_privacidad` (URL http(s) de su política de privacidad; si falta se muestra un texto genérico y avisa).
- `agencia.horario` (opcional): `{"apertura": "09:00", "cierre": "20:00"}` por defecto. "Fuera de horario" solo
  aparece si `lead.hora` < apertura o >= cierre.
- `lead.nombre`, `lead.hora` (HH:MM), `lead.primera_respuesta_seg` (1-120, por defecto 40; es simulado),
  `lead.presupuesto` (opcional, global).
- `pisos[]` con `ref`, `direccion`, `barrio`, `precio`, `m2`, `habitaciones` y `presupuesto_lead` (opcional, manda
  sobre el global). Sin presupuesto se usa precio + 6 % (rama CALIENTE). Presupuesto < precio → REVISAR PRESUPUESTO.
- `ejemplo`: `true` solo con datos inventados (el nombre debe contener "ficticia"; si no, avisa por stderr).
  Con `false`, recuerda por stderr que los pisos deben venir de la agencia con su permiso.

El `index.html` de esta carpeta es la plantilla y también funciona tal cual (datos ficticios).
`build_demo.py` calcula los textos que dependen de los datos (banner, horario, ramas) en `calculado`.
`salida/` está en `.gitignore`: las demos con datos de agencias reales no se suben al repositorio.

## Tests
```bash
cd proyecto-nuevo/negocio/demo && python3 -m unittest test_build_demo -v
```

## Enseñarla en el móvil
- Pasar el `index.html` generado al móvil (p. ej. enviándotelo a ti mismo) y abrirlo con el navegador.
  Funciona sin conexión. Que se abra bien desde la vista previa de Gmail/Drive: **SIN VERIFICAR** (mejor descargarlo).
- Botones: `x1/x2` velocidad, `Repetir`, píldoras de pisos para cambiar de piso, `Ficha` para reabrir la ficha.
- `index.html#rapido` la reproduce a 20x (para pruebas automáticas).
- Los tiempos que muestra son orientativos: el tiempo real se mide en el piloto.

Arquitectura de la instalación real: [ARQUITECTURA.md](ARQUITECTURA.md).
