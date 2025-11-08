import { useEffect, useState } from "react";
import { request } from "../utils/api";

export default function ExpensesPage({ token }) {
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [newTrip, setNewTrip] = useState("");
  const [newExpense, setNewExpense] = useState({ name: "", category: "", amount: "", date: "" });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [balances, setBalances] = useState([]);
  const [balancesData, setBalancesData] = useState({ total: 0, por_persona: 0, balances: [] });

  useEffect(() => {
    fetchTrips();
  }, []);

  async function fetchTrips() {
    const data = await request("/api/trips", { token });
    setTrips(data);
  }

  async function createTrip() {
    if (!newTrip.trim()) return;

    const formatDate = (d) => d ? d : null;

    await request("/api/trips", {
      method: "POST",
      token,
      body: { 
        name: newTrip,
        start_date: formatDate(startDate),
        end_date: formatDate(endDate)
      },
    });

    setNewTrip("");
    setStartDate("");
    setEndDate("");
    fetchTrips();
  }

  async function openTrip(tripId) {
    const data = await request(`/api/trips/${tripId}/expenses`, { token });
    setSelectedTrip(tripId);
    setExpenses(data);
  }

  async function addExpense() {
    const { name, category, amount, date } = newExpense;
    if (!name || !category || !amount || !date) return;
    await request(`/api/trips/${selectedTrip}/expenses`, {
      method: "POST",
      token,
      body: { name, category, amount: parseFloat(amount), date },
    });
    setNewExpense({ name: "", category: "", amount: "", date: "" });
    openTrip(selectedTrip);
  }

  async function exportToPDF() {
    if (!selectedTrip) return;
    const res = await fetch(`/api/trips/${selectedTrip}/expenses/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return alert("Error al generar el PDF");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Gastos_Viaje_${selectedTrip}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  async function joinTrip() {
    await request(`/api/trips/${selectedTrip}/participants`, { method: "POST", token });
    alert("Te uniste al viaje como participante premium");
  }

  async function calculateBalances() {
    const data = await request(`/api/trips/${selectedTrip}/balances`, { token });
    setBalancesData(data);
    setBalances(data.balances || []);
  }

  if (!selectedTrip) {
    return (
      <div className="container mt-4">
        <h3 className="mb-4 fw-bold">💼 Mis viajes</h3>

        {/* --- Formulario crear viaje --- */}
        <div className="card shadow-sm mb-4">
          <div className="card-body">
            <h5 className="mb-3 fw-semibold">Crear nuevo viaje</h5>
            
            <div className="row g-3">
              <div className="col-md-4">
                <input
                  className="form-control"
                  placeholder="Nombre del viaje"
                  value={newTrip}
                  onChange={(e) => setNewTrip(e.target.value)}
                />
              </div>

              <div className="col-md-3">
                <input
                  type="date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div className="col-md-3">
                <input
                  type="date"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>

              <div className="col-md-2 d-grid">
                <button className="btn btn-primary fw-semibold" onClick={createTrip}>
                  Crear viaje
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* --- Tabla viajes --- */}
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="fw-semibold mb-3">Viajes creados</h5>

            <table className="table table-hover align-middle text-center">
              <thead className="table-light">
                <tr>
                  <th className="text-center">📍 Viaje</th>
                  <th className="text-center">📅 Inicio</th>
                  <th className="text-center">📅 Fin</th>
                  <th className="text-center">👥 Integrantes</th>
                  <th className="text-center">Acción</th>
                </tr>
              </thead>
              <tbody>
                {trips.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center text-muted py-4">
                      No tenés viajes creados aún.
                    </td>
                  </tr>
                )}

                {trips.map((t) => (
                  <tr key={t.id}>
                    <td className="fw-semibold text-center">{t.name}</td>
                    <td>{t.start_date ? new Date(t.start_date).toLocaleDateString(undefined, { timeZone: 'UTC' }) : "-"}</td>
                    <td>{t.end_date ? new Date(t.end_date).toLocaleDateString(undefined, { timeZone: 'UTC' }) : "-"}</td>
                    <td>{t.participants_count ?? 1}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => openTrip(t.id)}
                      >
                        Abrir →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // --- Calcular totales por categoría ---
  const totalsByCategory = expenses.reduce((acc, exp) => {
    const cat = exp.category || "Sin categoría";
    acc[cat] = (acc[cat] || 0) + parseFloat(exp.amount || 0);
    return acc;
  }, {});

  return (
    <div className="container mt-4">
      <button className="btn btn-outline-secondary mb-3" onClick={() => setSelectedTrip(null)}>
        ← Volver
      </button>

      <div className="d-flex justify-content-between align-items-center">
        <h3>Gastos del viaje</h3>
        <div className="mb-3">
          <button className="btn btn-outline-primary me-2" onClick={joinTrip}>
            Unirse al viaje
          </button>
          <button className="btn btn-outline-success" onClick={calculateBalances}>
            Calcular saldos
          </button>
        </div>
        <button className="btn btn-outline-primary" onClick={exportToPDF}>
          📄 Exportar PDF
        </button>
      </div>

      <div className="card p-3 mb-4">
        <div className="row g-2">
          <div className="col-md-3">
            <input
              className="form-control"
              placeholder="Nombre"
              value={newExpense.name}
              onChange={(e) => setNewExpense({ ...newExpense, name: e.target.value })}
            />
          </div>
          <div className="col-md-3">
            <input
              list="categories"
              className="form-control"
              placeholder="Categoría"
              value={newExpense.category}
              onChange={(e) => setNewExpense({ ...newExpense, category: e.target.value })}
            />
            <datalist id="categories">
              <option value="Comida" />
              <option value="Transporte" />
              <option value="Alojamiento" />
              <option value="Entradas" />
              <option value="Compras" />
              <option value="Otros" />
            </datalist>
          </div>
          <div className="col-md-2">
            <input
              type="number"
              className="form-control"
              placeholder="Monto"
              value={newExpense.amount}
              onChange={(e) => setNewExpense({ ...newExpense, amount: e.target.value })}
            />
          </div>
          <div className="col-md-3">
            <input
              type="date"
              className="form-control"
              value={newExpense.date}
              onChange={(e) => setNewExpense({ ...newExpense, date: e.target.value })}
            />
          </div>
          <div className="col-md-1">
            <button className="btn btn-success w-100" onClick={addExpense}>
              +
            </button>
          </div>
        </div>
      </div>

      {expenses.length > 0 && (
        <div className="card p-3 mt-4">
          <h5 className="fw-bold mb-3">Totales por categoría</h5>
          <ul className="list-group">
            {Object.entries(totalsByCategory).map(([cat, total]) => (
              <li key={cat} className="list-group-item d-flex justify-content-between">
                <span>{cat}</span>
                <span className="fw-bold">${total.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {expenses.length === 0 ? (
        <div className="alert alert-secondary">Sin gastos registrados.</div>
      ) : (
        <ul className="list-group">
          {expenses.map((e) => (
            <li key={e.id} className="list-group-item d-flex justify-content-between">
              <div>
                <strong>{e.name}</strong> — {e.category}
                <div className="text-muted small">{e.date}</div>
              </div>
              <span className="badge bg-success">${e.amount}</span>
            </li>
          ))}
        </ul>
      )}

      {balances.length > 0 && (
        <div className="mt-4">
          <h5>💸 Saldos del viaje</h5>
          <div className="alert alert-info">
            Total del viaje: <strong>${balancesData?.total?.toFixed(2) ?? 0}</strong> —{" "}
            Por persona: <strong>${balancesData?.por_persona?.toFixed(2) ?? 0}</strong>
          </div>

          <ul className="list-group">
            {balances.map((b, i) => (
              <li key={i} className="list-group-item d-flex justify-content-between align-items-center">
                <span>👤 {b.username}</span>
                {b.debe_o_recibe > 0 ? (
                  <span className="text-success fw-bold">Recibe ${b.debe_o_recibe}</span>
                ) : b.debe_o_recibe < 0 ? (
                  <span className="text-danger fw-bold">Debe ${Math.abs(b.debe_o_recibe)}</span>
                ) : (
                  <span className="text-muted">Está equilibrado</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
