import React, { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { request } from "../utils/api";

export default function ShareItineraryPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem("token") || "";

  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setErr(""); setOk("");
    if (!email.trim()) { setErr("Ingresá un correo válido."); return; }

    setLoading(true);
    try {
      await request(`/api/itineraries/${id}/share-email`, {
        method: "POST",
        token,
        body: { to: email.trim(), note: note.trim() || undefined }
      });
      setOk("¡Itinerario enviado por email!");
      setEmail("");
      setNote("");
    } catch (e) {
      setErr(e.message || "No se pudo enviar el email.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Compartir Itinerario</h3>
        <button className="btn btn-outline-secondary" onClick={() => navigate(-1)}>
          Volver
        </button>
      </div>

      <div className="card shadow-sm">
        <div className="card-body">
          <h5 className="card-title mb-3">✉️ Enviar por correo</h5>
          <p className="text-muted" style={{marginTop: -6}}>
            Mandá este itinerario por email a quien quieras. (Similar a “Invitar amigos a Plan&Go”)
          </p>

          {err && <div className="alert alert-danger">{err}</div>}
          {ok && <div className="alert alert-success">{ok}</div>}

          <form onSubmit={onSubmit}>
            <div className="mb-3">
              <label className="form-label">Correo del destinatario</label>
              <input
                type="email"
                className="form-control"
                placeholder="ej: alguien@correo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Mensaje (opcional)</label>
              <input
                type="text"
                className="form-control"
                placeholder="Te paso el itinerario 🙂"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </div>

            <div className="d-flex gap-2">
              <button type="button" className="btn btn-outline-secondary" onClick={() => navigate(-1)}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-outline-custom" disabled={loading}>
                {loading ? "Enviando..." : "Enviar itinerario"}
              </button>
            </div>
          </form>

          <hr className="my-4" />
          <small className="text-muted">
            Consejo: si el correo no llega, revisá la carpeta de spam o consultá a soporte.
          </small>
        </div>
      </div>
    </div>
  );
}
