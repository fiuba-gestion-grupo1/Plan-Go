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
  const [view, setView] = useState('list'); // 'list' o 'report'
  const [editingExpense, setEditingExpense] = useState(null); 
  const [addError, setAddError] = useState(""); // Error para el formulario de 'Agregar'
  const [editError, setEditError] = useState(""); // Error para el 'Modal de Edición'
  const [editingTrip, setEditingTrip] = useState(null); // Para el modal de editar viaje
  const [editTripError, setEditTripError] = useState(""); // Error para ese modal

  // Estados para modales de confirmación
  const [deleteExpenseModal, setDeleteExpenseModal] = useState(false);
  const [expenseToDelete, setExpenseToDelete] = useState(null);
  const [deleteTripModal, setDeleteTripModal] = useState(false);
  const [tripToDelete, setTripToDelete] = useState(null);

  // --- NUEVO: estados para invitación ---
  const [inviteUsername, setInviteUsername] = useState("");
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [userRole, setUserRole] = useState("user");


    // --- INVITACIONES ---
  const [invitations, setInvitations] = useState([]);
  const [invitationsLoaded, setInvitationsLoaded] = useState(false);

  async function fetchInvitations() {
    try {
      const data = await request("/api/trips/invitations", { token });
      setInvitations(data);
    } catch (error) {
      console.error("Error al cargar invitaciones:", error);
    } finally {
      setInvitationsLoaded(true);
    }
  }

  async function respondInvitation(invitationId, action) {
    try {
      await request(`/api/trips/invitations/${invitationId}/respond`, {
        method: "POST",
        token,
        body: { action },
      });
      fetchInvitations(); // actualiza lista
      fetchTrips();       // refresca viajes (por si se aceptó)
    } catch (error) {
      alert(error.detail || "Error al responder invitación");
    }
  }


  // --- Cargar viajes al iniciar ---
  useEffect(() => {
    fetchTrips();
  }, []);

  useEffect(() => {
    async function fetchUser() {
      try {
        const data = await request("/api/auth/me", { token });
        console.log("👤 Usuario cargado:", data); // para verificar
        setUserRole(data.role || "user");
      } catch (error) {
        console.error("Error al obtener usuario:", error);
      }
    }
    fetchUser();
  }, [token]);

  // --- NUEVO: limpiar mensaje de invitación al cambiar de vista o viaje ---
  useEffect(() => {
    setInviteMessage(""); // 🔹 Limpia el cartel “Invitación enviada a…”
  }, [selectedTrip, view]);

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
    setInviteMessage(""); // 🔹 Limpia cartel anterior
    setBalances([]);
    setBalancesData({ total: 0, por_persona: 0, balances: [] });
    const data = await request(`/api/trips/${tripId}/expenses`, { token });
    setSelectedTrip(tripId);
    setExpenses(data);
  }


  async function addExpense() {
    const { name, category, amount, date } = newExpense;
    if (!name || !category || !amount || !date) return;
    
    try {
      await request(`/api/trips/${selectedTrip}/expenses`, {
        method: "POST",
        token,
        body: { name, category, amount: parseFloat(amount), date },
      });
      
      setNewExpense({ name: "", category: "", amount: "", date: "" });
      setAddError(""); // Limpiamos el error si tuvo éxito
      openTrip(selectedTrip);

    } catch (error) {
      console.error("Error al agregar gasto:", error);
      // Leemos 'error.message' o 'error.detail' y usamos un fallback genérico.
      const errorMessage = error.message || error.detail || "Error al agregar. Verifique los datos ingresados.";
      setAddError(errorMessage);
    }
  }

  async function handleDeleteExpense(expenseId) {
    // Mostrar modal de confirmación
    setExpenseToDelete(expenseId);
    setDeleteExpenseModal(true);
  }

  async function confirmDeleteExpense() {
    if (!expenseToDelete) return;

    try {
      await request(`/api/trips/${selectedTrip}/expenses/${expenseToDelete}`, {
        method: "DELETE",
        token,
      });
      openTrip(selectedTrip); // Refresca la lista de gastos
    } catch (error) {
      console.error("Error al eliminar gasto:", error);
      alert("Error al eliminar. Es posible que no tengas permiso para borrar este gasto.");
    } finally {
      // Cerrar modal
      setDeleteExpenseModal(false);
      setExpenseToDelete(null);
    }
  }

  async function handleUpdateExpense() {
    if (!editingExpense) return;
    
    const { id, name, category, amount, date } = editingExpense;
    
    try {
      await request(`/api/trips/${selectedTrip}/expenses/${id}`, {
        method: "PUT",
        token,
        body: { name, category, amount: parseFloat(amount), date },
      });
      setEditingExpense(null); // Cierra el modal
      setEditError(""); // Limpiamos el error
      openTrip(selectedTrip); // Refresca la lista
    } catch (error) {
      console.error("Error al actualizar gasto:", error);
      // Leemos 'error.message' o 'error.detail' y usamos un fallback genérico.
      const errorMessage = error.message || error.detail || "Error al actualizar. Verifique los datos ingresados.";
      setEditError(errorMessage);
    }
  }

  // Funciones auxiliares para abrir/cerrar el modal
  const handleOpenEditModal = (expense) => {
    const dateFormatted = expense.date ? new Date(expense.date).toISOString().split('T')[0] : "";
    setEditingExpense({...expense, date: dateFormatted});
    setEditError(""); // Limpia el error al abrir
  };

  const handleCloseEditModal = () => {
    setEditingExpense(null);
    setEditError(""); // Limpia el error al cerrar
  };

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

  async function handleDeleteTrip(tripId) {
    // Mostrar modal de confirmación
    setTripToDelete(tripId);
    setDeleteTripModal(true);
  }

  async function confirmDeleteTrip() {
    if (!tripToDelete) return;

    try {
      await request(`/api/trips/${tripToDelete}`, {
        method: "DELETE",
        token,
      });
      fetchTrips(); // Refresca la lista de viajes
      // Si eliminamos el viaje seleccionado, volver a la lista
      if (selectedTrip === tripToDelete) {
        setSelectedTrip(null);
      }
    } catch (error) {
      console.error("Error al eliminar viaje:", error);
      alert(error.detail || "Error al eliminar el viaje.");
    } finally {
      // Cerrar modal
      setDeleteTripModal(false);
      setTripToDelete(null);
    }
  }

  const handleOpenEditTripModal = (trip) => {
    // Formateamos las fechas para el input type="date"
    const format = (dateStr) => dateStr ? new Date(dateStr).toISOString().split('T')[0] : "";
    
    setEditingTrip({
      ...trip,
      start_date: format(trip.start_date),
      end_date: format(trip.end_date)
    });
    setEditTripError("");
  };

  const handleCloseEditTripModal = () => {
    setEditingTrip(null);
    setEditTripError("");
  };

  async function handleUpdateTrip() {
    if (!editingTrip) return;

    const { id, name, start_date, end_date } = editingTrip;

    try {
      await request(`/api/trips/${id}`, {
        method: "PUT",
        token,
        body: { name, start_date, end_date },
      });
      
      handleCloseEditTripModal();
      fetchTrips(); // Refresca la lista de viajes

    } catch (error) {
      console.error("Error al actualizar el viaje:", error);
      setEditTripError(error.detail || "Error al guardar los cambios.");
    }
  }

  // --- NUEVO: función para enviar invitación (usa /api/trips/{trip_id}/invite) ---
  async function sendInvitation() {
    if (userRole !== "premium") {
      setInviteError("Para invitar a otros usuarios, suscribite al plan Premium.");
      setInviteMessage("");
      return;
    }

    if (!inviteUsername.trim()) return;

    try {
      const res = await request(`/api/trips/${selectedTrip}/invite`, {
        method: "POST",
        token,
        body: { username: inviteUsername },
      });
      setInviteMessage(res.message || `Invitación enviada a ${inviteUsername}`);
      setTimeout(() => setInviteMessage(""), 3000);
      setInviteError("");
      setInviteUsername("");
    } catch (error) {
      const msg = error?.detail || error?.message || "Error al enviar invitación";
      setInviteError(msg);
      setInviteMessage("");
    }
  }


