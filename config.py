"""
Configuración central: activos a monitorizar y parámetros del sistema.
Ajusta esta lista a los instrumentos que operas en FTMO / cuenta de fondeo.
"""

# Nombre legible -> símbolos por proveedor + divisas cuyos eventos del
# calendario económico le afectan.
#   twelvedata: símbolo en Twelve Data (fuente principal, requiere TWELVEDATA_API_KEY).
#               El plan gratuito no cubre índices ni WTI: se usan ETFs como proxy.
#   yahoo:      ticker de Yahoo Finance (respaldo si Twelve Data falla o no hay key).
ASSETS = {
    "EUR/USD": {"twelvedata": "EUR/USD", "yahoo": "EURUSD=X", "currencies": ["EUR", "USD"]},
    "GBP/USD": {"twelvedata": "GBP/USD", "yahoo": "GBPUSD=X", "currencies": ["GBP", "USD"]},
    "USD/JPY": {"twelvedata": "USD/JPY", "yahoo": "USDJPY=X", "currencies": ["USD", "JPY"]},
    "Oro (XAU/USD)": {"twelvedata": "XAU/USD", "yahoo": "GC=F", "currencies": ["USD"]},
    "S&P 500 (SPY)": {"twelvedata": "SPY", "yahoo": "SPY", "currencies": ["USD"]},
    "Nasdaq 100 (QQQ)": {"twelvedata": "QQQ", "yahoo": "QQQ", "currencies": ["USD"]},
    "Dow Jones (DIA)": {"twelvedata": "DIA", "yahoo": "DIA", "currencies": ["USD"]},
    "Petróleo WTI (USO)": {"twelvedata": "USO", "yahoo": "USO", "currencies": ["USD"]},
    "Bitcoin": {"twelvedata": "BTC/USD", "yahoo": "BTC-USD", "currencies": ["USD"]},
}

# Palabras clave para filtrar noticias relevantes por activo
NEWS_KEYWORDS = {
    "EUR/USD": ["ECB", "eurozone", "euro", "Lagarde", "EU inflation"],
    "GBP/USD": ["Bank of England", "BoE", "UK inflation", "pound"],
    "USD/JPY": ["Bank of Japan", "BoJ", "yen", "Fed", "Federal Reserve"],
    "Oro (XAU/USD)": ["gold", "safe haven", "Fed rate", "inflation"],
    "S&P 500 (SPY)": ["S&P 500", "Wall Street", "US stocks", "Fed"],
    "Nasdaq 100 (QQQ)": ["Nasdaq", "tech stocks", "AI stocks"],
    "Dow Jones (DIA)": ["Dow Jones", "US economy"],
    "Petróleo WTI (USO)": ["oil", "OPEC", "crude", "Middle East"],
    "Bitcoin": ["bitcoin", "crypto", "BTC", "SEC crypto"],
}

# Umbral de volatilidad DIARIA (%, desviación típica de los retornos diarios)
# para marcar un activo como "alta atención".
HIGH_VOL_THRESHOLD = 1.2

# Nº de simulaciones Monte Carlo
MC_SIMULATIONS = 5000
MC_HORIZON_DAYS = 1

# Nº máximo de noticias por activo en el informe
MAX_NEWS_PER_ASSET = 3

# Umbral de "evento de alto impacto" en el calendario económico (1=bajo,2=medio,3=alto)
CALENDAR_MIN_IMPACT = 3

# Ventana de eventos del calendario a incluir (horas hacia delante desde ahora)
CALENDAR_LOOKAHEAD_HOURS = 24
