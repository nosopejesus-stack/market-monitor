# Demo: respuesta inmediata a leads por WhatsApp

Página estática (un solo `index.html`, sin librerías ni peticiones externas) que simula cómo el asistente
responde a un lead de Idealista, lo cualifica, agenda la visita y entrega la ficha al agente.
**Es una simulación:** no envía nada ni se conecta a ningún servicio.

## Generar la demo de una agencia
```bash
cd proyecto-nuevo/negocio/demo
cp agencias/ejemplo.json agencias/mi-agencia.json   # rellenar con sus datos (1-3 pisos)
python3 build_demo.py agencias/mi-agencia.json       # -> salida/<slug>/index.html
```
Campos: `agencia.nombre`, `agencia.color` (#RRGGBB), `agencia.agente`, `agencia.asistente` (opcional),
`lead.nombre`, `lead.hora` (HH:MM), `lead.primera_respuesta_seg` (1-120, por defecto 40),
`pisos[]` con `ref`, `direccion`, `barrio`, `precio`, `m2`, `habitaciones`.
`"ejemplo": true` muestra el aviso "datos ficticios". El `index.html` de esta carpeta es la plantilla y
también funciona tal cual (datos ficticios).

`salida/` está en `.gitignore`: las demos con datos de agencias reales no se suben al repositorio.

## Enseñarla en el móvil
- Pasar el `index.html` generado al móvil (p. ej. enviándotelo a ti mismo) y abrirlo con el navegador.
  Funciona sin conexión. Que se abra bien desde la vista previa de Gmail/Drive: **SIN VERIFICAR** (mejor descargarlo).
- Botones: `x1/x2` velocidad, `Repetir`, píldoras de pisos para cambiar de piso, `Ficha` para reabrir la ficha.
- `index.html#rapido` la reproduce a 20x (para pruebas automáticas).

Arquitectura de la instalación real: [ARQUITECTURA.md](ARQUITECTURA.md).
