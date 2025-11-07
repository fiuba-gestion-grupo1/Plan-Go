import { useEffect, useState } from "react";
import { request } from "../utils/api";

export default function ExpensesPage({ token }) {
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [newTrip, setNewTrip] = useState("");
  const [newExpense, setNewExpense] = useState({ name: "", category: "", amount: "", date: "" });
  const [balances, setBalances] = useState([]);

  useEffect(() => {
    fetchTrips();
  }, []);

  async function fetchTrips() {
    try {
      const data = await request("/api/trips", { token });
      setTrips(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error al cargar viajes:", err);
      setTrips([]);
    }
  }

  async function createTrip() {
    if (!newTrip.trim()) return;
    await request("/api/trips", {
      method: "POST",
      token,
      body: { name: newTrip },
    });
    setNewTrip("");
    fetchTrips();
  }

  async function openTrip(tripId) {
    try {
      const data = await request(`/api/trips/${tripId}/expenses`, { token });
      setSelectedTrip(tripId);
      setExpenses(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error al cargar gastos:", err);
      alert("No se pudieron cargar los gastos del viaje.");
      setExpenses([]);
    }
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
    try {
      await request(`/api/trips/${selectedTrip}/participants`, { method: "POST", token });
      alert("Te uniste al viaje como participante premium");
    } catch (err) {
      console.error("Error al unirse al viaje:", err);
      alert("No se pudo unir al viaje.");
    }
  }

  async function calculateBalances() {
    try {
      const data = await request(`/api/trips/${selectedTrip}/balances`, { token });
      setBalances(data.balances || []);
    } catch (err) {
      console.error("Error al calcular saldos:", err);
      setBalances([]);
    }
  }

  // --- Manejo seguro para evitar errores de tipo ---
  const safeExpenses = Array.isArray(expenses) ? expenses : [];

  const totalsByCategory = safeExpenses.reduce((acc, exp) => {
    const cat = exp.category || "Sin categoría";
    acc[cat] = (acc[cat] || 0) + parseFloat(exp.amount || 0);
    return acc;
  }, {});

  // --- Vista de selección de viajes ---
  if (!selectedTrip) {
    return (
      <div className="container mt-4">
        <h3>💰 Mis viajes</h3>
        <div className="input-group mb-3">
          <input
            className="form-control"
            value={newTrip}
            onChange={(e) => setNewTrip(e.target.value)}
            placeholder="Nombre del viaje..."
          />
          <button className="btn btn-primary" onClick={createTrip}>Crear</button>
        </div>
        {trips.map((t) => (
          <div
            key={t.id}
            className="list-group-item list-group-item-action"
            onClick={() => openTrip(t.id)}
            style={{ cursor: "pointer" }}
          >
            <strong>{t.name}</strong>{" "}
            <small className="text-muted">
              {t.created_at ? new Date(t.created_at).toLocaleDateString() : ""}
            </small>
          </div>
        ))}
      </div>
    );
  }

  // --- Vista de gastos del viaje ---
  return (
    <div className="container mt-4">
      <button className="btn btn-outline-secondary mb-3" onClick={() => setSelectedTrip(null)}>
        ← Volver
      </button>

      <div className="d-flex justify-content-between align-items-center">
        <h3>Gastos del viaje</h3>
        <div className="mb-3">
          <button className="btn btn-outline-primary me-2" onClick={joinTrip}>Unirse al viaje</button>
          <button className="btn btn-outline-success" onClick={calculateBalances}>Calcular saldos</button>
        </div>
        <button className="btn btn-outline-primary" onClick={exportToPDF}>📄 Exportar PDF</button>
      </div>

      {/* Formulario para agregar gasto */}
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
            <button className="btn btn-success w-100" onClick={addExpense}>+</button>
          </div>
        </div>
      </div>

      {/* Totales por categoría */}
      {safeExpenses.length > 0 && (
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

      {/* Lista de gastos */}
      {safeExpenses.length === 0 ? (
        <div className="alert alert-secondary">Sin gastos registrados.</div>
      ) : (
        <ul className="list-group mt-3">
          {safeExpenses.map((e) => (
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

      {/* Saldos */}
      {balances.length > 0 && (
        <div className="mt-4">
          <h5>Saldos</h5>
          <ul className="list-group">
            {balances.map((b, i) => (
              <li key={i} className="list-group-item d-flex justify-content-between">
                <span>Usuario #{b.user_id}</span>
                <span>${b.debe}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
