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


class TestIntegradoRiskScanner(unittest.TestCase):
    """Lo traído del risk-scanner antiguo (2026-09-29): promesas nuevas y detector de cadena."""

    def _pag(self, texto, url="https://c.test/tratamientos"):
        return reglas.extraer(url, f"<html><body><p>{texto}</p></body></html>")

    def test_promesas_nuevas(self):
        for frase in ("Tratamiento facial 100% eficaz.", "Depilación láser con resultados permanentes.",
                      "La cura definitiva para el acné.", "Relleno de labios con resultados para siempre."):
            hs = reglas.regla_promesas(self._pag(frase))
            self.assertEqual(len(hs), 1, frase)
            self.assertEqual(hs[0].gravedad, reglas.ALTA, frase)

    def test_promesas_nuevas_sin_falsos_positivos(self):
        for frase in ("El resultado definitivo se aprecia a las dos semanas del tratamiento.",
                      "Los resultados no son permanentes: el tratamiento se repite cada año.",
                      "Pago 100% eficaz y seguro con tarjeta.",
                      "Ningún tratamiento es 100% eficaz en todas las pieles."):
            self.assertEqual(reglas.regla_promesas(self._pag(frase)), [], frase)

    def test_texto_corregido_de_100_eficaz(self):
        h = reglas.regla_promesas(self._pag("Tratamiento facial 100% eficaz."))[0]
        self.assertNotIn("100", h.texto_corregido)
        self.assertIn("valoración médica", h.texto_corregido)

    def test_cadena_con_lenguaje_y_varios_registros(self):
        ps = [self._pag("Visite nuestras clínicas de Madrid y Marbella. Elige tu clínica."),
              self._pag("Madrid: CS12345. Marbella: NICA 67890.", "https://c.test/aviso-legal")]
        s = reglas.senales_cadena(ps)
        self.assertEqual(len(s), 3)
        self.assertIn("nuestras clinicas", s[0])
        self.assertIn("2 números de registro", s[1])
        self.assertIn("marbella", s[2])

    def test_sede_unica_sin_senales(self):
        ps = [self._pag("Las mejores clínicas en Madrid. Únete a nuestra newsletter. La doctora se formó en "
                        "Barcelona y Valencia."),
              self._pag("Centro sanitario CS12345.", "https://c.test/aviso-legal")]
        self.assertEqual(reglas.senales_cadena(ps), [])

    def test_cadena_no_va_al_informe_de_la_clinica(self):
        with tempfile.TemporaryDirectory() as tmp:
            paginas = [("https://c.test/", "<p>" + "Nuestros centros en Madrid y Barcelona. " * 10 + "</p>"),
                       ("https://c.test/b", "<p>Elige tu centro.</p>")]
            carpeta, datos, _ = blindaje.ejecutar(paginas, "Clínica Uno", "https://c.test", tmp, previo=True)
            self.assertTrue(datos["senales_cadena"])
            html = (carpeta / "informe_previo.html").read_text(encoding="utf-8")
            self.assertNotIn("cadena", reglas.plegar(html))
            self.assertNotIn("senales", html)


class TestReanalizar(unittest.TestCase):
    def test_guarda_copia_y_reanaliza_sin_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp)
            paginas = {"https://c.test/": "<html><body><p>" + "Nuestra clínica. " * 30 + "</p>"
                                         "<a href='/b'>b</a></body></html>",
                       "https://c.test/b": "<html><body><p>Tratamiento con bótox.</p></body></html>",
                       "https://c.test/robots.txt": ""}

            def obtener(url):
                if url not in paginas:
                    return 404, url, "text/html", b""
                return 200, url, "text/html", paginas[url].encode("utf-8")

            fila = {"id": "A1", "nombre": "Uno", "web": "https://c.test/", "telefono_publico": "600"}
            with redirect_stdout(io.StringIO()):
                r1 = lote.procesar_clinica(fila, salida, obtener=obtener, dormir=lambda s: None, subcarpeta="uno")
            self.assertTrue((salida / "uno" / lote.CACHE).is_file())
            with redirect_stdout(io.StringIO()):
                r2 = lote.procesar_clinica(fila, salida, obtener=_sin_red, dormir=lambda s: None,
                                           subcarpeta="uno", reanalizar=True)
            self.assertEqual(r2["estado"], r1["estado"])
            self.assertEqual(r2["n_puntos_norma"], r1["n_puntos_norma"])
            self.assertGreaterEqual(r1["n_puntos_norma"], 1)


