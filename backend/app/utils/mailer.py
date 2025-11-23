from __future__ import annotations
import os, smtplib, socket
from email.message import EmailMessage
from fastapi import HTTPException, status


def _smtp_config():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    use_starttls = os.getenv("SMTP_STARTTLS", "true").lower() != "false"
    use_ssl = os.getenv("SMTP_SSL", "false").lower() == "true"
    sender = os.getenv("EMAIL_FROM", user or "no-reply@plango.local")
    timeout = float(os.getenv("SMTP_TIMEOUT", "10"))
    if not host or not user or not password:
        raise RuntimeError("SMTP no configurado: faltan SMTP_HOST/SMTP_USER/SMTP_PASS")
    return host, port, user, password, use_starttls, use_ssl, sender, timeout


def send_email_html(
    to_email: str, subject: str, html_body: str, text_fallback: str | None = None
):
    host, port, user, password, use_starttls, use_ssl, sender, timeout = _smtp_config()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(text_fallback or "Tu cliente de correo no soporta HTML.")
    msg.add_alternative(html_body, subtype="html")

    print(
        f"[MAIL] Conectando a {host}:{port} (ssl={use_ssl}, starttls={use_starttls}, timeout={timeout}s) ..."
    )

    try:
        server = (
            smtplib.SMTP_SSL(host, port, timeout=timeout)
            if use_ssl
            else smtplib.SMTP(host, port, timeout=timeout)
        )
        with server:
            server.ehlo()
            if (not use_ssl) and use_starttls:
                server.starttls()
                server.ehlo()
            server.login(user, password)
            server.send_message(msg)
    except (socket.timeout, TimeoutError) as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout conectando a SMTP ({host}:{port}). Verificá firewall/red: {e}",
        )
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo autenticar contra el servidor SMTP (ver credenciales).",
        )
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error SMTP: {e}"
        )
