"""Tests de build_demo.py (solo biblioteca estándar).

Ejecutar desde esta carpeta:
    python3 -m unittest test_build_demo -v
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import build_demo  # noqa: E402

BASE = {
    "ejemplo": False,
    "agencia": {
        "nombre": "Agencia de Prueba Test",
        "color": "#0f5f8c",
        "agente": "Agente de prueba",
        "url_privacidad": "https://example.com/privacidad",
    },
    "lead": {"nombre": "Comprador Prueba", "hora": "11:00"},
    "pisos": [
        {"ref": "T-1", "direccion": "Calle Test, 1", "barrio": "Centro", "precio": 300000, "m2": 70, "habitaciones": 2}
    ],
}
BANNER = "SIMULACIÓN · conversación y comprador inventados; tiempos orientativos"
CONFIG = re.compile(r"/\*CONFIG_INICIO\*/(.*?)/\*CONFIG_FIN\*/", re.S)


class TestBuildDemo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def construir(self, cfg: dict) -> str:
        ruta = self.tmp / "agencia.json"
        ruta.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        destino = build_demo.generar(ruta, self.tmp / "salida")
        return destino.read_text(encoding="utf-8")

    def config_de(self, html: str) -> dict:
        bloques = CONFIG.findall(html)
        self.assertEqual(len(bloques), 1)
        return json.loads(bloques[0])

    def cfg(self, **cambios) -> dict:
        c = copy.deepcopy(BASE)
        for ruta, valor in cambios.items():
            obj = c
            partes = ruta.split("__")
            for p in partes[:-1]:
                obj = obj[int(p)] if p.isdigit() else obj[p]
            obj[partes[-1]] = valor
        return c

    # (a) En horario: sin "fuera de horario" y con banner de simulación.
    def test_en_horario_sin_fuera_de_horario_y_con_banner(self):
        html = self.construir(self.cfg())
        self.assertNotIn("fuera de horario", html)
        self.assertIn(BANNER, html)
        self.assertNotIn("agencia ficticia", html)
        calc = self.config_de(html)["calculado"]
        self.assertFalse(calc["fuera_horario"])
        self.assertEqual(calc["crono"], "objetivo < 2 min (simulado)")

    # (b) 22:00 es fuera de horario (cierre por defecto 20:00).
    def test_22h_fuera_de_horario(self):
        html = self.construir(self.cfg(lead__hora="22:00"))
        self.assertIn("fuera de horario", html)
        self.assertTrue(self.config_de(html)["calculado"]["fuera_horario"])

    def test_umbrales_de_horario(self):
        casos = [("08:59", True), ("09:00", False), ("19:59", False), ("20:00", True)]
        for hora, esperado in casos:
            with self.subTest(hora=hora):
                c = build_demo.validar(self.cfg(lead__hora=hora))
                self.assertEqual(c["calculado"]["fuera_horario"], esperado)
        # Umbrales configurables
        c = self.cfg(lead__hora="21:30")
        c["agencia"]["horario"] = {"apertura": "10:00", "cierre": "22:00"}
        self.assertFalse(build_demo.validar(c)["calculado"]["fuera_horario"])

    # (c) Presupuesto por debajo del precio -> rama REVISAR PRESUPUESTO.
    def test_presupuesto_bajo_rama_revisar(self):
        html = self.construir(self.cfg(lead__presupuesto=250000))
        piso = self.config_de(html)["calculado"]["pisos"][0]
        self.assertEqual(piso, {"presupuesto": 250000, "rama": "REVISAR PRESUPUESTO"})

    def test_presupuesto_por_piso_manda_sobre_global(self):
        c = self.cfg(lead__presupuesto=250000, pisos__0__presupuesto_lead=320000)
        self.assertEqual(build_demo.validar(c)["calculado"]["pisos"][0]["rama"], "CALIENTE")
        # Sin presupuesto: por defecto encaja (CALIENTE)
        self.assertEqual(build_demo.validar(self.cfg())["calculado"]["pisos"][0]["rama"], "CALIENTE")

    # (d) Datos hostiles escapados: no pueden cerrar el <script> ni inyectar HTML.
    def test_json_hostil_escapado(self):
        hostil = "</script><script>alert(1)</script><!--&"
        html = self.construir(self.cfg(agencia__nombre=hostil[:80], pisos__0__direccion="<img src=x onerror=alert(1)>"))
        self.assertNotIn("</script><script>alert(1)", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertEqual(html.count("</script>"), 2)  # solo las dos etiquetas de la plantilla
        cfg = self.config_de(html)
        self.assertEqual(cfg["agencia"]["nombre"], hostil[:80])

    # (e) Color inválido -> error.
    def test_color_invalido(self):
        for color in ("rojo", "#fff", "#12345g", "#0f5f8c;}body{display:none", ""):
            with self.subTest(color=color):
                with self.assertRaises(build_demo.ErrorConfig):
                    build_demo.validar(self.cfg(agencia__color=color))

    def test_url_privacidad_invalida(self):
        with self.assertRaises(build_demo.ErrorConfig):
            build_demo.validar(self.cfg(agencia__url_privacidad="javascript:alert(1)"))

    def test_banner_ejemplo_y_avisos(self):
        c = build_demo.validar(self.cfg(ejemplo=True))
        self.assertEqual(c["calculado"]["banner"], BANNER + " · agencia ficticia")
        self.assertTrue(any("ficticia" in a for a in build_demo.avisos(c)))
        c = build_demo.validar(self.cfg())
        self.assertTrue(any("permiso" in a for a in build_demo.avisos(c)))

    def test_main_avisa_por_stderr(self):
        ruta = self.tmp / "a.json"
        ruta.write_text(json.dumps(self.cfg(ejemplo=True)), encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            codigo = build_demo.main([str(ruta), "--salida", str(self.tmp / "s")])
        self.assertEqual(codigo, 0)
        self.assertIn("Aviso:", err.getvalue())
        self.assertIn("ficticia", err.getvalue())

    def test_plantilla_sin_textos_prohibidos(self):
        plantilla = build_demo.PLANTILLA.read_text(encoding="utf-8")
        sin_config = CONFIG.sub("", plantilla)
        for prohibido in ("fuera de horario", "solo tienes que presentarte", "asistente virtual",
                          "tiempo del agente", "Respondido en"):
            with self.subTest(prohibido=prohibido):
                self.assertNotIn(prohibido, sin_config)
        self.assertIn(BANNER, sin_config)  # banner estático, visible aunque falle el JS
        self.assertIn("Soy el asistente automático de", sin_config)
        self.assertIn("Responde BAJA para no recibir más mensajes", sin_config)
        self.assertNotRegex(sin_config, r"(src|href)\s*=\s*[\"']https?:")

    def test_config_de_la_plantilla_es_coherente(self):
        plantilla = build_demo.PLANTILLA.read_text(encoding="utf-8")
        cfg = self.config_de(plantilla)
        recalculado = build_demo.validar(copy.deepcopy(cfg))
        self.assertEqual(cfg["calculado"], recalculado["calculado"])

    def test_ejemplo_json_valido(self):
        cfg = build_demo.cargar(AQUI / "agencias" / "ejemplo.json")
        self.assertTrue(cfg["ejemplo"])
        self.assertIn("(ficticia)", cfg["agencia"]["nombre"])
        ramas = {p["rama"] for p in cfg["calculado"]["pisos"]}
        self.assertEqual(ramas, {"CALIENTE", "REVISAR PRESUPUESTO"})


if __name__ == "__main__":
    unittest.main()
