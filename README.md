# Market Monitor — Informe diario + alertas (100% gratis)

Sistema automatizado que corre 24/7 en GitHub Actions (sin servidor propio)
y te envía por email un informe diario + alertas cuando detecta señales
fuertes, combinando: precios (Yahoo Finance), noticias (NewsAPI), calendario
económico (ForexFactory) y simulación Monte Carlo.

⚠️ Es una herramienta de apoyo, no garantiza aciertos. Los mercados son
parcialmente impredecibles.

## Instalación (10-15 min)

### 1. Sube este proyecto a GitHub
```
git init
git add .
git commit -m "market monitor inicial"
git remote add origin https://github.com/TU_USUARIO/market-monitor.git
git push -u origin main
```

### 2. Consigue tus credenciales gratuitas

**NewsAPI** (noticias): regístrate en https://newsapi.org (gratis, 100 req/día) → copia tu API key.

**Gmail App Password** (para enviar los emails):
1. Activa verificación en 2 pasos en tu cuenta Google
2. Ve a https://myaccount.google.com/apppasswords
3. Genera una contraseña de aplicación (16 caracteres)

### 3. Configura los secretos en GitHub
En tu repo: `Settings → Secrets and variables → Actions → New repository secret`

Añade estos 4 secretos:
- `NEWSAPI_KEY` — tu API key de NewsAPI
- `EMAIL_FROM` — tu email de Gmail
- `EMAIL_APP_PASSWORD` — la contraseña de aplicación de 16 caracteres
- `EMAIL_TO` — el email donde quieres recibir los informes (puede ser el mismo)

### 4. Activa los workflows
Ve a la pestaña `Actions` de tu repo → activa los workflows si te lo pide
GitHub. Ya está: correrá automáticamente según el cron configurado.

Puedes forzar una ejecución manual en `Actions → [nombre workflow] → Run workflow`
para probar que todo funciona antes de esperar al cron.

## Personalización

- **Activos monitorizados**: edita `config.py` → diccionario `ASSETS`
- **Horario del informe diario**: edita el cron en `.github/workflows/daily-report.yml`
- **Frecuencia de alertas**: edita el cron en `.github/workflows/alert-check.yml`
- **Sensibilidad de alertas**: `ALERT_CONFIDENCE_THRESHOLD` en `main.py`
- **Pesos del modelo** (Monte Carlo vs noticias): `analysis/scoring.py`

## Límites conocidos (importante)

- Yahoo Finance puede tener pequeños retrasos/huecos de datos — no es un
  feed de nivel institucional. Para precisión de grado profesional, sustituye
  `data_sources/market.py` por la API de tu broker (MT5) o un proveedor de
  pago (Polygon, Twelve Data).
- NewsAPI gratis tiene 100 requests/día — con 9 activos configurados usarás
  ~9 por ejecución. El plan diario + varias alertas puede acercarte al límite;
  ajusta la frecuencia del cron de alertas si lo agotas.
- El calendario económico usa una fuente pública no oficial; si deja de
  responder, sustitúyela por una API de pago (TradingEconomics) para fiabilidad.
- El "score" es un modelo heurístico simple. Antes de operar con capital real
  de fondeo, valida sus señales con backtesting histórico.

## Próximos pasos sugeridos

- Backtesting del scoring contra datos históricos
- Migrar a VPS (Hetzner ~4€/mes) cuando quieras chequeos cada 1 min en vez de 30
- Integrar datos de tu broker MT5 directamente para precios exactos de FTMO
