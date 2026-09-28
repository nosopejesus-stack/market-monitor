"""Tests sin red de la herramienta Blindaje.

Ejecutar desde la carpeta blindaje/:
    python -m unittest discover -s tests -v
"""

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import blindaje  # noqa: E402
import informe  # noqa: E402
import reglas  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def pagina(nombre, url=None):
    ruta = FIX / "reglas" / nombre
    return reglas.extraer(url or f"https://clinica.test/{nombre}", ruta.read_text(encoding="utf-8"))


def por_pagina(p):
    return [h for regla in reglas.REGLAS_POR_PAGINA for h in regla(p)]


class TestTexto(unittest.TestCase):
    def test_plegar_conserva_longitud(self):
        t = "Bótox, ÁCIDO hialurónico, reseñas, nº İ"
        self.assertEqual(len(reglas.plegar(t)), len(t))
        self.assertIn("botox", reglas.plegar(t))
        self.assertIn("resenas", reglas.plegar(t))

    def test_extraccion_omite_scripts_y_recoge_meta(self):
        p = pagina("toxina.html")
        self.assertNotIn("Dysport", p.texto)
        self.assertIn("Bótox", p.titulo)
        self.assertIn("toxina botulínica", p.descripcion)
        self.assertEqual(p.imagenes[0][1], "Sesión de Xeomin en frente")

    def test_fragmento_marca_la_coincidencia(self):
        texto = "Primera frase. Aquí va el bótox de la clínica. Otra frase."
        i = texto.index("bótox")
        ev, a, b = reglas.fragmento(texto, i, i + 5)
        self.assertEqual(ev, "Aquí va el bótox de la clínica.")
        self.assertEqual(ev[a:b], "bótox")


class TestToxina(unittest.TestCase):
    def test_detecta_marcas_hashtags_y_meta(self):
        hs = reglas.regla_toxina(pagina("toxina.html"))
        self.assertEqual(len(hs), 1)
        h = hs[0]
        self.assertEqual(h.gravedad, reglas.ALTA)
        self.assertEqual(h.evidencia[h.marca_inicio:h.marca_fin], "Vistabel")
        self.assertGreaterEqual(h.apariciones, 6)
        self.assertTrue(h.texto_corregido)
        self.assertNotRegex(reglas.plegar(h.texto_corregido), r"botox|toxina|neuromodul")

    def test_hashtag_y_url(self):
        p = reglas.extraer("https://c.test/tratamientos/botox-madrid/", "<p>Hola #botoxmadrid</p>")
        h = reglas.regla_toxina(p)[0]
        self.assertIn("dirección de la página también", h.accion)

    def test_no_detecta_toxinas_detox_ni_scripts(self):
        self.assertEqual(reglas.regla_toxina(pagina("falsos_positivos.html")), [])


class TestPromesas(unittest.TestCase):
    def test_detecta_cada_promesa(self):
        hs = reglas.regla_promesas(pagina("promesas.html"))
        titulos = " ".join(h.titulo for h in hs)
        for pid in ("resultados garantizados", "garantía", "sin riesgo", "sin efectos secundarios",
                    "100 % seguro", "sin dolor", "milagro"):
            self.assertIn(f"«{pid}»", titulos)
        self.assertTrue(all(h.gravedad == reglas.ALTA for h in hs))

    def test_textos_corregidos_ya_no_infringen(self):
        for h in reglas.regla_promesas(pagina("promesas.html")):
            p = reglas.extraer("https://c.test/x", f"<p>{h.texto_corregido}</p>")
            self.assertEqual(reglas.regla_promesas(p), [], h.texto_corregido)
            self.assertIn("varían", h.texto_corregido)

    def test_correccion_frase_concreta(self):
        self.assertTrue(reglas.corregir_promesa("Relleno de labios sin efectos secundarios.").startswith(
            "Relleno de labios con posibles efectos secundarios"))
        # si sigue prometiendo un plazo, se usa el texto genérico
        self.assertTrue(reglas.corregir_promesa("Garantizamos que tus arrugas desaparecerán en una semana.")
                        .startswith(reglas.TEXTO_PROMESA_GENERICO))

    def test_falsos_positivos(self):
        self.assertEqual(reglas.regla_promesas(pagina("falsos_positivos.html")), [])

    def test_varias_promesas_en_una_frase(self):
        p = reglas.extraer("https://c.test/x", "<p>Relleno de labios sin dolor y sin efectos secundarios.</p>")
        hs = reglas.regla_promesas(p)
        self.assertEqual(len(hs), 1)
        self.assertIn("«sin dolor»", hs[0].titulo)
        self.assertIn("«sin efectos secundarios»", hs[0].titulo)
        self.assertTrue(hs[0].texto_corregido.startswith("Relleno de labios con mínimas molestias y con posibles"))


