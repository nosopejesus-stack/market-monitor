"""
Configuración central: activos a monitorizar y parámetros del sistema.
Ajusta esta lista a los instrumentos que operas en FTMO / cuenta de fondeo.
"""

# Ticker de Yahoo Finance -> nombre legible
ASSETS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "XAUUSD=X": "Oro (XAU/USD)",
    "^GSPC": "S&P 500",
    "^NDX": "Nasdaq 100",
    "^DJI": "Dow Jones",
    "CL=F": "Petróleo WTI",
    "BTC-USD": "Bitcoin",
}

# Palabras clave para filtrar noticias relevantes por activo
NEWS_KEYWORDS = {
    "EUR/USD": ["ECB", "eurozone", "euro", "Lagarde", "EU inflation"],
    "GBP/USD": ["Bank of England", "BoE", "UK inflation", "pound"],
    "USD/JPY": ["Bank of Japan", "BoJ", "yen", "Fed", "Federal Reserve"],
    "Oro (XAU/USD)": ["gold", "safe haven", "Fed rate", "inflation"],
    "S&P 500": ["S&P 500", "Wall Street", "US stocks", "Fed"],
    "Nasdaq 100": ["Nasdaq", "tech stocks", "AI stocks"],
    "Dow Jones": ["Dow Jones", "US economy"],
    "Petróleo WTI": ["oil", "OPEC", "crude", "Middle East"],
    "Bitcoin": ["bitcoin", "crypto", "BTC", "SEC crypto"],
}

# Umbral de volatilidad diaria (%) para marcar un activo como "alta atención"
HIGH_VOL_THRESHOLD = 1.2

# Nº de simulaciones Monte Carlo
MC_SIMULATIONS = 5000
MC_HORIZON_DAYS = 1

# Nº máximo de noticias por activo en el informe
MAX_NEWS_PER_ASSET = 3

# Umbral de "evento de alto impacto" en el calendario económico (1=bajo,2=medio,3=alto)
CALENDAR_MIN_IMPACT = 3
