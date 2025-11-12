import React, { useState } from "react";

export default function InviteFriend({ token }) {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [okMsg, setOkMsg] = useState("");
  const [errMsg, setErrMsg] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setOkMsg("");
    setErrMsg("");

    const trimmed = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setErrMsg("Ingresá un correo válido.");
      return;
    }

    try {
      setSending(true);
      const res = await fetch("/api/invitations/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ email: trimmed }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || `Error ${res.status}`);
      }

      setOkMsg("¡Invitación enviada! Tu amigo recibirá un correo de Plan&Go.");
      setEmail("");
    } catch (err) {
      setErrMsg(
        err?.message ||
          "No pudimos enviar la invitación. Intentá nuevamente en un rato."
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card shadow-sm" style={{ maxWidth: 640, margin: "0 auto" }}>
      <div className="card-body">
        <h3 className="card-title mb-2">✉️ Invitar amigos a Plan&Go</h3>
        <p className="text-muted mb-4">
          Enviá una invitación por correo para que se unan a la app y planifiquen
          itinerarios con vos.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Correo del amigo</label>
            <input
              type="email"
              className="form-control"
              placeholder="ej: amiga@mail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {errMsg && (
            <div className="alert alert-danger py-2" role="alert">
              {errMsg}
            </div>
          )}
          {okMsg && (
            <div className="alert alert-success py-2" role="alert">
              {okMsg}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={sending}>
            {sending ? "Enviando..." : "Enviar invitación"}
          </button>
        </form>
      </div>
    </div>
  );
}
