from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
import os
from ..utils.mailer import send_email_html

router = APIRouter(prefix="/api/invitations", tags=["invitations"])

class InvitationPayload(BaseModel):
    email: EmailStr

def _build_email_html(invitee_email: str, inviter_name: str | None, app_url: str) -> str:
    inviter = inviter_name or "un amigo"
    return f"""
<!doctype html>
<html>
  <head><meta charset="utf-8" /><title>Te invitaron a Plan&Go</title></head>
  <body style="font-family: Arial, sans-serif; background:#f6fbff; padding:24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;margin:0 auto;background:#ffffff;border-radius:16px;box-shadow:0 6px 20px rgba(0,0,0,0.06);overflow:hidden;">
      <tr>
        <td style="background:linear-gradient(135deg,#0ea5e9,#22d3ee);color:#fff;padding:24px;">
          <h1 style="margin:0;font-size:22px;">✈️ ¡{inviter} te invitó a Plan&Go!</h1>
          <p style="margin:8px 0 0 0;opacity:0.95;">Descubrí lugares, armá itinerarios y compartí planes increíbles.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:24px;">
          <p>Hola <strong>{invitee_email}</strong>,</p>
          <p>Sumate a <strong>Plan&Go</strong>, la app para planificar viajes con amigos.</p>
          <p style="margin:18px 0;">
            <a href="{app_url}" style="background:#0ea5e9;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;display:inline-block;">
              Crear mi cuenta en Plan&Go
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;">
            Si el botón no funciona, copiá y pegá este enlace:<br />
            <span style="word-break:break-all;color:#0ea5e9;">{app_url}</span>
          </p>
        </td>
      </tr>
      <tr><td style="padding:16px 24px; background:#f9fafb; color:#6b7280; font-size:12px;">
        © {os.getenv("APP_BRAND_NAME", "Plan&Go")}
      </td></tr>
    </table>
  </body>
</html>
""".strip()

@router.post("/send")
def send_invitation(payload: InvitationPayload):
    app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8000")
    subject = f"Te invitaron a {os.getenv('APP_BRAND_NAME', 'Plan&Go')} ✈️"
    html = _build_email_html(payload.email, inviter_name=None, app_url=app_url)
    send_email_html(payload.email, subject, html)
    return {"ok": True, "message": "Invitación enviada"}
