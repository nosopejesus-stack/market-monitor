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
        for h in hs:
            esperada = reglas.MEDIA if ("«sin dolor»" in h.titulo or "«milagro»" in h.titulo) else reglas.ALTA
            self.assertEqual(h.gravedad, esperada, h.titulo)
            self.assertIn("SIN VERIFICAR", h.sin_verificar)

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


def _pag(texto, url="https://c.test/x"):
    return reglas.extraer(url, f"<p>{texto}</p>")


class TestTextosCorregidosCondicionados(unittest.TestCase):
    """Revisor 1: los textos corregidos no afirman hechos del cliente."""

    def test_registro_condicionado_y_sin_verificar(self):
        hs = reglas.regla_registro([pagina("falsos_positivos.html")])
        self.assertIn("Solo si el centro está inscrito en el Registro de centros sanitarios de la Comunidad de "
                      "Madrid — comprobar antes de publicar", hs[0].texto_corregido)
        self.assertIn("SIN VERIFICAR", hs[0].sin_verificar)

    def test_colegio_como_marcador(self):
        h = reglas.regla_medico([pagina("promesas.html")])[0]
        self.assertIn("{colegio}", h.texto_corregido)
        self.assertNotIn("Colegio Oficial de Médicos de Madrid", h.texto_corregido)
        aviso = next(x for x in reglas.reglas_legales([pagina("promesas.html")]) if x.regla == "aviso_legal")
        self.assertIn("{colegio}", aviso.texto_corregido)
        self.assertIn("Solo si el centro está inscrito", aviso.texto_corregido)

    def test_antes_despues_solo_si_es_cierto(self):
        h = reglas.regla_antes_despues(pagina("antes_despues.html"))[0]
        self.assertTrue(h.texto_corregido.startswith("[Solo si es cierto]"))

    def test_promesas_sin_verificar(self):
        self.assertIn("SIN VERIFICAR", reglas.PROMESA_BASE["sin_verificar"])
        self.assertIn("SIN VERIFICAR", reglas.REGISTRO_BASE["sin_verificar"])


class TestNegacionYContexto(unittest.TestCase):
    """Revisor 2: negaciones, nombre propio y menciones explicativas."""

    def test_negaciones_no_son_promesa(self):
        for t in ("No garantizamos resultados en su piel.",
                  "Ningún médico serio le ofrecerá resultados garantizados.",
                  "La medicina estética no hace milagros.",
                  "No existe un tratamiento sin riesgo.",
                  "El láser no es indoloro.",
                  "Le atiende la DRA. MILAGROS PÉREZ.",
                  "DRA. MILAGROS PÉREZ"):
            self.assertEqual(reglas.regla_promesas(_pag(t)), [], t)

    def test_no_invasivo_no_niega_la_promesa(self):
        hs = reglas.regla_promesas(_pag("Técnica no invasiva y sin dolor."))
        self.assertEqual(len(hs), 1)

    def test_milagro_en_mayusculas_sigue_contando(self):
        hs = reglas.regla_promesas(_pag("¡RESULTADOS MILAGROSOS en su piel!"))
        self.assertEqual([h.gravedad for h in hs], [reglas.MEDIA])

    def test_toxina_explicativa_no_es_alta(self):
        p = _pag("¿Por qué no anunciamos la toxina botulínica? La ley prohíbe la publicidad de medicamentos "
                 "con receta.")
        hs = reglas.regla_toxina(p)
        self.assertEqual([(h.regla, h.gravedad) for h in hs], [("toxina_revisar", reglas.BAJA)])

    def test_toxina_negada_no_es_alta(self):
        hs = reglas.regla_toxina(_pag("En nuestra clínica no usamos bótox."))
        self.assertTrue(all(h.gravedad == reglas.BAJA for h in hs))

    def test_botox_capilar_y_efecto_botox(self):
        for t in ("Botox capilar para un pelo brillante.", "Crema con efecto botox.",
                  "Tratamiento de botox capilar"):
            self.assertEqual(reglas.regla_toxina(_pag(t, "https://c.test/peluqueria")), [], t)

    def test_toxina_real_sigue_siendo_alta(self):
        hs = reglas.regla_toxina(_pag("Tratamiento con bótox en Madrid."))
        self.assertEqual([h.gravedad for h in hs], [reglas.ALTA])


