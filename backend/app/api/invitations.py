from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import os
import uuid
from ..utils.mailer import send_email_html
from .. import models
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/invitations", tags=["invitations"])

class InvitationPayload(BaseModel):
    email: EmailStr


def _build_email_html(invitee_email: str, inviter_name: str | None, app_url: str, invitation_code: str) -> str:
    inviter = inviter_name or "un amigo"
    register_url = f"{app_url}/register?invitation_code={invitation_code}"
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
            <a href="{register_url}" style="background:#0ea5e9;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;display:inline-block;">
              Crear mi cuenta en Plan&Go
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;">
            Si el botón no funciona, copiá y pegá este enlace:<br />
            <span style="word-break:break-all;color:#0ea5e9;">{register_url}</span>
          </p>
          <p style="color:#6b7280;font-size:11px;margin-top:20px;">
            Código de invitación: <strong>{invitation_code}</strong>
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
def send_invitation(
    payload: InvitationPayload,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 🔒 Solo premium
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403,
            detail="Función disponible solo para usuarios premium."
        )

    # Verificar si ya existe una invitación pendiente para este email
    existing_invitation = db.query(models.Invitation).filter(
        models.Invitation.invitee_email == payload.email,
        models.Invitation.used == False
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una invitación pendiente para este email."
        )
    
    # Verificar si el email ya está registrado
    existing_user = db.query(models.User).filter(
        models.User.email == payload.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Este email ya está registrado en la aplicación."
        )

    # Generar código único de invitación
    invitation_code = str(uuid.uuid4()).replace('-', '')[:12].upper()
    
    # Crear registro de invitación en la base de datos
    invitation = models.Invitation(
        inviter_id=current_user.id,
        invitee_email=payload.email,
        invitation_code=invitation_code,
        used=False
    )
    db.add(invitation)
    db.commit()

    app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:5173")
    subject = f"Te invitaron a {os.getenv('APP_BRAND_NAME', 'Plan&Go')} ✈️"
    html = _build_email_html(
        invitee_email=payload.email,
        inviter_name=current_user.username,
        app_url=app_url,
        invitation_code=invitation_code
    )
    send_email_html(payload.email, subject, html)
    return {"ok": True, "message": "Invitación enviada", "invitation_code": invitation_code}