class TestFalsosPositivosLoteReal(unittest.TestCase):
    """Falsos positivos vistos en el lote real del 29-09-2026 (webs de clínicas de Madrid)."""

    def _pag(self, texto, url="https://c.test/tratamientos"):
        return reglas.extraer(url, f"<html><body><p>{texto}</p></body></html>")

    def _regla(self, regla, frase):
        return regla(self._pag(frase))

    def test_garantizar_como_finalidad_o_sin_resultado_no_es_promesa(self):
        for frase in ("Para garantizar la comodidad del paciente, aplicamos una crema anestésica en la zona.",
                      "Para garantizar los mejores resultados, es importante elegir un médico con experiencia.",
                      "Seguir las indicaciones del especialista para garantizar los mejores resultados.",
                      "Nuestro enfoque personalizado garantiza que el tratamiento se adapte a cada zona.",
                      "Instalaciones equipadas con la última tecnología para garantizar tu comodidad en el tratamiento.",
                      "Seguridad y garantías del tratamiento.",
                      "¿Dónde hacer un relleno de labios con garantías?",
                      "La cara es sensible, por lo que es imposible garantizar un procedimiento completamente indoloro."):
            self.assertEqual(self._regla(reglas.regla_promesas, frase), [], frase)

    def test_garantizar_resultados_sigue_siendo_promesa(self):
        for frase in ("Técnicas innovadoras que garantizan resultados naturales en el tratamiento.",
                      "Tratamiento facial: resultados garantizados.",
                      "Profesionales expertos que garantizan resultados visibles desde la primera sesión."):
            hs = self._regla(reglas.regla_promesas, frase)
            self.assertEqual(len(hs), 1, frase)
            self.assertEqual(hs[0].gravedad, reglas.ALTA, frase)

    def test_consulta_gratuita_no_es_promocion(self):
        for frase in ("1ª valoración médica gratuita para su tratamiento de arrugas.",
                      "Diagnóstico gratuito antes de cualquier tratamiento.",
                      "Reserva una consulta gratuita para tu tratamiento facial.",
                      "En la clínica no participamos en promociones masivas del tratamiento.",
                      "Te ofrecemos soluciones médico estéticas basadas en una amplia oferta de tratamientos."):
            self.assertEqual(self._regla(reglas.regla_promociones, frase), [], frase)

    def test_promocion_real_sigue_saliendo(self):
        for frase in ("Tratamiento antiarrugas en oferta por solo 199 €.", "Promoción de septiembre en relleno de labios.",
                      "Tratamiento de mesoterapia gratis al comprar un bono de sesiones."):
            self.assertEqual(len(self._regla(reglas.regla_promociones, frase)), 1, frase)

    def test_prosa_sobre_antes_y_despues_no_es_galeria(self):
        for frase in ("Luego pondré resultados del antes y después.",
                      "Hay una imagen que muchas personas conocen: la foto de antes y después de unos labios exagerados."):
            self.assertEqual(self._regla(reglas.regla_antes_despues, frase), [], frase)
        self.assertEqual(len(self._regla(reglas.regla_antes_despues, "Fotos del antes y después")), 1)

    def test_consejo_de_leer_opiniones_no_es_testimonio(self):
        frase = ("En primer lugar, la credibilidad de la clínica: revisa referencias, opiniones de pacientes e "
                 "incluso su trayectoria.")
        self.assertEqual(self._regla(reglas.regla_testimonios, frase), [])
        self.assertEqual(len(self._regla(reglas.regla_testimonios, "Lo que dicen nuestros pacientes")), 1)