class TestGravedadDolorYMilagro(unittest.TestCase):
    """Revisor 5: "sin dolor"/"indoloro" y "milagro" son MEDIA; cookies -> AEPD."""

    def test_sin_dolor_media(self):
        for t in ("Depilación sin dolor.", "Láser indoloro para su piel."):
            h = reglas.regla_promesas(_pag(t))[0]
            self.assertEqual(h.gravedad, reglas.MEDIA)
            self.assertIn("Afirmación absoluta sobre dolor o riesgo", h.titulo)
            self.assertIn("Puede considerarse", h.base_normativa)

    def test_milagro_media(self):
        h = reglas.regla_promesas(_pag("¡El efecto milagro que tu piel necesita!"))[0]
        self.assertEqual(h.gravedad, reglas.MEDIA)
        self.assertIn("Posible promesa de resultado", h.titulo)

    def test_frase_mixta_manda_la_alta(self):
        h = reglas.regla_promesas(_pag("Relleno de labios sin dolor y resultados garantizados."))[0]
        self.assertEqual(h.gravedad, reglas.ALTA)

    def test_cookies_aepd(self):
        h = next(x for x in reglas.reglas_legales([pagina("promesas.html")]) if x.regla == "cookies")
        self.assertIn("AEPD", h.base_normativa)
        self.assertIn("no la Consejería", h.base_normativa)


class TestPlantillasLegales(unittest.TestCase):
    """Revisor 9."""

    def test_borrador_y_campos(self):
        hs = {h.regla: h for h in reglas.reglas_legales([pagina("promesas.html")])}
        for rid in ("privacidad", "cookies"):
            self.assertIn("Borrador mínimo: completar y validar con su asesor", hs[rid].texto_corregido)
        self.assertIn("{plazos_conservacion}", hs["privacidad"].texto_corregido)
        self.assertIn("{destinatarios}", hs["privacidad"].texto_corregido)
        self.assertNotIn("solo si usted lo acepta", hs["cookies"].texto_corregido.lower())


class TestFalsosPositivosRevisor(unittest.TestCase):
    """Revisor 10."""

    def test_oferta_de_tratamientos(self):
        self.assertEqual(reglas.regla_promociones(_pag("Conozca nuestra oferta de tratamientos faciales.")), [])
        self.assertEqual(reglas.regla_promociones(_pag("Amplia oferta de servicios de medicina estética.")), [])
        self.assertTrue(reglas.regla_promociones(_pag("Oferta: 20 % en relleno de labios.")))

    def test_cuidados_antes_y_despues(self):
        for t in ("Cuidados antes y después del tratamiento: evite el sol.",
                  "Instrucciones antes y después de la sesión de láser para pacientes."):
            self.assertEqual(reglas.regla_antes_despues(_pag(t + " Texto largo para que no sea un titular.")), [], t)

    def test_pacientes_ya_no_es_contexto_de_foto(self):
        t = "Recomendamos a los pacientes hidratarse antes y después, durante toda la semana del tratamiento."
        self.assertEqual(reglas.regla_antes_despues(_pag(t)), [])

    def test_enlace_exige_galeria(self):
        p = reglas.extraer("https://c.test/", '<p>Hola, bienvenida a la clínica de medicina estética.</p>'
                                               '<a href="/consejos-antes-y-despues">Leer consejos</a>')
        self.assertEqual(reglas.regla_antes_despues(p), [])
        p2 = reglas.extraer("https://c.test/", '<p>Hola, bienvenida a la clínica de medicina estética.</p>'
                                                '<a href="/casos-antes-y-despues">Ver</a>')
        self.assertEqual(len(reglas.regla_antes_despues(p2)), 1)

    def test_testimonios_explicados_no_cuentan(self):
        t = "La normativa prohíbe publicar testimonios de pacientes, por eso no los mostramos."
        self.assertEqual(reglas.regla_testimonios(_pag(t)), [])


class TestRegistroPegado(unittest.TestCase):
    """Revisor 11."""

    def _estado(self, t):
        return reglas.estado_registro([_pag(t)])[0]

    def test_no_cuentan_telefono_calle_ni_cp(self):
        for t in ("Registro sanitario. Tel. 912 345 678", "Registro sanitario: c/ Alcalá 123",
                  "Centro con registro sanitario, 28001 Madrid",
                  "Centro con registro sanitario en la Comunidad de Madrid desde hace muchos años 2015"):
            self.assertEqual(self._estado(t), "sin_numero", t)

    def test_cuentan_numeros_pegados(self):
        for t in ("Inscripción en el Registro: 10953", "Nº de registro sanitario 1234/2020",
                  "Nº registro sanitario: CS9876"):
            self.assertEqual(self._estado(t), "con_numero", t)


