from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import os
import smtplib
from email.message import EmailMessage

router = APIRouter(prefix="/api/invitations", tags=["invitations"])

class InvitationPayload(BaseModel):
    email: EmailStr

def _build_email_html(invitee_email: str, inviter_name: str | None, app_url: str) -> str:
    inviter = inviter_name or "un amigo"
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Te invitaron a Plan&Go</title>
  </head>
  <body style="font-family: Arial, sans-serif; background:#f6fbff; padding:24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;margin:0 auto;background:#ffffff;border-radius:16px;box-shadow:0 6px 20px rgba(0,0,0,0.06);overflow:hidden;">
      <tr>
        <td style="background:linear-gradient(135deg,#0ea5e9,#22d3ee);color:#fff;padding:24px 24px;">
          <h1 style="margin:0;font-size:22px;">✈️ ¡{inviter} te invitó a Plan&Go!</h1>
          <p style="margin:8px 0 0 0;opacity:0.95;">Descubrí lugares, armá itinerarios y compartí planes increíbles.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:24px;">
          <p>Hola <strong>{invitee_email}</strong>,</p>
          <p>
            Te llegó una invitación para unirte a <strong>Plan&Go</strong>, la app para planificar viajes con amigos.
          </p>
          <p style="margin:18px 0;">
            <a href="{app_url}" style="background:#0ea5e9;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;display:inline-block;">
              Crear mi cuenta en Plan&Go
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;">
            Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br />
            <span style="word-break:break-all;color:#0ea5e9;">{app_url}</span>
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 24px; background:#f9fafb; color:#6b7280; font-size:12px;">
          © {os.getenv("APP_BRAND_NAME", "Plan&Go")} — Viajá mejor, con amigos.
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()

def _send_email_smtp(to_email: str, subject: str, html_body: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    starttls = os.getenv("SMTP_STARTTLS", "true").lower() != "false"
    sender = os.getenv("EMAIL_FROM", user or "no-reply@plango.local")

    if not host or not user or not password:
        raise RuntimeError("SMTP no configurado: faltan SMTP_HOST/SMTP_USER/SMTP_PASS")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content("Tu cliente de correo no soporta HTML.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(host, port) as server:
        if starttls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)

@router.post("/send")
def send_invitation(payload: InvitationPayload):
    """
    Envía una invitación por correo a un amigo para que se una a Plan&Go.
    No requiere autenticación. Usa SMTP_* del entorno.
    """
    app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8000")
    inviter_name = None  # si luego queremos, podemos obtenerlo del JWT

    html = _build_email_html(payload.email, inviter_name, app_url)
    subject = f"Te invitaron a {os.getenv('APP_BRAND_NAME', 'Plan&Go')} ✈️"

    try:
        _send_email_smtp(payload.email, subject, html)
    except RuntimeError as cfg_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(cfg_err),
        )
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo autenticar contra el servidor SMTP (ver credenciales).",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo enviar el correo: {e}",
        )

    return {"ok": True, "message": "Invitación enviada"}