class TestRegistro(unittest.TestCase):
    def test_con_cs(self):
        self.assertEqual(reglas.regla_registro([pagina("registro_cs.html")]), [])

    def test_mencion_sin_numero_es_media(self):
        hs = reglas.regla_registro([pagina("registro_sin_numero.html")])
        self.assertEqual([h.gravedad for h in hs], [reglas.MEDIA])
        self.assertIn("registro sanitario", hs[0].evidencia[hs[0].marca_inicio:hs[0].marca_fin])

    def test_ausente_es_alta_y_registro_mercantil_no_cuenta(self):
        hs = reglas.regla_registro([pagina("falsos_positivos.html")])
        self.assertEqual([h.gravedad for h in hs], [reglas.ALTA])
        self.assertIn("{numero_registro_sanitario}", hs[0].texto_corregido)


class TestMedias(unittest.TestCase):
    def test_promociones(self):
        hs = reglas.regla_promociones(pagina("promociones.html"))
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].gravedad, reglas.MEDIA)
        self.assertGreaterEqual(hs[0].apariciones, 4)  # black friday, dto, bono, gratis, 2x1

    def test_promociones_falsos_positivos(self):
        self.assertEqual(reglas.regla_promociones(pagina("falsos_positivos.html")), [])

    def test_antes_despues_imagenes_enlaces_y_titular(self):
        hs = reglas.regla_antes_despues(pagina("antes_despues.html"))
        self.assertEqual(len(hs), 1)
        h = hs[0]
        self.assertEqual(h.ubicacion, "texto de la página")
        self.assertGreaterEqual(h.apariciones, 4)  # titular, archivo, alt before after, enlace
        self.assertIn("SIN VERIFICAR", h.sin_verificar)

    def test_antes_despues_consejo_no_cuenta(self):
        self.assertEqual(reglas.regla_antes_despues(pagina("falsos_positivos.html")), [])

    def test_testimonios(self):
        hs = reglas.regla_testimonios(pagina("testimonios.html"))
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].gravedad, reglas.MEDIA)
        self.assertEqual(hs[0].apariciones, 2)  # texto + class="testimonials-slider"

    def test_paginas_legales_no_se_revisan_como_publicidad(self):
        p = reglas.extraer("https://c.test/privacidad.html",
                           (FIX / "sitio_limpio" / "privacidad.html").read_text(encoding="utf-8"))
        self.assertTrue(p.es_legal)
        self.assertEqual(por_pagina(p), [])


class TestBajas(unittest.TestCase):
    def test_faltan_legales(self):
        hs = reglas.reglas_legales([pagina("promesas.html")])
        self.assertEqual({h.regla for h in hs}, {"aviso_legal", "privacidad", "cookies"})
        self.assertTrue(all(h.gravedad == reglas.BAJA for h in hs))

    def test_legales_presentes_por_enlace(self):
        self.assertEqual(reglas.reglas_legales([pagina("registro_sin_numero.html")]), [])

    def test_privacidad_de_datos_no_cuenta_como_politica(self):
        p = reglas.extraer("https://c.test/", "<p>Garantizamos su privacidad.</p>")
        self.assertIn("privacidad", {h.regla for h in reglas.reglas_legales([p])})

    def test_medico_sin_colegiado_sin_verificar(self):
        hs = reglas.regla_medico([pagina("registro_sin_numero.html")])
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].gravedad, reglas.BAJA)
        self.assertIn("nº de colegiado", hs[0].titulo)
        self.assertIn("SIN VERIFICAR", hs[0].sin_verificar)
        hs2 = reglas.regla_medico([pagina("promesas.html")])
        self.assertIn("médico responsable", hs2[0].titulo)


