"""
Envío de email vía SMTP. Recomendado: Gmail con "contraseña de aplicación"
(no tu contraseña normal) — se genera en myaccount.google.com/apppasswords.

Variables de entorno requeridas:
- EMAIL_FROM: tu cuenta de gmail
- EMAIL_APP_PASSWORD: contraseña de aplicación (16 caracteres)
- EMAIL_TO: destinatario (puede ser el mismo)
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")


def send_email_report(subject: str, html_content: str):
    if not all([EMAIL_FROM, EMAIL_APP_PASSWORD, EMAIL_TO]):
        print("[email] faltan variables de entorno, no se envía email.")
        print(html_content[:500])
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

    print(f"[email] enviado a {EMAIL_TO}: {subject}")