class TestLecturaNoFiable(unittest.TestCase):
    """Revisor 3: web que no se puede leer (SPA con JavaScript)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_spa_no_emite_ausencias(self):
        spa = ('<!DOCTYPE html><html><head><title>Clínica</title></head><body><div id="root"></div>'
               '<script src="/static/js/main.js"></script></body></html>')
        paginas = [("https://spa.test/", spa), ("https://spa.test/tratamientos", spa)]
        carpeta, datos, hs = blindaje.ejecutar(paginas, "SPA", "https://spa.test", self.tmp.name)
        self.assertFalse(datos["lectura_fiable"])
        self.assertEqual(hs, [])
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        self.assertIn("No se ha podido leer el contenido (probablemente se carga con JavaScript); revisión no "
                      "fiable", html)
        self.assertIn("--html-local", html)
        self.assertIn('class="alerta"', html)

    def test_una_pagina_no_emite_ausencias_pero_si_promesas(self):
        texto = "<p>" + "Resultados garantizados en su piel. " * 20 + "</p>"
        _, datos, hs = blindaje.ejecutar([("index.html", texto)], "X", "https://x.test", self.tmp.name)
        self.assertFalse(datos["lectura_fiable"])
        reglas_vistas = {h.regla for h in hs}
        self.assertIn("promesas", reglas_vistas)
        self.assertFalse(reglas_vistas & {"registro", "aviso_legal", "privacidad", "cookies", "medico"})

    def test_sitio_legible(self):
        _, datos, _ = blindaje.ejecutar(blindaje.cargar_local(FIX / "sitio_malo"), "X", "https://x.test",
                                        self.tmp.name)
        self.assertTrue(datos["lectura_fiable"])


class TestPuntosNormaYPrevio(unittest.TestCase):
    """Revisor 4, 8, 15, 19, 21."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _h(self, regla, grav, ev, sv=""):
        return reglas.Hallazgo(regla, grav, "t", "u", "x", ev, 0, 0, "a", "c", "b", sin_verificar=sv)

    def test_n_puntos_norma_deduplica(self):
        hs = [self._h("toxina", "ALTA", "Bótox en Madrid."),
              self._h("toxina", "ALTA", "Bótox en Madrid"),           # misma frase (texto y meta)
              self._h("promociones", "MEDIA", "Bótox en Madrid."),    # otra norma: cuenta
              self._h("promesas", "ALTA", "Sin riesgos.", sv="SIN VERIFICAR"),
              self._h("cookies", "BAJA", "No hay cookies.")]
        self.assertEqual(reglas.n_puntos_norma(hs), 2)

    def test_json_expone_n_puntos_norma_y_anonimiza(self):
        carpeta, datos, hs = blindaje.ejecutar(blindaje.cargar_local(FIX / "sitio_malo"), "X", "https://x.test",
                                               self.tmp.name)
        js = json.loads((carpeta / "informe.json").read_text(encoding="utf-8"))
        self.assertEqual(js["n_puntos_norma"], reglas.n_puntos_norma(hs))
        self.assertGreaterEqual(js["n_puntos_norma"], 2)   # toxina y promoción
        texto_json = json.dumps(js, ensure_ascii=False)
        self.assertNotIn("- Ana", texto_json)
        self.assertIn("- [nombre]", texto_json)
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        self.assertIn(f"{js['n_puntos_norma']} puntos con norma concreta", html)
        for h in js["hallazgos"]:
            self.assertEqual(h["evidencia"][h["marca_inicio"]:h["marca_fin"]].strip() != "", h["marca_fin"] > 0)

    def test_anonimizar(self):
        self.assertEqual(informe.anonimizar('"Me encantó" - Laura, 45 años'), '"Me encantó" - [nombre], 45 años')
        self.assertEqual(informe.anonimizar('«Genial» — Ana M.'), '«Genial» — [nombre]')

    def test_previo_sin_textos_corregidos(self):
        paginas = blindaje.cargar_local(FIX / "sitio_malo")
        carpeta, datos, hs = blindaje.ejecutar(paginas, "X", "https://x.test", self.tmp.name, previo=True)
        self.assertFalse((carpeta / "informe.html").exists())
        html = (carpeta / "informe_previo.html").read_text(encoding="utf-8")
        self.assertIn("Informe previo", html)
        self.assertNotIn("Texto corregido", html)
        self.assertNotIn("incluye los textos corregidos", html)
        for h in hs:
            self.assertNotIn(escape_html(h.texto_corregido), html)
        self.assertIn("puntos con norma concreta", html)
        self.assertIn("RD 1416/1994", html)          # norma de cada punto
        self.assertIn("390 €", html)
        self.assertNotRegex(html, r"\bIA\b")

    def test_completo_si_incluye_textos(self):
        carpeta, _, _ = blindaje.ejecutar(blindaje.cargar_local(FIX / "sitio_malo"), "X", "https://x.test",
                                          self.tmp.name)
        html = (carpeta / "informe.html").read_text(encoding="utf-8")
        self.assertIn("este informe incluye los textos corregidos", html)

    def test_proximos_pasos_condiciones(self):
        carpeta, _, _ = blindaje.ejecutar(blindaje.cargar_local(FIX / "sitio_malo"), "X", "https://x.test",
                                          self.tmp.name, previo=True)
        html = (carpeta / "informe_previo.html").read_text(encoding="utf-8")
        for txt in ("5 días hábiles desde el cobro", "últimos 12 meses", "no en tiempo real",
                    "15 días de preaviso", "sin IVA"):
            self.assertIn(txt, html)

    def test_modo_local_sin_url(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            code = blindaje.main(["--html-local", str(FIX / "sitio_malo"), "--nombre", "Clínica X",
                                  "--salida", self.tmp.name, "--previo"])
        self.assertEqual(code, 0)
        js = json.loads((Path(self.tmp.name) / "clinica-x" / "informe.json").read_text(encoding="utf-8"))
        self.assertTrue(js["resumen"][0].startswith("Hemos revisado 3 páginas guardadas de la web de Clínica X"))
        self.assertIn("informe_previo.html", salida.getvalue())


def escape_html(t):
    from html import escape
    return escape(t)


class TestDescargaRevisor(unittest.TestCase):
    """Revisor 6, 7, 17, 18, 20."""

    def test_enlaces_mal_formados_no_rompen(self):
        self.assertIsNone(blindaje.normalizar_url("http://c.test:abc/x"))
        self.assertIsNone(blindaje.normalizar_url("http://[::1/x"))
        B = "https://www.clinica.test"
        sitio = SitioFalso({B + "/": (200, "text/html", _html("http://www.clinica.test:abc/x", "http://[::1/x",
                                                               "/ok"))})
        r = blindaje.Rastreador(B, obtener=sitio, dormir=lambda s: None, log=lambda *a: None)
        self.assertEqual([u for u, _ in r.rastrear()], [B + "/"])

    def test_quita_parametros_de_seguimiento(self):
        self.assertEqual(blindaje.normalizar_url("https://c.test/a?utm_source=x&id=3&fbclid=9&gclid=1#f"),
                         "https://c.test/a?id=3")

    def test_deduplica_por_url_final(self):
        B = "https://www.clinica.test"
        sitio = SitioFalso({B + "/": (200, "text/html", _html("/botox", "/botox/", "/botox?utm_campaign=z")),
                            B + "/botox/": (200, "text/html", _html())},
                           redirecciones={B + "/botox": B + "/botox/"})
        r = blindaje.Rastreador(B, obtener=sitio, dormir=lambda s: None, log=lambda *a: None)
        urls = [u for u, _ in r.rastrear()]
        self.assertEqual(urls.count(B + "/botox/"), 1)
        self.assertEqual(len(urls), 2)

    def test_error_ssl_sugiere_html_local(self):
        import ssl
        import urllib.error

        def falla(url):
            raise urllib.error.URLError(ssl.SSLCertVerificationError("certificate verify failed"))
        r = blindaje.Rastreador("https://c.test", obtener=falla, dormir=lambda s: None, log=lambda *a: None)
        self.assertEqual(r.rastrear(), [])
        self.assertTrue(any("--html-local" in a and "SSL" in a for a in r.avisos), r.avisos)

    def test_utf8_estricto_primero(self):
        self.assertEqual(blindaje.decodificar("Bótox".encode("utf-8"), "text/html; charset=iso-8859-1"), "Bótox")
        self.assertEqual(blindaje.decodificar("Bótox".encode("cp1252"), "text/html; charset=windows-1252"), "Bótox")

    def test_user_agent_con_contacto(self):
        ua = blindaje.crear_user_agent("yo@ejemplo.es")
        self.assertIn("(+contacto: yo@ejemplo.es)", ua)
        self.assertIn(blindaje.AGENTE, ua)
        self.assertNotIn("contacto", blindaje.crear_user_agent(""))


if __name__ == "__main__":
    unittest.main()