class TestPuntuacion(unittest.TestCase):
    def _h(self, regla, grav):
        return reglas.Hallazgo(regla, grav, "t", "u", "x", "e", 0, 0, "a", "c", "b")

    def test_sin_hallazgos(self):
        self.assertEqual(reglas.puntuar([]), (100, "A"))

    def test_un_alta_limita_a_c(self):
        self.assertEqual(reglas.puntuar([self._h("registro", "ALTA")]), (75, "C"))

    def test_repeticiones_restan_menos_con_tope(self):
        tres = [self._h("toxina", "ALTA")] * 3
        self.assertEqual(reglas.puntuar(tres)[0], 62)  # 100 - 25 * 1.5 = 62.5 -> 62
        veinte = [self._h("toxina", "ALTA")] * 20
        self.assertEqual(reglas.puntuar(veinte)[0], 50)

    def test_bajas(self):
        self.assertEqual(reglas.puntuar([self._h("cookies", "BAJA"), self._h("medico", "BAJA")]), (92, "A"))


class TestInformeYCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _ejecutar(self, carpeta, nombre):
        paginas = blindaje.cargar_local(FIX / carpeta)
        return blindaje.ejecutar(paginas, nombre, "https://clinica.test", self.tmp.name, fecha="28/09/2026")

    def test_sitio_limpio(self):
        carpeta, datos, hs = self._ejecutar("sitio_limpio", "Clínica Limpia")
        self.assertEqual(hs, [], [h.titulo for h in hs])
        self.assertEqual((datos["puntuacion"], datos["nota"]), (100, "A"))
        self.assertEqual(datos["paginas"][0], "index.html")

    def test_sitio_malo(self):
        carpeta, datos, hs = self._ejecutar("sitio_malo", "Clínica Malo & Cía")
        reglas_vistas = {h.regla for h in hs}
        self.assertTrue({"toxina", "promesas", "registro", "promociones", "antes_despues", "testimonios",
                         "aviso_legal", "privacidad", "cookies", "medico"} <= reglas_vistas)
        self.assertEqual(datos["nota"], "E")
        self.assertEqual(carpeta.name, "clinica-malo-cia")
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        js = json.loads((carpeta / "informe.json").read_text(encoding="utf-8"))
        self.assertEqual(len(js["hallazgos"]), len(hs))
        self.assertEqual(len(js["resumen"]), 3)
        # contenido obligatorio
        self.assertIn(informe.NOTA_METODOLOGICA, html)
        self.assertIn("robots.txt", html)  # modo web por defecto
        self.assertIn("Revisión basada solo en información pública, sin acceder a ningún sistema. "
                      "No constituye asesoramiento jurídico.", html)
        for txt in ("Resumen para el titular", "Hallazgos", "Texto corregido listo para publicar",
                    "Próximos pasos", "390 €", "190 €/mes", "{nombre_contacto}", "{telefono_contacto}",
                    "{email_contacto}", "@page", "size: A4", "<mark>"):
            self.assertIn(txt, html)
        # regla comercial: nunca "IA"
        self.assertNotRegex(html, r"\bIA\b")
        self.assertNotIn("inteligencia artificial", html.lower())
        # autocontenido: sin recursos externos
        self.assertNotRegex(html, r"<(script|link)\b|src=\"http")

    def test_escapa_contenido_de_la_web(self):
        paginas = [("index.html", "<p>Resultados garantizados &lt;script&gt;alert(1)&lt;/script&gt; en su piel.</p>")]
        carpeta, _, hs = blindaje.ejecutar(paginas, "X", "https://x.test", self.tmp.name)
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("&lt;script&gt;alert(1)", html)

    def test_contacto_rellena_placeholders(self):
        paginas = blindaje.cargar_local(FIX / "sitio_malo")
        carpeta, _, _ = blindaje.ejecutar(paginas, "X", "https://x.test", self.tmp.name,
                                          contacto={"nombre": "Ana Ruiz", "telefono": "600 000 000", "email": ""})
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        self.assertIn("Ana Ruiz", html)
        self.assertNotIn("{nombre_contacto}", html)
        self.assertIn("{email_contacto}", html)

    def test_resumen_tres_lineas(self):
        r = informe.resumen_titular("X", "https://x.test", "28/09/2026", 1, 100, "A", [])
        self.assertEqual(len(r), 3)
        self.assertIn("1 página pública", r[0])

    def test_cli_html_local(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            code = blindaje.main(["--html-local", str(FIX / "sitio_malo"), "--nombre", "Clínica X",
                                  "--salida", self.tmp.name])
        self.assertEqual(code, 0)
        html = (Path(self.tmp.name) / "clinica-x" / "informe.html").read_text(encoding="utf-8")
        self.assertIn("copias guardadas", html)
        self.assertNotIn("robots.txt", html)
        self.assertIn("Nota E", salida.getvalue())


class SitioFalso:
    """Simula un servidor web: dict url -> (estado, content_type, cuerpo)."""

    def __init__(self, paginas, redirecciones=None):
        self.paginas = paginas
        self.redirecciones = redirecciones or {}

    def __call__(self, url):
        final = self.redirecciones.get(url, url)
        estado, ctype, cuerpo = self.paginas.get(final, (404, "text/html", ""))
        return estado, final, ctype, cuerpo.encode("utf-8")


def _html(*enlaces, texto=""):
    return "<html><body>" + texto + "".join(f'<a href="{e}">l</a>' for e in enlaces) + "</body></html>"


class TestRastreador(unittest.TestCase):
    def _rastreador(self, sitio, **kw):
        t = [0.0]
        esperas = []

        def dormir(s):
            esperas.append(s)
            t[0] += s

        r = blindaje.Rastreador("https://www.clinica.test", obtener=sitio, dormir=dormir,
                                reloj=lambda: t[0], log=lambda *a: None, **kw)
        return r, esperas

    def test_respeta_robots_dominio_y_ritmo(self):
        B = "https://www.clinica.test"
        sitio = SitioFalso({
            B + "/robots.txt": (200, "text/plain", "User-agent: *\nDisallow: /privado/\n"),
            B + "/": (200, "text/html; charset=utf-8",
                      _html("/tratamientos", "/privado/x", "https://otra.test/", "/foto.jpg",
                            "mailto:a@b.c", "https://clinica.test/aviso-legal", "/wp-admin/")),
            B + "/tratamientos": (200, "text/html", _html("/")),
            "https://clinica.test/aviso-legal": (200, "text/html", _html()),
        })
        r, esperas = self._rastreador(sitio)
        paginas = r.rastrear()
        urls = [u for u, _ in paginas]
        self.assertEqual(set(urls), {B + "/", B + "/tratamientos", "https://clinica.test/aviso-legal"})
        self.assertNotIn(B + "/privado/x", r.peticiones)
        self.assertFalse(any("otra.test" in u or u.endswith(".jpg") or "wp-admin" in u for u in r.peticiones))
        # 1 petición por segundo como mínimo entre peticiones (robots incluido)
        self.assertEqual(len(esperas), len(r.peticiones) - 1)
        self.assertTrue(all(e >= 1.0 - 1e-9 for e in esperas))

    def test_crawl_delay_y_maximo_de_paginas(self):
        B = "https://www.clinica.test"
        paginas = {B + "/robots.txt": (200, "text/plain", "User-agent: *\nCrawl-delay: 3\n")}
        paginas[B + "/"] = (200, "text/html", _html(*[f"/p{i}" for i in range(10)]))
        for i in range(10):
            paginas[f"{B}/p{i}"] = (200, "text/html", _html())
        r, esperas = self._rastreador(SitioFalso(paginas), max_paginas=4)
        self.assertEqual(len(r.rastrear()), 4)
        self.assertTrue(all(e >= 3.0 - 1e-9 for e in esperas))

    def test_robots_prohibido(self):
        B = "https://www.clinica.test"
        sitio = SitioFalso({B + "/robots.txt": (200, "text/plain", "User-agent: *\nDisallow: /\n"),
                            B + "/": (200, "text/html", _html())})
        r, _ = self._rastreador(sitio)
        self.assertEqual(r.rastrear(), [])
        self.assertEqual(r.peticiones, [B + "/robots.txt"])

    def test_robots_403_no_descarga(self):
        B = "https://www.clinica.test"
        r, _ = self._rastreador(SitioFalso({B + "/robots.txt": (403, "text/html", "")}))
        self.assertEqual(r.rastrear(), [])
        self.assertTrue(any("403" in a for a in r.avisos))

    def test_sin_robots_se_permite_y_omite_no_html(self):
        B = "https://www.clinica.test"
        sitio = SitioFalso({B + "/": (200, "text/html", _html("/datos")),
                            B + "/datos": (200, "application/pdf", "%PDF")})
        r, _ = self._rastreador(sitio)
        self.assertEqual([u for u, _ in r.rastrear()], [B + "/"])

    def test_user_agent_identificable(self):
        self.assertIn(blindaje.AGENTE, blindaje.USER_AGENT)
        self.assertIn("revision pasiva", blindaje.USER_AGENT)


if __name__ == "__main__":
    unittest.main()
