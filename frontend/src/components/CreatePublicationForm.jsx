import React, { useState } from 'react';

export default function CreatePublicationForm({ onSubmit, onCancel, loading, error, successMsg }) {
  return (
    <div className="container py-4" style={{ maxWidth: 720 }}>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <h3 className="mb-0">Agregar Nueva Publicación</h3>
        <button className="btn btn-outline-secondary" onClick={onCancel}>
          Cancelar
        </button>
      </div>

      {loading && <div className="alert alert-info mb-3">Enviando publicación...</div>}
      {error && <div className="alert alert-danger mb-3">{error}</div>}
      {successMsg && <div className="alert alert-success mb-3">{successMsg}</div>}

      <form className="card shadow-sm p-4" onSubmit={onSubmit}>
        <div className="row g-3">
          <div className="col-12">
            <label className="form-label">Nombre del lugar *</label>
            <input name="place_name" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">País *</label>
            <input name="country" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Provincia/Estado *</label>
            <input name="province" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Ciudad *</label>
            <input name="city" type="text" className="form-control" required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Dirección (calle y número) *</label>
            <input name="address" type="text" className="form-control" required />
          </div>

          <div className="col-12">
            <label className="form-label">Fotos (hasta 4) — JPG/PNG/WebP</label>
            <input
              name="photos"
              type="file"
              className="form-control"
              multiple
              accept="image/jpeg,image/png,image/webp"
            />
            <div className="form-text">
              Podés seleccionar varias a la vez. Máximo 4.
            </div>
          </div>
        </div>

        <div className="d-flex justify-content-end gap-2 mt-4">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={onCancel}
          >
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Enviando...' : 'Enviar para aprobación'}
          </button>
        </div>
      </form>
    </div>
  );
}
