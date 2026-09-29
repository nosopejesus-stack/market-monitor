"""Tests sin red del modo lote (lote.py) y de la métrica n_puntos_revisar / frase_llamada."""

import csv
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import blindaje  # noqa: E402
import lote  # noqa: E402
import reglas  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
CABECERA = "id,nombre,distrito,direccion,web,telefono_publico,titular_o_director_medico,instagram,cadena,fuente,estado,notas\n"
RELLENO = "<p>" + "Nuestra clínica atiende en el centro de Madrid con un equipo de profesionales. " * 6 + "</p>"


def _h(regla, gravedad, evidencia, sv=""):
    return reglas.Hallazgo(regla=regla, gravedad=gravedad, titulo=f"T {regla}", url="u", ubicacion="texto",
                           evidencia=evidencia, marca_inicio=0, marca_fin=1, accion="", texto_corregido="",
                           base_normativa="", sin_verificar=sv)


def _sin_red(url):
    raise urllib.error.URLError("sin red en el test")


def _escribir(carpeta: Path, archivos: dict):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, html in archivos.items():
        (carpeta / nombre).write_text(html, encoding="utf-8")
    return carpeta


def _leer_resumen(salida: Path):
    with open(salida / "RESUMEN.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


class TestPuntosRevisar(unittest.TestCase):
    def test_incluye_sin_verificar_y_deduplica(self):
        hs = [_h("toxina", reglas.ALTA, "Tratamiento con Bótox."),
              _h("toxina", reglas.ALTA, "tratamiento con botox"),          # misma frase normalizada
              _h("testimonios", reglas.MEDIA, "Opiniones de pacientes", sv="SIN VERIFICAR"),
              _h("testimonios", reglas.MEDIA, "Opiniones de pacientes", sv="SIN VERIFICAR"),
              _h("registro", reglas.ALTA, "", sv="SIN VERIFICAR"),
              _h("cookies", reglas.BAJA, "")]
        self.assertEqual(reglas.n_puntos_norma(hs), 1)
        self.assertEqual(reglas.n_puntos_revisar(hs), 3)

    def test_revisar_nunca_menor_que_norma_en_fixtures(self):
        for sitio in ("sitio_malo", "sitio_limpio"):
            ps = [reglas.extraer(u, h) for u, h in blindaje.cargar_local(FIX / sitio)]
            hs = reglas.analizar(ps)
            self.assertGreaterEqual(reglas.n_puntos_revisar(hs), reglas.n_puntos_norma(hs))

    def test_frase_llamada(self):
        f = reglas.frase_llamada
        self.assertEqual(f(3, 7), "He revisado la publicidad de su web y hay 3 puntos que la normativa de "
                                  "publicidad sanitaria no permite.")
        self.assertEqual(f(1, 1), "He revisado la publicidad de su web y hay 1 punto que la normativa de "
                                  "publicidad sanitaria no permite.")
        self.assertEqual(f(0, 4), "He revisado la publicidad de su web y hay 4 puntos que conviene revisar según "
                                  "la normativa de publicidad sanitaria.")
        self.assertIn("1 punto que conviene", f(0, 1))
        self.assertEqual(f(0, 0), "")
        self.assertEqual(f(5, 5, lectura_fiable=False), "")

    def test_json_e_informe_previo_muestran_puntos_a_revisar(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta, datos, hs = blindaje.ejecutar(blindaje.cargar_local(FIX / "sitio_malo"), "Clínica Mala",
                                                   "https://mala.test", tmp, previo=True, fecha="01/01/2026")
            j = json.loads((carpeta / "informe.json").read_text(encoding="utf-8"))
            self.assertEqual(j["n_puntos_revisar"], reglas.n_puntos_revisar(hs))
            self.assertEqual(j["frase_llamada"], datos["frase_llamada"])
            html = (carpeta / "informe_previo.html").read_text(encoding="utf-8")
            self.assertIn(f"Puntos a revisar: {j['n_puntos_revisar']}", html)
            self.assertNotIn("Texto corregido listo para publicar", html)


class TestSeleccion(unittest.TestCase):
    def test_salta_sin_web_cadena_y_no_llamar(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "c.csv"
            ruta.write_text(CABECERA +
                            "A1,Uno,,,https://uno.test,600,,,no,,,\n"
                            "A2,Dos,,,,601,,,no,,,\n"
                            "A3,Tres,,,https://tres.test,602,,,Sí,,,\n"
                            "A4,Cuatro,,,https://cuatro.test,603,,,no,,,\"pidió no_llamar\"\n"
                            "A5,Cinco,,,https://cinco.test,604,,,no,,,\n", encoding="utf-8")
            filas = lote.leer_clinicas(ruta)
            procesar, saltadas, desc = lote.seleccionar(filas)
            self.assertEqual([f["id"] for f in procesar], ["A1", "A5"])
            self.assertEqual({f["id"]: m for f, m in saltadas}, {"A2": "sin web", "A3": "cadena", "A4": "no_llamar"})
            procesar, saltadas, desc = lote.seleccionar(filas, "A5, A4,ZZ")
            self.assertEqual([f["id"] for f in procesar], ["A5"])
            self.assertEqual([f["id"] for f, _ in saltadas], ["A4"])
            self.assertEqual(desc, ["ZZ"])

    def test_csv_de_excel_con_punto_y_coma_y_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "c.csv"
            ruta.write_bytes(("﻿" + CABECERA.replace(",", ";") +
                              "A1;Clínica Ñ;;;https://uno.test;600;;;no;;;\n").encode("utf-8"))
            filas = lote.leer_clinicas(ruta)
            self.assertEqual(filas[0]["id"], "A1")
            self.assertEqual(filas[0]["nombre"], "Clínica Ñ")

    def test_csv_real_del_proyecto_se_lee(self):
        ruta = RAIZ.parent / "prospectos" / "clinicas.csv"
        if not ruta.is_file():
            self.skipTest("sin CSV de prospectos")
        procesar, saltadas, _ = lote.seleccionar(lote.leer_clinicas(ruta))
        self.assertTrue(procesar)
        self.assertTrue(all(f["web"] for f in procesar))


class TestLote(unittest.TestCase):
    def _lote(self, filas_csv, html_local_id=None, solo=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        ruta = base / "clinicas.csv"
        ruta.write_text(CABECERA + filas_csv, encoding="utf-8")
        salida = base / "informes"
        with redirect_stdout(io.StringIO()):
            res, salt = lote.ejecutar_lote(ruta, salida, solo=solo, contacto={}, html_local_id=html_local_id,
                                           obtener=_sin_red, dormir=lambda s: None, fecha="01/01/2026")
        return base, salida, res, salt

    def test_sin_red_error_por_clinica_y_resumen(self):
        base, salida, res, salt = self._lote(
            "A1,Uno,,,https://uno.invalid,600,,,no,,,\n"
            "A2,Dos,,,http://127.0.0.1:9/,601,,,no,,,\n"
            "A3,Tres,,,http://[mal,602,,,no,,,\n")        # URL mal formada: no debe parar el lote
        self.assertEqual(len(res), 3)
        for r in res:
            self.assertTrue(r["estado"].startswith("error:"), r["estado"])
            self.assertEqual(r["frase_llamada"], "")
            self.assertNotIn("\n", r["estado"])
        self.assertIn("--html-local", res[0]["estado"])
        filas = _leer_resumen(salida)
        self.assertEqual([f["id"] for f in filas], ["A1", "A2", "A3"])
        self.assertEqual(filas[0]["telefono"], "600")
        self.assertTrue((salida / "RESUMEN.html").is_file())

    def test_prioridad_y_frases_con_html_local(self):
        base = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(base, ignore_errors=True))
        # Solo puntos SIN VERIFICAR (testimonios, registro): gancho "conviene revisar".
        revisar = _escribir(base / "revisar", {
            "index.html": "<html><body><h1>Clínica</h1>" + RELLENO +
                          "<a href='opiniones.html'>Opiniones</a></body></html>",
            "opiniones.html": "<html><body><h2>Opiniones de nuestros pacientes</h2>"
                              "<p>“Estoy encantada con el trato” - Ana</p>" + RELLENO + "</body></html>"})
        no_legible = _escribir(base / "js", {"index.html": "<html><body><div id='root'></div></body></html>"})
        base2, salida, res, salt = self._lote(
            "L1,Limpia,,,https://limpia.test,1,,,no,,,\n"
            "N1,No legible,,,https://js.test,2,,,no,,,\n"
            "E1,Error,,,https://error.invalid,3,,,no,,,\n"
            "R1,Revisar,,,https://revisar.test,4,,,no,,,\n"
            "M1,Mala,,,https://mala.test,5,,,no,,,\n"
            "C1,Cadena,,,https://cadena.test,6,,,si,,,\n",
            html_local_id={"L1": str(FIX / "sitio_limpio"), "M1": str(FIX / "sitio_malo"),
                           "R1": str(revisar), "N1": str(no_legible)})
        filas = _leer_resumen(salida)
        self.assertEqual([f["id"] for f in filas], ["M1", "R1", "L1", "N1", "E1"])
        por_id = {f["id"]: f for f in filas}
        m = por_id["M1"]
        self.assertEqual(m["estado"], "ok")
        self.assertIn(f"hay {m['n_puntos_norma']} puntos que la normativa", m["frase_llamada"])
        self.assertTrue(m["hallazgo_principal"])
        r = por_id["R1"]
        self.assertEqual(r["n_puntos_norma"], "0")
        self.assertGreater(int(r["n_puntos_revisar"]), 0)
        self.assertIn("conviene revisar", r["frase_llamada"])
        self.assertEqual(por_id["L1"]["frase_llamada"], "")
        self.assertEqual(por_id["L1"]["estado"], lote.ESTADO_SIN_GANCHO)
        self.assertEqual(por_id["N1"]["lectura_fiable"], "no")
        self.assertEqual(por_id["N1"]["frase_llamada"], "")
        self.assertIn("revisar a mano", por_id["N1"]["estado"])
        self.assertIn("--html-local", por_id["N1"]["estado"])
        self.assertTrue(por_id["E1"]["estado"].startswith("error"))
        self.assertEqual([f["id"] for f, _ in salt], ["C1"])
        # informes por clínica como con blindaje.py --previo
        for id_, sub in (("M1", "mala"), ("R1", "revisar"), ("L1", "limpia")):
            self.assertTrue((salida / sub / "informe_previo.html").is_file(), id_)
            j = json.loads((salida / sub / "informe.json").read_text(encoding="utf-8"))
            self.assertTrue(j["previo"])
            self.assertEqual(j["n_puntos_revisar"], int(por_id[id_]["n_puntos_revisar"]))
        html = (salida / "RESUMEN.html").read_text(encoding="utf-8")
        self.assertIn('href="mala/informe_previo.html"', html)
        self.assertIn("Saltadas", html)
        self.assertNotIn("EN CURSO", html)

    def test_nombres_repetidos_no_se_pisan(self):
        base, salida, res, _ = self._lote(
            "A1,Clínica Igual,,,https://a.test,1,,,no,,,\n"
            "A2,Clínica Igual,,,https://b.test,2,,,no,,,\n",
            html_local_id={"A1": str(FIX / "sitio_malo"), "A2": str(FIX / "sitio_limpio")})
        self.assertNotEqual(res[0]["informe"], res[1]["informe"])
        for r in res:
            self.assertTrue((salida / r["informe"]).is_file())

    def test_carpeta_local_inexistente_no_para_el_lote(self):
        _, _, res, _ = self._lote("A1,Uno,,,https://a.test,1,,,no,,,\nA2,Dos,,,https://b.test,2,,,no,,,\n",
                                  html_local_id={"A1": "/no/existe/ninguna/carpeta",
                                                 "A2": str(FIX / "sitio_malo")})
        self.assertTrue(res[0]["estado"].startswith("error"))
        self.assertEqual(res[1]["estado"], "ok")

    def test_cli_con_opcion_oculta_y_solo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "c.csv"
            ruta.write_text(CABECERA + "A1,Uno,,,https://a.test,1,,,no,,,\n"
                                       "A2,Dos,,,https://b.test,2,,,no,,,\n", encoding="utf-8")
            salida = Path(tmp) / "inf"
            out = io.StringIO()
            with redirect_stdout(out):
                code = lote.main([str(ruta), "--solo", "A1", "--salida", str(salida),
                                  "--html-local-id", f"A1={FIX / 'sitio_malo'}",
                                  "--contacto-nombre", "Tu Nombre", "--contacto-telefono", "600 000 000"])
            self.assertEqual(code, 0)
            self.assertEqual([f["id"] for f in _leer_resumen(salida)], ["A1"])
            html = (salida / "uno" / "informe_previo.html").read_text(encoding="utf-8")
            self.assertIn("Tu Nombre", html)
            ayuda = io.StringIO()
            with redirect_stdout(ayuda), self.assertRaises(SystemExit):
                lote.main(["--help"])
            self.assertNotIn("html-local-id", ayuda.getvalue())


if __name__ == "__main__":
    unittest.main()
