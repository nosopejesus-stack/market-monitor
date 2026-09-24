"""Genera el HTML del informe diario / alerta."""
from datetime import datetime

DIRECTION_COLOR = {"ALZA": "#16a34a", "BAJA": "#dc2626", "NEUTRAL": "#6b7280"}
DIRECTION_ICON = {"ALZA": "▲", "BAJA": "▼", "NEUTRAL": "■"}


def build_asset_block(name, mc, score, news_items, calendar_events):
    color = DIRECTION_COLOR[score["direction"]]
    icon = DIRECTION_ICON[score["direction"]]

    news_html = ""
    for n in news_items[:3]:
        news_html += f'<li><a href="{n["url"]}">{n["title"]}</a> — {n["source"]}</li>'

    cal_html = ""
    for e in calendar_events:
        cal_html += f'<li><b>{e["title"]}</b> ({e["country"]}) — impacto {e["impact"]}, previsión: {e["forecast"]}</li>'

    return f"""
    <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:16px;">
      <h3 style="margin:0 0 8px 0;">{name}
        <span style="color:{color};font-weight:bold;">{icon} {score['direction']}</span>
        <span style="color:#6b7280;font-size:14px;"> (confianza {score['confidence_pct']}%)</span>
      </h3>
      <p style="margin:4px 0;color:#374151;font-size:14px;">{score['reasoning']}</p>
      <p style="margin:4px 0;font-size:13px;color:#6b7280;">
        Precio: {mc.get('last_price', 'N/A')} | Rango esperado (90% conf.): {mc['p5']:.4f} - {mc['p95']:.4f}
      </p>
      {'<p style="margin:4px 0;font-size:13px;"><b>Eventos clave:</b></p><ul style="font-size:13px;">' + cal_html + '</ul>' if cal_html else ''}
      {'<p style="margin:4px 0;font-size:13px;"><b>Noticias:</b></p><ul style="font-size:13px;">' + news_html + '</ul>' if news_html else ''}
    </div>
    """


def build_full_report(asset_blocks: list[str], title="Informe diario de mercado"):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    body = "".join(asset_blocks)
    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
      <h2>{title}</h2>
      <p style="color:#6b7280;font-size:13px;">Generado: {now}</p>
      {body}
      <p style="color:#9ca3af;font-size:11px;margin-top:24px;">
        Generado automáticamente. No constituye asesoramiento financiero.
        Verifica siempre antes de operar en cuenta de fondeo.
      </p>
    </body>
    </html>
    """
