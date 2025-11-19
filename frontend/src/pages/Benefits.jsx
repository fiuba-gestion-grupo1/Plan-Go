import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';

export default function Benefits({ token, me }) {
  const [activeView, setActiveView] = useState('my-points'); // 'my-points' | 'movements'
  const [userPoints, setUserPoints] = useState(0);
  const [pointsMovements, setPointsMovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserPoints();
  }, []);

  async function fetchUserPoints() {
    setLoading(true);
    try {
      const data = await request('/api/users/points', { token });
      setUserPoints(data.points || 0);
    } catch (e) {
      console.error('Error al cargar puntos:', e);
      setUserPoints(0);
    } finally {
      setLoading(false);
    }
  }

  async function fetchPointsMovements() {
    if (pointsMovements.length > 0) return; // Ya cargados
    
    setLoading(true);
    try {
      const data = await request('/api/users/points/movements', { token });
      setPointsMovements(data || []);
    } catch (e) {
      console.error('Error al cargar movimientos:', e);
      setError('Error al cargar el historial de puntos');
    } finally {
      setLoading(false);
    }
  }

  function handleViewChange(view) {
    setActiveView(view);
    if (view === 'movements') {
      fetchPointsMovements();
    }
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMovementIcon = (transactionType) => {
    switch (transactionType) {
      case 'review_earned': return '⭐';
      case 'bonus': return '🎁';
      case 'redeemed': return '💸';
      default: return '💎';
    }
  };

  const getMovementDescription = (movement) => {
    switch (movement.transaction_type) {
      case 'review_earned': 
        return `Puntos ganados por reseña: "${movement.description}"`;
      case 'bonus': 
        return `Bonus especial: ${movement.description}`;
      case 'redeemed': 
        return `Puntos canjeados: ${movement.description}`;
      default: 
        return movement.description || 'Movimiento de puntos';
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex align-items-center justify-content-between mb-4">
        <h3 className="mb-0">🎁 Beneficios Premium</h3>
        <div className="badge bg-warning text-dark fs-6 px-3 py-2">
          💎 {userPoints} puntos
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Pestañas de navegación */}
      <div className="d-flex mb-4 border-bottom">
        <button
          className={`btn pb-2 ${activeView === 'my-points' ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => handleViewChange('my-points')}
        >
          💰 Mis puntos
        </button>
        <button
          className={`btn pb-2 ${activeView === 'movements' ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => handleViewChange('movements')}
        >
          📋 Ver movimientos
        </button>
      </div>

      {/* Vista: Mis puntos */}
      {activeView === 'my-points' && (
        <div className="row g-4">
          {/* Resumen de puntos */}
          <div className="col-lg-6">
            <div className="card shadow-sm border-warning">
              <div className="card-body text-center">
                <div className="display-4 text-warning mb-3">💎</div>
                <h4 className="mb-2">Tus puntos actuales</h4>
                <div className="display-5 fw-bold text-primary mb-3">{userPoints}</div>
                <p className="text-muted">
                  Ganá más puntos escribiendo reseñas detalladas
                </p>
              </div>
            </div>
          </div>

          {/* Cómo ganar puntos */}
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header bg-light">
                <h5 className="mb-0">💡 ¿Cómo ganar puntos?</h5>
              </div>
              <div className="card-body">
                <ul className="list-unstyled mb-0">
                  <li className="mb-3">
                    <div className="d-flex align-items-center">
                      <span className="me-3 fs-4">⭐</span>
                      <div>
                        <strong>Escribir reseñas</strong>
                        <br />
                        <small className="text-muted">+10 puntos por reseña detallada</small>
                      </div>
                    </div>
                  </li>
                  <li className="mb-3">
                    <div className="d-flex align-items-center">
                      <span className="me-3 fs-4">📊</span>
                      <div>
                        <strong>Invitar un amigo</strong>
                        <br />
                        <small className="text-muted">+50 puntos por calificación</small>
                      </div>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Próximamente: Canjear puntos */}
          <div className="col-12">
            <div className="card shadow-sm border-light">
              <div className="card-body text-center">
                <h5 className="text-muted">🚀 Próximamente</h5>
                <p className="text-muted mb-0">
                  Muy pronto podrás canjear tus puntos por descuentos, promociones especiales y beneficios exclusivos.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Vista: Movimientos de puntos */}
      {activeView === 'movements' && (
        <div className="card shadow-sm">
          <div className="card-header">
            <h5 className="mb-0">📋 Historial de movimientos</h5>
          </div>
          <div className="card-body">
            {loading ? (
              <div className="text-center py-4">
                <div className="spinner-border spinner-border-sm me-2" role="status"></div>
                Cargando movimientos...
              </div>
            ) : pointsMovements.length === 0 ? (
              <div className="text-center py-4 text-muted">
                <div className="mb-3">📭</div>
                <p>Aún no tenés movimientos de puntos.</p>
                <small>Comenzá a escribir reseñas para ganar tus primeros puntos.</small>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">
                  <thead className="table-light">
                    <tr>
                      <th>Fecha</th>
                      <th>Descripción</th>
                      <th className="text-end">Puntos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pointsMovements.map((movement, index) => (
                      <tr key={movement.id || index}>
                        <td className="text-muted small">
                          {formatDate(movement.created_at)}
                        </td>
                        <td>
                          <div className="d-flex align-items-center">
                            <span className="me-2">{getMovementIcon(movement.transaction_type)}</span>
                            <span>{getMovementDescription(movement)}</span>
                          </div>
                        </td>
                        <td className="text-end">
                          <span className={`fw-bold ${movement.points > 0 ? 'text-success' : 'text-danger'}`}>
                            {movement.points > 0 ? '+' : ''}{movement.points}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}