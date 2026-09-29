"""Tests sin red del escáner pasivo de cumplimiento de la web (escaner.py)."""

import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import blindaje  # noqa: E402
import escaner  # noqa: E402
import reglas  # noqa: E402

RELLENO = "<p>" + "Clínica de medicina estética en Madrid con un equipo médico. " * 8 + "</p>"


def _pags(*htmls):
    return [(f"https://c.test/p{i}", h) for i, h in enumerate(htmls)]


class TestCertificado(unittest.TestCase):
    def test_caducado_y_no_valido_son_media(self):
        for est in ("caducado", "no_valido"):
            hs = escaner.regla_certificado("https://c.test", {"estado": est, "dias": None, "detalle": "x"})
            self.assertEqual([(h.regla, h.gravedad) for h in hs], [("web_certificado", reglas.MEDIA)], est)

    def test_caduca_pronto_es_baja_y_ok_no_dice_nada(self):
        hs = escaner.regla_certificado("https://c.test", {"estado": "caduca_pronto", "dias": 10, "detalle": "09/10/2026"})
        self.assertEqual([h.gravedad for h in hs], [reglas.BAJA])
        self.assertEqual(escaner.regla_certificado("https://c.test", {"estado": "ok", "dias": 80, "detalle": ""}), [])
        # sin conexión no se afirma nada
        self.assertEqual(escaner.regla_certificado("https://c.test", {"estado": "sin_conexion", "dias": None,
                                                                       "detalle": ""}), [])

    def test_http_sin_certificado(self):
        hs = escaner.regla_certificado("http://c.test", None)
        self.assertEqual([h.regla for h in hs], ["web_https"])

    def test_comprobar_certificado_sin_red_no_rompe(self):
        r = escaner.comprobar_certificado("host-que-no-existe.invalid", timeout=2)
        self.assertEqual(r["estado"], "sin_conexion")


class TestCookies(unittest.TestCase):
    def test_analitica_sin_gestor(self):
        hs = escaner.regla_cookies(_pags("<script async src='https://www.googletagmanager.com/gtag/js?id=G-1'></script>"
                                         "<script>fbq('init', '1');</script>" + RELLENO))
        self.assertEqual(len(hs), 1)
        self.assertIn("Google Analytics", hs[0].evidencia)
        self.assertIn("Meta", hs[0].evidencia)
        self.assertTrue(hs[0].sin_verificar)
        self.assertEqual(hs[0].gravedad, reglas.BAJA)      # sin ver el navegador no se afirma

    def test_gestor_propio_con_nombre_de_banner(self):
        self.assertEqual(escaner.regla_cookies(_pags("<div class='cookies-consent'>Usamos cookies</div>"
                                                     "<script>fbq('init', '1');</script>")), [])

    def test_con_gestor_o_sin_analitica_no_sale(self):
        self.assertEqual(escaner.regla_cookies(_pags(
            "<script src='https://consent.cookiebot.com/uc.js'></script>"
            "<script src='https://www.googletagmanager.com/gtag/js'></script>")), [])
        self.assertEqual(escaner.regla_cookies(_pags(
            "<script>gtag('consent', 'default', {});</script><script src='https://www.googletagmanager.com/gtag/js'>"
            "</script>")), [])
        self.assertEqual(escaner.regla_cookies(_pags(RELLENO)), [])


class TestFormularios(unittest.TestCase):
    def test_formulario_sin_privacidad(self):
        hs = escaner.regla_formularios(_pags("<form><input type='text' name='nombre'><input type='email' name='mail'>"
                                             "<input type='tel' name='tel'><button>Enviar</button></form>"))
        self.assertEqual([(h.regla, h.gravedad) for h in hs], [("web_formulario", reglas.MEDIA)])
        self.assertIn("correo y teléfono", hs[0].evidencia)

    def test_formulario_montado_con_javascript_no_sale(self):
        self.assertEqual(escaner.regla_formularios(_pags(
            "<form><script>t_onReady(function(){})</script><input type='tel' name='phone'></form>")), [])

    def test_formulario_con_aviso_o_buscador_no_sale(self):
        self.assertEqual(escaner.regla_formularios(_pags(
            "<form><input type='email' name='email'><label><input type='checkbox'> Acepto la "
            "<a href='/privacidad'>política de privacidad</a></label></form>")), [])
        self.assertEqual(escaner.regla_formularios(_pags(
            "<form><input type='email' name='email'></form><p>Responsable: Clínica X SL. Más información en la "
            "política de privacidad.</p>")), [])       # aviso justo debajo del formulario
        self.assertEqual(escaner.regla_formularios(_pags(
            "<form role='search'><input type='search' name='s'></form>")), [])


class TestEnlacesYRegistro(unittest.TestCase):
    def test_enlace_legal_roto(self):
        hs = escaner.regla_enlaces_legales(["https://c.test/aviso-legal respondió 404.",
                                            "https://c.test/blog respondió 404."])
        self.assertEqual(len(hs), 1)
        self.assertIn("aviso-legal", hs[0].evidencia)
        self.assertNotIn("blog", hs[0].evidencia)

    def test_registro_distinto(self):
        ps = [reglas.extraer("https://c.test/", "<footer>Registro sanitario: CS-13529</footer>")]
        hs = escaner.regla_registro_distinto(ps, "CS18040")
        self.assertEqual([h.regla for h in hs], ["web_registro_distinto"])
        self.assertIn("CS13529", hs[0].evidencia)
        self.assertEqual(escaner.regla_registro_distinto(ps, "CS13529"), [])
        self.assertEqual(escaner.regla_registro_distinto(ps, "CS18040 (probable)"), [])   # dato no seguro
        self.assertEqual(escaner.regla_registro_distinto(ps, "SIN VERIFICAR"), [])


class TestIntegracion(unittest.TestCase):
    def test_no_cuenta_en_la_frase_de_la_llamada(self):
        with tempfile.TemporaryDirectory() as tmp:
            paginas = [("https://c.test/", RELLENO + "<form><input type='email' name='email'></form>"
                        "<script src='https://www.googletagmanager.com/gtag/js'></script>"),
                       ("https://c.test/aviso-legal", "<p>Aviso legal. Registro sanitario CS12345.</p>")]
            _, datos, hs = blindaje.ejecutar(paginas, "Clínica Uno", "https://c.test", tmp, previo=True,
                                             certificado={"estado": "caducado", "dias": None, "detalle": ""})
            reglas_web = {h.regla for h in hs if h.regla.startswith("web_")}
            self.assertEqual(reglas_web, {"web_certificado", "web_cookies", "web_formulario"})
            self.assertEqual(datos["n_puntos_norma"], 0)
            self.assertEqual(datos["n_incumplimientos_web"], 2)          # cookies es BAJA: no cuenta
            self.assertEqual(datos["frase_llamada"], "")


if __name__ == "__main__":
    unittest.main()
