import React from "react";
import "../styles/buttons.css";

export default function CreatePublicationForm({
  onSubmit,
  onCancel,
  loading,
  error,
  successMsg,
}) {
  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Crear publicación</h3>
        <button
          type="button"
          className="btn btn-outline-secondary"
          onClick={onCancel}
        >
          {" "}
          Volver
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      <div className="row justify-content-center">
        <div className="col-lg-10">
          <form
            onSubmit={onSubmit}
            className="border rounded-3 p-3 bg-white shadow-sm"
          >
            <div className="row g-3">
              <div className="col-md-12">
                <label className="form-label">Nombre del lugar *</label>
                <input name="place_name" className="form-control" required />
              </div>

              <div className="col-md-12">
                <label className="form-label">Descripción *</label>
                <textarea
                  name="description"
                  className="form-control"
                  rows="3"
                  required
                  placeholder="Describe brevemente el lugar, qué se puede hacer, etc."
                ></textarea>
                <small className="text-muted">
                  Esta descripción será visible en la página de detalle.
                </small>
              </div>
              <div className="col-md-6">
                <label className="form-label">País *</label>
                <input name="country" className="form-control" required />
              </div>
              <div className="col-md-6">
                <label className="form-label">Provincia/Estado *</label>
                <input name="province" className="form-control" required />
              </div>

              <div className="col-md-6">
                <label className="form-label">Ciudad *</label>
                <input name="city" className="form-control" required />
              </div>
              <div className="col-md-6">
                <label className="form-label">
                  Dirección (calle y número) *
                </label>
                <input name="address" className="form-control" required />
              </div>

              <div className="col-md-12">
                <label className="form-label">Categorías (CSV) *</label>
                <input
                  name="categories"
                  className="form-control"
                  placeholder="ej: aventura,cultura,gastronomia"
                  required
                />
                <small className="text-muted">
                  Usá slugs: aventura, cultura, gastronomia
                </small>
              </div>

              <hr className="mt-2 mb-2" />
              <div className="col-12">
                <div className="fw-semibold text-muted">
                  Información del destino
                </div>
                <small className="text-muted">
                  Estos campos ayudan a recomendar destinos según preferencias.
                </small>
              </div>

              <div className="col-md-6">
                <label className="form-label">Continente</label>
                <select
                  name="continent"
                  className="form-select"
                  defaultValue=""
                >
                  <option value="">—</option>
                  <option value="américa">América</option>
                  <option value="europa">Europa</option>
                  <option value="asia">Asia</option>
                  <option value="áfrica">África</option>
                  <option value="oceanía">Oceanía</option>
                </select>
              </div>
              <div className="col-md-6">
                <label className="form-label">Clima</label>
                <select name="climate" className="form-select" defaultValue="">
                  <option value="">—</option>
                  <option value="templado">Templado</option>
                  <option value="frio">Frío</option>
                  <option value="tropical">Tropical</option>
                  <option value="seco">Seco</option>
                </select>
              </div>

              <div className="col-md-12">
                <label className="form-label">Actividades</label>
                <input
                  name="activities"
                  className="form-control"
                  placeholder="ej: playa,gastronomía,noche"
                />
                <small className="text-muted">
                  Separá por comas. Se guardan en minúsculas.
                </small>
              </div>

              <div className="col-md-6">
                <label className="form-label">Costo por día (USD)</label>
                <input
                  name="cost_per_day"
                  type="number"
                  step="any"
                  className="form-control"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Duración (minutos)</label>
                <input
                  name="duration_min"
                  type="number"
                  className="form-control"
                />
              </div>

              <div className="col-md-12">
                <label className="form-label">
                  Fotos (hasta 4) — JPG/PNG/WebP
                </label>
                <input
                  name="photos"
                  type="file"
                  className="form-control"
                  multiple
                  accept=".jpg,.jpeg,.png,.webp"
                />
                <small className="text-muted">
                  Podés seleccionar varias a la vez. Máximo 4.
                </small>
              </div>

              <div className="col-12 d-flex justify-content-end gap-2 mt-2">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={onCancel}
                  disabled={loading}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-outline-custom"
                  disabled={loading}
                >
                  {loading ? "Enviando..." : "Enviar para aprobación"}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