if (!selectedTrip) {
  return (
    <div className="container mt-4">

      {/* --- Pestañas --- */}
      <div className="d-flex mb-4 border-bottom">
        <button
          className={`btn me-3 pb-2 ${view === "trips" ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => { setView("trips"); fetchTrips(); }}
        >
          💼 Mis viajes
        </button>
        <button
          className={`btn pb-2 ${view === "invitations" ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => { setView("invitations"); fetchInvitations(); }}
        >
          ✉️ Mis invitaciones
        </button>
      </div>

      {/* --- Vista de Invitaciones Pendientes --- */}
      {view === "invitations" && (
        <div className="card shadow-sm mb-4">
          <div className="card-body">
            <h5 className="fw-semibold mb-3">Invitaciones recibidas</h5>

            {!invitationsLoaded ? (
              <p className="text-muted">Cargando invitaciones...</p>
            ) : invitations.length === 0 ? (
              <p className="text-muted">No tenés invitaciones pendientes.</p>
            ) : (
              <table className="table align-middle text-center">
                <thead className="table-light">
                  <tr>
                    <th>Viaje</th>
                    <th>Invitado por</th>
                    <th>Fecha</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.map((inv) => (
                    <tr key={inv.id}>
                      <td className="fw-semibold">{inv.trip_name}</td>
                      <td>{inv.invited_by}</td>
                      <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <button
                            className="btn btn-outline-success"
                            onClick={() => respondInvitation(inv.id, "accept")}
                          >
                            ✅ Aceptar
                          </button>
                          <button
                            className="btn btn-outline-danger"
                            onClick={() => respondInvitation(inv.id, "reject")}
                          >
                            ❌ Rechazar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* --- Formulario crear viaje --- */}
      {view === "trips" && (
        <>
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
                    <th className="text-center">Viaje</th>
                    <th className="text-center">Inicio</th>
                    <th className="text-center">Fin</th>
                    <th className="text-center">Integrantes</th>
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
                      <td className="text-center">
                        <div className="btn-group btn-group-sm" role="group">
                          <button 
                            className="btn btn-outline-primary" 
                            onClick={() => openTrip(t.id)}
                          >
                            Abrir
                          </button>
                          <button 
                            className="btn btn-outline-secondary" 
                            onClick={() => handleOpenEditTripModal(t)} 
                            title="Editar Viaje"
                          >
                            ✏️
                          </button>
                          <button 
                            className="btn btn-outline-danger" 
                            onClick={() => handleDeleteTrip(t.id)} 
                            title="Eliminar Viaje"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* --- NUEVO: MODAL DE EDICIÓN DE VIAJE --- */}
          {editingTrip && (
            <>
              <div className="modal-backdrop fade show"></div>
              <div className="modal fade show d-block" tabIndex="-1">
                <div className="modal-dialog modal-dialog-centered">
                  <div className="modal-content">
                    <div className="modal-header">
                      <h5 className="modal-title">Editar Viaje</h5>
                      <button type="button" className="btn-close" onClick={handleCloseEditTripModal}></button>
                    </div>
                    <div className="modal-body">
                      
                      {editTripError && (
                        <div className="alert alert-danger" role="alert">
                          {editTripError}
                        </div>
                      )}

                      <div className="mb-3">
                        <label className="form-label">Nombre del Viaje</label>
                        <input
                          type="text"
                          className="form-control"
                          value={editingTrip.name}
                          onChange={(e) => setEditingTrip({ ...editingTrip, name: e.target.value })}
                        />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Fecha de Inicio</label>
                        <input
                          type="date"
                          className="form-control"
                          value={editingTrip.start_date}
                          onChange={(e) => setEditingTrip({ ...editingTrip, start_date: e.target.value })}
                        />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Fecha de Fin</label>
                        <input
                          type="date"
                          className="form-control"
                          value={editingTrip.end_date}
                          onChange={(e) => setEditingTrip({ ...editingTrip, end_date: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="modal-footer">
                      <button type="button" className="btn btn-secondary" onClick={handleCloseEditTripModal}>Cancelar</button>
                      <button type="button" className="btn btn-primary" onClick={handleUpdateTrip}>Guardar Cambios</button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          {/* --- FIN MODAL EDICIÓN DE VIAJE --- */}

          {/* Modal de confirmación para eliminar viaje (en vista de lista) */}
          {deleteTripModal && (
            <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
              style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}>
              <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 400, width: "90%" }}>
                <div className="p-4 text-center">
                  <h5 className="mb-3">¿Seguro que querés eliminar este viaje?</h5>
                  <p className="text-muted mb-3">Se borrarán todos sus gastos.</p>
                  <div className="d-flex gap-2 justify-content-center">
                    <button
                      className="btn btn-outline-secondary"
                      onClick={() => setDeleteTripModal(false)}
                    >
                      Cancelar
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={confirmDeleteTrip}
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}


  // --- Calcular totales por categoría ---
  // (Esta lógica la dejamos como está)
  const totalsByCategory = expenses.reduce((acc, exp) => {
    const cat = exp.category || "Sin categoría";
    acc[cat] = (acc[cat] || 0) + parseFloat(exp.amount || 0);
    return acc;
  }, {});

  return (
    <div className="container mt-4">
      <button
        className="btn btn-outline-secondary mb-3"
        onClick={() => {
          setSelectedTrip(null);
          setInviteMessage(""); // 🔹 Limpia cartel
          setBalances([]);
          setBalancesData({ total: 0, por_persona: 0, balances: [] });
        }}
      >
        ← Volver
      </button>

      {/* --- Cabecera y botones de acción --- */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="mb-0">Gastos del viaje</h3>
        <div className="d-flex gap-2">
          <button className="btn btn-outline-success" onClick={calculateBalances}>
            Calcular saldos
          </button>
          <button className="btn btn-outline-primary" onClick={exportToPDF}>
            📄 Exportar PDF
          </button>
          <button 
            className="btn btn-outline-danger" 
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteTrip(selectedTrip);
            }} 
            title="Eliminar Viaje"
          >
            🗑️ Eliminar Viaje
          </button>
        </div>
      </div>

      {/* --- NUEVO: Invitar usuario premium al viaje --- */}
      <div className="card p-3 mb-4 shadow-sm">
        <h5 className="mb-3 fw-semibold">Invitar usuario premium al viaje</h5>
        <div className="row g-2 align-items-center">
          <div className="col-md-6">
            <input
              type="text"
              className="form-control"
              placeholder="Nombre de usuario"
              value={inviteUsername}
              onChange={(e) => setInviteUsername(e.target.value)}
            />
          </div>
          <div className="col-md-3 d-grid">
            <button className="btn btn-outline-primary" onClick={sendInvitation}>
              Enviar invitación
            </button>
          </div>
        </div>

        {inviteMessage && (
          <div className="alert alert-success mt-3 mb-0 py-2">
            ✅ {inviteMessage}
          </div>
        )}
        {inviteError && (
          <div className="alert alert-danger mt-3 mb-0 py-2">
            ⚠️ {inviteError}
          </div>
        )}
      </div>

      {/* --- Formulario de nuevo gasto (sin cambios) --- */}
      <div className="card p-3 mb-4 shadow-sm">
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
            <select
              className="form-select"
              value={newExpense.category}
              onChange={(e) => setNewExpense({ ...newExpense, category: e.target.value })}
            >
              <option value="">Seleccionar categoría</option>
              <option value="Comida">Comida</option>
              <option value="Transporte">Transporte</option>
              <option value="Alojamiento">Alojamiento</option>
              <option value="Entradas">Entradas</option>
              <option value="Compras">Compras</option>
              <option value="Otros">Otros</option>
            </select>
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

      {/* --- NUEVO: Mensaje de error para 'add' --- */}
      {addError && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          <strong>Error:</strong> {addError}
          <button type="button" className="btn-close" onClick={() => setAddError("")}></button>
        </div>
      )}

      {/* --- NUEVO: Botones para cambiar de vista --- */}
      <div className="mb-3">
        <button 
          className={`btn ${view === 'list' ? 'btn-light' : 'btn-outline-secondary'} me-2`}
          onClick={() => {
            setView('list');
            setInviteMessage(""); // 🔹 Limpia cartel
            setBalances([]);
            setBalancesData({ total: 0, por_persona: 0, balances: [] });
          }}

        >
          🧾 Lista de Gastos
        </button>
        <button 
          className={`btn ${view === 'report' ? 'btn-light' : 'btn-outline-secondary'}`}
          onClick={() => setView('report')}
        >
          📊 Reporte por Categoría
        </button>
      </div>

      {/* --- Vista de Lista de Gastos (Tabla) --- */}
      {view === 'list' && (
        <div className="card shadow-sm">
          <div className="card-body">
            {expenses.length === 0 ? (
              <div className="alert alert-secondary m-0">Sin gastos registrados.</div>
            ) : (
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Fecha</th>
                    <th>Concepto</th>
                    <th>Categoría</th>
                    <th className="text-end">Monto</th>
                    <th className="text-center">Acciones</th> {/* 👈 NUEVA COLUMNA */}
                  </tr>
                </thead>
                <tbody>
                  {expenses.map((e) => (
                    <tr key={e.id}>
                      <td>{e.date ? new Date(e.date).toLocaleDateString(undefined, { timeZone: 'UTC' }) : "-"}</td>
                      <td className="fw-semibold">{e.name}</td>
                      <td>
                        <span className="badge bg-secondary bg-opacity-25 text-dark-emphasis">
                          {e.category || "Sin categoría"}
                        </span>
                      </td>
                      <td className="text-end fw-bold">${parseFloat(e.amount).toFixed(2)}</td>
                      <td className="text-center">
                        <button 
                          className="btn btn-sm text-secondary py-0 px-1 me-1 border-0"
                          onClick={() => handleOpenEditModal(e)}
                          title="Editar"
                        >
                          ✏️
                        </button>
                        <button 
                          className="btn btn-sm text-danger py-0 px-1 border-0"
                          onClick={() => handleDeleteExpense(e.id)}
                          title="Eliminar"
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* --- NUEVO: Vista de Reporte por Categoría --- */}
      {view === 'report' && (
        <div className="card shadow-sm">
          <div className="card-body">
            <h5 className="fw-bold mb-3">Totales por categoría</h5>
            {expenses.length > 0 ? (
              <ul className="list-group">
                {Object.entries(totalsByCategory).map(([cat, total]) => (
                  <li key={cat} className="list-group-item d-flex justify-content-between align-items-center">
                    <span>{cat}</span>
                    <span className="fw-bold fs-5">${total.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="alert alert-secondary m-0">No hay gastos para reportar.</div>
            )}
          </div>
        </div>
      )}

      {/* --- Sección de Saldos (sin cambios) --- */}
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

      {editingExpense && (
        <>
          <div className="modal-backdrop fade show"></div>
          <div className="modal fade show d-block" tabIndex="-1">
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Editar Gasto</h5>
                  <button type="button" className="btn-close" onClick={handleCloseEditModal}></button>
                </div>
                <div className="modal-body">
                  {editError && (
                    <div className="alert alert-danger" role="alert">
                      {editError}
                    </div>
                  )}
                  <div className="mb-3">
                    <label className="form-label">Nombre</label>
                    <input
                      type="text"
                      className="form-control"
                      value={editingExpense.name}
                      onChange={(e) => setEditingExpense({ ...editingExpense, name: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Categoría</label>
                    <select
                      className="form-select"
                      value={editingExpense.category}
                      onChange={(e) => setEditingExpense({ ...editingExpense, category: e.target.value })}
                    >
                      <option value="">Seleccionar categoría</option>
                      <option value="Comida">Comida</option>
                      <option value="Transporte">Transporte</option>
                      <option value="Alojamiento">Alojamiento</option>
                      <option value="Entradas">Entradas</option>
                      <option value="Compras">Compras</option>
                      <option value="Otros">Otros</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Monto</label>
                    <input
                      type="number"
                      className="form-control"
                      value={editingExpense.amount}
                      onChange={(e) => setEditingExpense({ ...editingExpense, amount: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Fecha</label>
                    <input
                      type="date"
                      className="form-control"
                      value={editingExpense.date}
                      onChange={(e) => setEditingExpense({ ...editingExpense, date: e.target.value })}
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={handleCloseEditModal}>Cancelar</button>
                  <button type="button" className="btn btn-primary" onClick={handleUpdateExpense}>Guardar Cambios</button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Modal de confirmación para eliminar gasto */}
      {deleteExpenseModal && (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}>
          <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 400, width: "90%" }}>
            <div className="p-4 text-center">
              <h5 className="mb-3">¿Estás seguro de que querés eliminar este gasto?</h5>
              <div className="d-flex gap-2 justify-content-center">
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setDeleteExpenseModal(false)}
                >
                  Cancelar
                </button>
                <button
                  className="btn btn-danger"
                  onClick={confirmDeleteExpense}
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmación para eliminar viaje */}
      {deleteTripModal && (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: "rgba(0,0,0,.4)", zIndex: 1051 }}>
          <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 400, width: "90%" }}>
            <div className="p-4 text-center">
              <h5 className="mb-3">¿Seguro que querés eliminar este viaje?</h5>
              <p className="text-muted mb-3">Se borrarán todos sus gastos.</p>
              <div className="d-flex gap-2 justify-content-center">
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setDeleteTripModal(false)}
                >
                  Cancelar
                </button>
                <button
                  className="btn btn-danger"
                  onClick={confirmDeleteTrip}
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
