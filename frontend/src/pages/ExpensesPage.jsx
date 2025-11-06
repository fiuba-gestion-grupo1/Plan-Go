import React, { useEffect, useState } from "react";
import { request } from "../utils/api";

export default function ExpensesPage({ token }) {
  const [expenses, setExpenses] = useState([]);
  const [tripName, setTripName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function fetchExpenses() {
    setLoading(true);
    setError("");
    try {
      const data = await request("/api/expenses", { token });
      setExpenses(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddExpense() {
    if (!tripName.trim()) return;
    setLoading(true);
    try {
      await request("/api/expenses", {
        method: "POST",
        token,
        body: {
          trip_name: tripName,
          name: "Nuevo gasto",
          category: "general",
          amount: 0,
          date: new Date().toISOString().split("T")[0],
        },
      });
      setTripName("");
      fetchExpenses();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchExpenses();
  }, []);

  return (
    <div className="container mt-4">
      <h3 className="mb-4">💰 Mis Gastos</h3>

      <div className="input-group mb-4">
        <input
          type="text"
          className="form-control"
          placeholder="Nombre del viaje..."
          value={tripName}
          onChange={(e) => setTripName(e.target.value)}
        />
        <button className="btn btn-primary" onClick={handleAddExpense}>
          Crear viaje
        </button>
      </div>

      {loading && <div className="alert alert-info">Cargando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {!loading && expenses.length === 0 && (
        <div className="alert alert-secondary">Aún no registraste ningún gasto.</div>
      )}

      <div className="list-group">
        {expenses.map((e) => (
          <div key={e.id} className="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <strong>{e.trip_name}</strong> — {e.category}
              <div className="small text-muted">{e.date}</div>
            </div>
            <span className="badge bg-success">${e.amount}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