class TestRevisionManualLoteReal(unittest.TestCase):
    """Falsos positivos que encontró la revisión a mano (revisor) de los 996 hallazgos del lote real, 29-09-2026."""

    def _pag(self, cuerpo, url="https://c.test/tratamientos"):
        return reglas.extraer(url, f"<html><body>{cuerpo}</body></html>")

    def _p(self, texto):
        return self._pag(f"<p>{texto}</p>")

    # -- promociones -----------------------------------------------------
    def test_consultas_citas_y_telefonos_gratuitos_no_son_promocion(self):
        for frase in ("Ofrecemos un diagnóstico completo, gratuito y honesto de su tratamiento facial.",
                      "Siempre previa cita gratuita con la Dra. para su tratamiento.",
                      "Dudas y consultas gratis sobre cualquier tratamiento.",
                      "Pide Cita Gratuita para tu tratamiento de labios.",
                      "Pídenos asesoramiento gratuito sobre el tratamiento.",
                      "1ª Cita y diagnóstico ¡GRATIS! en medicina estética.",
                      "Línea gratuita 900 902 623 para pedir su tratamiento.",
                      "Precio: (Se reintegra de tu compra o tratamiento, es decir, gratuito)."):
            hs = reglas.regla_promociones(self._p(frase))
            self.assertEqual(hs, [], frase)

    def test_otros_sentidos_de_oferta_y_promocion(self):
        for frase in ("Tenemos la mejor oferta posible de tratamientos faciales en Madrid.",
                      "Chequeos generales, promoción y prevención en salud y tratamientos.",
                      "Ha formado más de 5 promociones médicas en tratamientos de medicina estética.",
                      "Los tratamientos médicos son incompatibles con ese tipo de ofertas.",
                      "Acepto recibir la newsletter con ofertas de tratamientos de la clínica."):
            self.assertEqual(reglas.regla_promociones(self._p(frase)), [], frase)

    def test_promocion_de_tratamiento_no_medico_no_cuenta(self):
        for frase in ("Limpieza 5en1 personalizada y terapia LED. Incluye valoración dermo-cosmética. Ahora: 49,90€ Antes 90€",
                      "Bono 5 sesiones de maderoterapia facial: 200 €.",
                      "BONO 5 SESIONES de terapia EMDR (psicología): 350 €."):
            self.assertEqual(reglas.regla_promociones(self._p(frase)), [], frase)

    def test_promocion_sin_precio_queda_para_revisar_y_no_cuenta_en_n(self):
        hs = reglas.regla_promociones(self._pag("<nav><a href='/promociones'>Promociones</a> "
                                                "<a href='/t'>Tratamientos</a></nav><p>Relleno de labios.</p>"))
        self.assertEqual([(h.regla, h.gravedad) for h in hs], [("promociones_revisar", reglas.BAJA)])
        self.assertEqual(reglas.n_puntos_norma(hs), 0)
        self.assertEqual(reglas.n_puntos_revisar(hs), 0)

    def test_promocion_con_precio_cuenta_y_es_la_evidencia(self):
        hs = reglas.regla_promociones(self._pag(
            "<nav><a href='/promociones'>Promociones</a></nav>"
            "<p>Bonos anuales de tratamiento.</p><p>15% de descuento en aumento de labios con el código VERANO26.</p>"))
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].gravedad, reglas.MEDIA)
        self.assertIn("15%", hs[0].evidencia)

    # -- reseñas de pacientes --------------------------------------------
    def test_resena_en_widget_no_cuenta_como_publicidad_de_la_clinica(self):
        p = self._pag("<p>Medicina estética facial en Madrid.</p>"
                      "<div class='ti-widget ti-reviews'><div class='ti-review-item'>"
                      "<p>Acudí para ponerme botox y el resultado fue muy natural. El procedimiento fue indoloro.</p>"
                      "</div></div>")
        self.assertEqual(reglas.regla_toxina(p), [])
        self.assertEqual(reglas.regla_promesas(p), [])
        hs = reglas.regla_testimonios(p)
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].ubicacion, "bloque de reseñas o testimonios")

    def test_resena_pegada_como_texto_baja_a_revisar(self):
        hs = reglas.regla_toxina(self._p("Lleve a mi madre y el doctor le ha ido poniendo ácido hialurónico y botox."))
        self.assertEqual([h.regla for h in hs], ["toxina_revisar"])

    def test_clase_css_sola_no_es_testimonio(self):
        p = self._pag("<div class='widget-testimonial-carousel-css'></div><p>Tratamientos faciales.</p>")
        self.assertEqual(reglas.regla_testimonios(p), [])

    # -- toxina ----------------------------------------------------------
    def test_curriculum_del_medico_baja_a_revisar(self):
        for frase in ("Formación avanzada en técnicas de toxina botulínica, hilos tensores y rellenos.",
                      "Médico general con formación en neuromoduladores y ecografía."):
            hs = reglas.regla_toxina(self._p(frase))
            self.assertEqual([h.regla for h in hs], ["toxina_revisar"], frase)

    def test_pack_cosmetico_post_toxina_no_es_el_medicamento(self):
        self.assertEqual(reglas.regla_toxina(self._p("Pack POST-TOXINA de SkinCeuticals.")), [])

    def test_toxina_ofrecida_sigue_siendo_alta(self):
        hs = reglas.regla_toxina(self._p("Neuromoduladores (Bot*x): ahora 385 €, antes 505 €."))
        self.assertEqual([h.gravedad for h in hs], [reglas.ALTA])

    # -- promesas --------------------------------------------------------
    def test_promesas_falsas_de_la_revision(self):
        for frase in ("La mayoría son indoloros o ligeramente molestos.",
                      "Los tratamientos suelen ser indoloros.",
                      "Generalmente son indoloros.",
                      "Un procedimiento sin dolor significativo, no invasivo.",
                      "Algunas personas encuentran el láser indoloro, otras perciben algo de dolor.",
                      "Recupere una vida sin dolor ni molestias provocadas por el bruxismo.",
                      "Mejora tu alimentación de forma médica, sin dietas milagro.",
                      "Recupera tu peso ideal sin hacer dietas “milagro”.",
                      "Trabajó en Vithas La Milagrosa como médico estético.",
                      "Es importante asistir a las revisiones médicas para garantizar un buen resultado.",
                      "El producto está regulado por la AEMPS, que se encarga de garantizar la seguridad y eficacia.",
                      "Esto garantiza la continuidad del tratamiento y su efectividad.",
                      "Esto puede ser un beneficio, sin obtener unos resultados permanentes.",
                      "Masaje DrenoRedux: resultados inmediatos, sin dolor ni aparatos."):
            self.assertEqual(reglas.regla_promesas(self._p(frase)), [], frase)

    def test_sin_riesgo_concreto_es_media(self):
        hs = reglas.regla_promesas(self._p("El cuerpo asimila el ácido hialurónico sin riesgo de rechazo."))
        self.assertEqual([h.gravedad for h in hs], [reglas.MEDIA])

    # -- antes y después y registro --------------------------------------
    def test_antes_y_despues_sin_fotos(self):
        for frase in ("¿Qué precauciones debo tener antes y después del tratamiento?",
                      "¿Cuáles son los resultados de la mesoterapia corporal antes y después?"):
            self.assertEqual(reglas.regla_antes_despues(self._p(frase)), [], frase)

    def test_consejo_sobre_autorizacion_no_es_mencion_del_registro(self):
        legal = reglas.extraer("https://c.test/aviso-legal", "<p>Aviso legal. Registro sanitario CS12345.</p>")
        consejo = self._p("Asegúrate de que la clínica cuente con la autorización sanitaria U48.")
        self.assertEqual(reglas.regla_registro([consejo, legal]), [])
        estado, _ = reglas.estado_registro([consejo])
        self.assertEqual(estado, "ausente")

    def test_precio_en_la_linea_siguiente_es_promocion_concreta(self):
        hs = reglas.regla_promociones(self._pag("<div><h3>Promoción</h3><p>280 €</p><p>Neuromoduladores</p></div>"))
        self.assertEqual([(h.regla, h.gravedad) for h in hs], [("promociones", reglas.MEDIA)])

    def test_pregunta_de_blog_y_bono_con_precio_no_cuentan_en_n(self):
        for frase in ("Descuento de la inyección de toxina botulínica (Botox) ¿es posible?",
                      "HIFU facial: el bono de 3 sesiones 1100 €."):
            hs = reglas.regla_promociones(self._p(frase))
            self.assertEqual(reglas.n_puntos_norma(hs), 0, frase)
        hs = reglas.regla_promociones(self._p("Relleno de labios: precio bono (-10%) en 3 sesiones."))
        self.assertEqual(reglas.n_puntos_norma(hs), 1)

    def test_precio_antes_y_ahora_es_promocion(self):
        hs = reglas.regla_promociones(self._p("Neuromoduladores (Bot*x) Ahora: 385€ Antes: 505€"))
        self.assertEqual([(h.regla, h.gravedad) for h in hs], [("promociones", reglas.MEDIA)])

    def test_n_cuenta_tipos_de_punto_no_frases(self):
        ps = [self._p("Tratamiento con bótox en la frente."), self._p("Neuromoduladores para el entrecejo."),
              self._p("Relleno de labios: 20% de descuento este mes.")]
        hs = reglas.analizar(ps, ausencias=False)
        self.assertEqual(reglas.n_puntos_norma(hs), 2)          # toxina + promociones

    def test_index_html_y_raiz_son_la_misma_pagina(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = "<p>" + "Clínica de medicina estética en Madrid. " * 10 + "</p>"
            _, datos, _ = blindaje.ejecutar([("https://c.test/", html), ("https://c.test/index.html", html),
                                            ("https://c.test/b", "<p>Otra página.</p>")], "Uno", "https://c.test", tmp)
            self.assertEqual(len(datos["paginas"]), 2)
