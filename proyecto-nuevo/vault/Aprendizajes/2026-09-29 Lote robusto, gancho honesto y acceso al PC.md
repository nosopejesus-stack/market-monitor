---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, python, csv, ventas, proceso]
origen: sesión 2026-09-29 (lote.py, gancho del informe previo, README, organización)
---
# 2026-09-29 Lote robusto, gancho honesto y acceso al PC

## 1. Lote robusto (`proyecto-nuevo/arcend/blindaje/lote.py`)
- **Qué pasó:** procesar muchas clínicas de una vez; un fallo (incluido `sys.exit`) no debe tumbar el lote.
- **Lección:** capturar `(Exception, SystemExit)` por elemento; el motivo del error es el primer aviso de conexión/SSL; reescribir el resumen tras cada elemento (si se corta, queda lo hecho). CSV para Excel en español: separador `;` y BOM (`utf-8-sig`). Al leer, aceptar `,` o `;` y UTF-8 o cp1252.
- **Cómo aplicarla:** cualquier proceso por lotes del proyecto sigue este patrón. Relacionado: [[Aprendizajes/2026-09-28 Rastreadores robustos - URL final, parámetros y codificación]].

## 2. Gancho honesto en el informe previo
- **Qué pasó:** la frase de venta del informe previo podía exagerar.
- **Lección:** "no permite" solo si `n_puntos_norma > 0`; "conviene revisar" con `n_puntos_revisar` (incluye los SIN VERIFICAR); sin frase si no hay puntos o la lectura no es fiable. La frase la calcula la herramienta, no se escribe a mano.
- **Cómo aplicarla:** ver [[Decisiones/2026-09-28 Arcend - Informe previo y N calculado por la herramienta]] y [[Aprendizajes/2026-09-28 Documento previo a la venta sin entregable de pago]].

## 3. README y carpetas sueltas
- **Qué pasó:** si el usuario copia carpetas sueltas, las rutas relativas a carpetas hermanas se rompen.
- **Lección:** indicar en el README que se copie la carpeta del proyecto entera (`proyecto-nuevo/arcend/`).
- **Cómo aplicarla:** toda guía para el usuario dice qué carpeta completa copiar.

## 4. Acceso al PC del usuario
- **Qué pasó:** se planteó usar el PC del usuario desde esta sesión cloud.
- **Lección:** en la sesión cloud no hay herramientas de Computer use. Para usarlo hace falta la app de escritorio de Claude con Computer use activado (o elegir el equipo en Devices en claude.ai). No afirmar acceso sin tener las herramientas.
- **Cómo aplicarla:** antes de prometer acciones en el PC, comprobar que las herramientas existen en la sesión; si no, dar al usuario los pasos. Relacionado: [[Aprendizajes/2026-09-28 El contenedor cloud no tiene internet libre]].

## 5. Organización del repo
- **Qué pasó:** el usuario necesitaba un punto de entrada claro.
- **Lección:** `EMPIEZA_AQUI.md` en la raíz es el punto de entrada; `infra/server/` queda marcado como futuro (cero gasto).
- **Cómo aplicarla:** enlazar desde `EMPIEZA_AQUI.md` cualquier guía nueva para el usuario.
