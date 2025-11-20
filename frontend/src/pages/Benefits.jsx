import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';
import PublicationDetailModal from "../components/PublicationDetailModal";

export default function Benefits({ token, me }) {
  const [activeView, setActiveView] = useState('benefits'); // 'benefits' | 'my-benefits' | 'movements'
  const [userPoints, setUserPoints] = useState(0);
  const [pointsMovements, setPointsMovements] = useState([]);
  const [premiumBenefits, setPremiumBenefits] = useState([]);
  const [userBenefits, setUserBenefits] = useState([]);
  const [obtainedBenefits, setObtainedBenefits] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Estados para modales
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showVoucherModal, setShowVoucherModal] = useState(false);
  const [showPublicationModal, setShowPublicationModal] = useState(false);
  const [selectedBenefit, setSelectedBenefit] = useState(null);
  const [selectedVoucher, setSelectedVoucher] = useState(null);
  const [selectedPublication, setSelectedPublication] = useState(null);
  
  // Estados para filtros y búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [percentageFilter, setPercentageFilter] = useState('');
  const [pointsFilter, setPointsFilter] = useState('');
  const [activityFilter, setActivityFilter] = useState('');
  const [filteredBenefits, setFilteredBenefits] = useState([]);

  useEffect(() => {
    fetchUserPoints();
    fetchPremiumBenefits(); // Cargar beneficios por defecto
  }, []);

  // Efecto para refrescar cuando el componente se vuelve visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // Refrescar puntos cuando la página vuelve a ser visible
        fetchUserPoints();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Efecto para refrescar cuando cambia el usuario
  useEffect(() => {
    if (me?.id) {
      fetchUserPoints();
    }
  }, [me?.id, token]);

  // Efecto para filtrar beneficios
  useEffect(() => {
    if (premiumBenefits.length === 0) {
      setFilteredBenefits([]);
      return;
    }

    try {
      let filtered = [...premiumBenefits];

      // Filtro por término de búsqueda
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(benefit => {
          try {
            return (
              (benefit.title && benefit.title.toLowerCase().includes(term)) ||
              (benefit.description && benefit.description.toLowerCase().includes(term)) ||
              (benefit.publication?.place_name && benefit.publication.place_name.toLowerCase().includes(term)) ||
              (benefit.publication?.city && benefit.publication.city.toLowerCase().includes(term)) ||
              (benefit.publication?.province && benefit.publication.province.toLowerCase().includes(term)) ||
              (benefit.publication?.country && benefit.publication.country.toLowerCase().includes(term)) ||
              (benefit.publication?.continent && benefit.publication.continent.toLowerCase().includes(term)) ||
              (benefit.publication?.activities && Array.isArray(benefit.publication.activities) && 
                benefit.publication.activities.some(activity => 
                  activity && activity.toLowerCase().includes(term)
                )
              )
            );
          } catch (e) {
            console.warn('Error filtering benefit:', e, benefit);
            return false;
          }
        });
      }

      // Filtro por porcentaje de descuento
      if (percentageFilter) {
        if (percentageFilter === 'no-discount') {
          filtered = filtered.filter(benefit => !benefit.discount_percentage);
        } else {
          const [min, max] = percentageFilter.split('-').map(Number);
          filtered = filtered.filter(benefit => {
            const discount = benefit.discount_percentage || 0;
            return discount >= min && (max ? discount <= max : true);
          });
        }
      }

      // Filtro por costo en puntos
      if (pointsFilter) {
        const [min, max] = pointsFilter.split('-').map(Number);
        filtered = filtered.filter(benefit => {
          try {
            const points = calculatePointsCost(benefit);
            return points >= min && (max ? points <= max : true);
          } catch (e) {
            console.warn('Error calculating points for benefit:', e, benefit);
            return false;
          }
        });
      }

      // Filtro por actividad
      if (activityFilter) {
        filtered = filtered.filter(benefit => {
          try {
            return (
              benefit.publication?.activities && 
              Array.isArray(benefit.publication.activities) &&
              benefit.publication.activities.some(activity => 
                activity && activity.toLowerCase().includes(activityFilter.toLowerCase())
              )
            );
          } catch (e) {
            console.warn('Error filtering by activity:', e, benefit);
            return false;
          }
        });
      }

      setFilteredBenefits(filtered);
    } catch (error) {
      console.error('Error in benefits filtering:', error);
      setFilteredBenefits([]);
    }
  }, [premiumBenefits, searchTerm, percentageFilter, pointsFilter, activityFilter]);

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
    setLoading(true);
    setError('');
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

  async function fetchPremiumBenefits() {
    setLoading(true);
    setError('');
    try {
      const data = await request('/api/users/benefits', { token });
      setPremiumBenefits(data || []);
      
      // Obtener beneficios ya obtenidos para marcarlos
      const userBenefitsData = await request('/api/users/my-benefits', { token });
      const obtainedIds = new Set(userBenefitsData.map(ub => ub.benefit.publication.id));
      setObtainedBenefits(obtainedIds);
    } catch (e) {
      console.error('Error al cargar beneficios:', e);
      setError('Error al cargar los beneficios premium');
    } finally {
      setLoading(false);
    }
  }

  async function fetchUserBenefits() {
    setLoading(true);
    setError('');
    try {
      const data = await request('/api/users/my-benefits', { token });
      setUserBenefits(data || []);
    } catch (e) {
      console.error('Error al cargar mis beneficios:', e);
      setError('Error al cargar mis beneficios');
    } finally {
      setLoading(false);
    }
  }

  async function redeemBenefit(benefitId) {
    try {
      setLoading(true);
      const result = await request(`/api/users/benefits/${benefitId}/redeem`, { 
        method: 'POST', 
        token 
      });
      
      // Actualizar puntos
      setUserPoints(result.remaining_points);
      
      // Marcar beneficio como obtenido
      setObtainedBenefits(prev => new Set([...prev, selectedBenefit.publication.id]));
      
      setShowConfirmModal(false);
      setSelectedBenefit(null);
      
      // Mostrar mensaje de éxito
      alert(`¡Beneficio obtenido! Código: ${result.voucher_code}`);
      
    } catch (e) {
      setError(e.detail || 'Error al obtener el beneficio');
    } finally {
      setLoading(false);
    }
  }

  function calculatePointsCost(benefit) {
    try {
      if (benefit && typeof benefit.discount_percentage === 'number' && benefit.discount_percentage > 0) {
        return benefit.discount_percentage * 2;
      }
      return 20; // Beneficios gratuitos/upgrades
    } catch (e) {
      console.warn('Error calculating points cost:', e, benefit);
      return 20; // Valor por defecto seguro
    }
  }

  function handleObtainBenefit(benefit) {
    setSelectedBenefit(benefit);
    setShowConfirmModal(true);
  }

  function handleShowVoucher(voucher) {
    setSelectedVoucher(voucher);
    setShowVoucherModal(true);
  }

  function handleShowPublication(publication) {
    setSelectedPublication(publication);
    setShowPublicationModal(true);
  }

  function handleViewChange(view) {
    setActiveView(view);
    if (view === 'movements') {
      fetchPointsMovements();
    } else if (view === 'benefits') {
      fetchPremiumBenefits();
    } else if (view === 'my-benefits') {
      fetchUserBenefits();
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
      case 'invitation_bonus': return '👥';
      case 'bonus': return '🎁';
      case 'redeemed': return '💸';
      default: return '💎';
    }
  };

  const getMovementDescription = (movement) => {
    switch (movement.transaction_type) {
      case 'review_earned': 
        return `Puntos ganados por reseña: "${movement.description}"`;
      case 'invitation_bonus':
        return `Puntos por invitar a: ${movement.description}`;
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
          💎 {loading ? '...' : userPoints} puntos
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Pestañas de navegación */}
      <div className="d-flex mb-4 border-bottom">
        <button
          className={`btn pb-2 ${activeView === 'benefits' ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => handleViewChange('benefits')}
        >
          🎁 Beneficios disponibles
        </button>
        <button
          className={`btn pb-2 ${activeView === 'my-benefits' ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => handleViewChange('my-benefits')}
        >
          🎯 Mis descuentos
        </button>
        <button
          className={`btn pb-2 ${activeView === 'movements' ? "border-bottom border-3 border-primary fw-bold" : "text-muted"}`}
          onClick={() => handleViewChange('movements')}
        >
          📋 Historial de puntos
        </button>
      </div>

      {/* Vista: Beneficios disponibles */}
      {activeView === 'benefits' && (
        <div>
          {/* Sección prominente de puntos */}
          <div className="row mb-4">
            <div className="col-lg-6">
              <div className="card shadow-sm border-warning">
                <div className="card-body text-center">
                  <div className="display-4 text-warning mb-3">💎</div>
                  <h4 className="mb-2">Tus puntos actuales</h4>
                  <div className="display-5 fw-bold text-primary mb-3">{loading ? '...' : userPoints}</div>
                  <p className="text-muted">
                    Ganá más puntos escribiendo reseñas detalladas
                  </p>
                </div>
              </div>
            </div>
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
                        <span className="me-3 fs-4">👥</span>
                        <div>
                          <strong>Invitar un amigo</strong>
                          <br />
                          <small className="text-muted">+50 puntos por invitación exitosa</small>
                        </div>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Beneficios disponibles */}
          <h5 className="mb-4">🎁 Beneficios disponibles</h5>
          
          {/* Filtros y búsqueda */}
          <div className="card shadow-sm mb-4">
            <div className="card-body">
              <div className="row g-3">
                {/* Búsqueda manual */}
                <div className="col-12 col-md-6 col-lg-4">
                  <label className="form-label small fw-bold">🔍 Buscar beneficios</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Buscar por lugar, país, actividad..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                
                {/* Filtro por porcentaje */}
                <div className="col-12 col-md-6 col-lg-2">
                  <label className="form-label small fw-bold">💸 % Descuento</label>
                  <select
                    className="form-select"
                    value={percentageFilter}
                    onChange={(e) => setPercentageFilter(e.target.value)}
                  >
                    <option value="">Todos</option>
                    <option value="no-discount">Sin descuento</option>
                    <option value="1-10">1% - 10%</option>
                    <option value="10-20">10% - 20%</option>
                    <option value="20-30">20% - 30%</option>
                    <option value="30-50">30% - 50%</option>
                    <option value="50">50%+</option>
                  </select>
                </div>
                
                {/* Filtro por puntos */}
                <div className="col-12 col-md-6 col-lg-2">
                  <label className="form-label small fw-bold">💎 Puntos</label>
                  <select
                    className="form-select"
                    value={pointsFilter}
                    onChange={(e) => setPointsFilter(e.target.value)}
                  >
                    <option value="">Todos</option>
                    <option value="1-20">1 - 20</option>
                    <option value="20-40">20 - 40</option>
                    <option value="40-60">40 - 60</option>
                    <option value="60-100">60 - 100</option>
                    <option value="100">100+</option>
                  </select>
                </div>
                
                {/* Filtro por actividad */}
                <div className="col-12 col-md-6 col-lg-2">
                  <label className="form-label small fw-bold">🎯 Actividad</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Ej: restaurante"
                    value={activityFilter}
                    onChange={(e) => setActivityFilter(e.target.value)}
                  />
                </div>
                
                {/* Botón limpiar filtros */}
                <div className="col-12 col-md-6 col-lg-2 d-flex align-items-end">
                  <button
                    type="button"
                    className="btn btn-outline-secondary w-100"
                    onClick={() => {
                      setSearchTerm('');
                      setPercentageFilter('');
                      setPointsFilter('');
                      setActivityFilter('');
                    }}
                  >
                    🗑️ Limpiar
                  </button>
                </div>
              </div>
              
              {/* Contador de resultados */}
              {!loading && (
                <div className="mt-3 text-muted small">
                  {searchTerm || percentageFilter || pointsFilter || activityFilter ? (
                    <>Mostrando {filteredBenefits.length} de {premiumBenefits.length} beneficios</>
                  ) : (
                    <>{premiumBenefits.length} beneficios disponibles</>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="row g-4">
            {loading ? (
              <div className="col-12 text-center py-4">
                <div className="spinner-border spinner-border-sm me-2" role="status"></div>
                Cargando beneficios...
              </div>
            ) : (searchTerm || percentageFilter || pointsFilter || activityFilter) && filteredBenefits.length === 0 ? (
              <div className="col-12">
                <div className="text-center py-4 text-muted">
                  <div className="mb-3">🔍</div>
                  <p>No se encontraron beneficios con los filtros aplicados.</p>
                  <small>Intenta modificar los criterios de búsqueda.</small>
                </div>
              </div>
            ) : premiumBenefits.length === 0 ? (
              <div className="col-12">
                <div className="text-center py-4 text-muted">
                  <div className="mb-3">🎁</div>
                  <p>No hay beneficios disponibles en este momento.</p>
                  <small>Agregamos nuevos descuentos y ofertas regularmente.</small>
                </div>
              </div>
            ) : (
              (searchTerm || percentageFilter || pointsFilter || activityFilter ? filteredBenefits : premiumBenefits).map((benefit) => {
              const pointsCost = calculatePointsCost(benefit);
              const isObtained = obtainedBenefits.has(benefit.publication.id);
              
              return (
                <div className="col-md-6 col-lg-4" key={benefit.id}>
                  <div className="card shadow-sm h-100">
                    <div className="card-body">
                      <div className="d-flex align-items-start justify-content-between mb-3">
                        <h5 className="card-title mb-0 flex-grow-1">{benefit.title}</h5>
                        {benefit.discount_percentage && (
                          <span className="badge bg-success ms-2">
                            -{benefit.discount_percentage}%
                          </span>
                        )}
                        {benefit.benefit_type === 'free_item' && (
                          <span className="badge bg-primary ms-2">GRATIS</span>
                        )}
                        {benefit.benefit_type === 'upgrade' && (
                          <span className="badge bg-warning text-dark ms-2">UPGRADE</span>
                        )}
                      </div>
                      
                      <h6 className="text-primary mb-2">
                        📍 {benefit.publication.place_name}
                      </h6>
                      
                      <p className="text-muted small mb-2">
                        {benefit.publication.city}, {benefit.publication.province}
                      </p>
                      
                      <p className="mb-3">{benefit.description}</p>
                      
                      <div className="bg-light p-2 rounded mb-3">
                        <small className="text-muted">
                          💎 <strong>Costo: {pointsCost} puntos</strong>
                        </small>
                      </div>
                      
                      {benefit.terms_conditions && (
                        <div className="bg-light p-2 rounded mb-3">
                          <small className="text-muted">
                            <strong>Términos:</strong> {benefit.terms_conditions}
                          </small>
                        </div>
                      )}
                    </div>
                    
                    <div className="card-footer bg-transparent">
                      <div className="d-grid gap-2">
                        <button
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => handleShowPublication(benefit.publication)}
                        >
                          Ver detalle de publicación
                        </button>
                        
                        {isObtained ? (
                          <button className="btn btn-success btn-sm" disabled>
                            ✅ ¡Obtenido!
                          </button>
                        ) : (
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleObtainBenefit(benefit)}
                            disabled={userPoints < pointsCost}
                          >
                            {userPoints < pointsCost ? 'Puntos insuficientes' : 'Obtener beneficio'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
            )}
          </div>
        </div>
      )}

      {/* Vista: Mis descuentos */}
      {activeView === 'my-benefits' && (
        <div className="row g-4">
          {loading ? (
            <div className="col-12 text-center py-4">
              <div className="spinner-border spinner-border-sm me-2" role="status"></div>
              Cargando mis beneficios...
            </div>
          ) : userBenefits.length === 0 ? (
            <div className="col-12">
              <div className="text-center py-4 text-muted">
                <div className="mb-3">🎫</div>
                <p>No tienes beneficios canjeados aún.</p>
                <small>Ve a la pestaña "Beneficios disponibles" para obtener descuentos.</small>
              </div>
            </div>
          ) : (
            userBenefits.map((userBenefit) => {
              const benefit = userBenefit.benefit;
              return (
                <div className="col-md-6 col-lg-4" key={userBenefit.id}>
                  <div className="card shadow-sm h-100 border-success">
                    <div className="card-body">
                      <div className="d-flex align-items-start justify-content-between mb-3">
                        <h5 className="card-title mb-0 flex-grow-1">{benefit.title}</h5>
                        <span className="badge bg-success">ACTIVO</span>
                      </div>
                      
                      <h6 className="text-primary mb-2">
                        📍 {benefit.publication.place_name}
                      </h6>
                      
                      <p className="text-muted small mb-2">
                        {benefit.publication.city}, {benefit.publication.province}
                      </p>
                      
                      <p className="mb-3">{benefit.description}</p>
                      
                      <div className="bg-light p-2 rounded mb-3">
                        <small className="text-muted">
                          <strong>Obtenido:</strong> {new Date(userBenefit.obtained_at).toLocaleDateString('es-ES')}
                          <br />
                          <strong>Código:</strong> {userBenefit.voucher_code}
                        </small>
                      </div>
                    </div>
                    
                    <div className="card-footer bg-transparent">
                      <div className="d-grid gap-2">
                        <button
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => handleShowPublication(benefit.publication)}
                        >
                          Ver detalle de publicación
                        </button>
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleShowVoucher(userBenefit)}
                        >
                          📱 Mostrar comprobante
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
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
                <small>Comenzá a escribir reseñas o invitar amigos para ganar tus primeros puntos.</small>
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

      {/* Modal de confirmación para obtener beneficio */}
      {showConfirmModal && selectedBenefit && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">🎁 Confirmar beneficio</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowConfirmModal(false)}
                ></button>
              </div>
              <div className="modal-body">
                <div className="text-center mb-3">
                  <h5>{selectedBenefit.title}</h5>
                  <p className="text-muted">📍 {selectedBenefit.publication.place_name}</p>
                </div>
                
                <div className="alert alert-warning">
                  <strong>¿Estás seguro de querer obtener este beneficio?</strong>
                  <br />
                  Se descontarán <strong>{calculatePointsCost(selectedBenefit)} puntos</strong> de tu cuenta.
                </div>
                
                <div className="bg-light p-3 rounded">
                  <small>
                    <strong>Puntos actuales:</strong> {userPoints}<br />
                    <strong>Costo del beneficio:</strong> -{calculatePointsCost(selectedBenefit)}<br />
                    <strong>Puntos restantes:</strong> {userPoints - calculatePointsCost(selectedBenefit)}
                  </small>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowConfirmModal(false)}
                >
                  No, cancelar
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => redeemBenefit(selectedBenefit.id)}
                  disabled={loading}
                >
                  {loading ? 'Procesando...' : 'Sí, obtener beneficio'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de comprobante */}
      {showVoucherModal && selectedVoucher && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">🎫 Comprobante de beneficio</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowVoucherModal(false)}
                ></button>
              </div>
              <div className="modal-body text-center">
                <div className="border rounded p-4 bg-light">
                  <h4 className="text-primary mb-3">Plan&Go Premium</h4>
                  
                  {selectedVoucher.benefit.discount_percentage && (
                    <div className="badge bg-success fs-6 mb-3">
                      -{selectedVoucher.benefit.discount_percentage}% DESCUENTO
                    </div>
                  )}
                  
                  <h5 className="mb-2">{selectedVoucher.benefit.title}</h5>
                  
                  <p className="mb-2">
                    <strong>📍 {selectedVoucher.benefit.publication.place_name}</strong>
                  </p>
                  
                  <p className="text-muted small mb-3">
                    {selectedVoucher.benefit.publication.address}<br />
                    {selectedVoucher.benefit.publication.city}, {selectedVoucher.benefit.publication.province}
                  </p>
                  
                  <hr />
                  
                  <div className="row text-start">
                    <div className="col-6">
                      <small><strong>Usuario:</strong></small>
                    </div>
                    <div className="col-6">
                      <small>{me?.username || 'Usuario Premium'}</small>
                    </div>
                    
                    <div className="col-6">
                      <small><strong>Código:</strong></small>
                    </div>
                    <div className="col-6">
                      <small className="font-monospace">{selectedVoucher.voucher_code}</small>
                    </div>
                    
                    <div className="col-6">
                      <small><strong>N° Beneficio:</strong></small>
                    </div>
                    <div className="col-6">
                      <small>#{String(selectedVoucher.id).padStart(6, '0')}</small>
                    </div>
                    
                    <div className="col-6">
                      <small><strong>Válido desde:</strong></small>
                    </div>
                    <div className="col-6">
                      <small>{new Date(selectedVoucher.obtained_at).toLocaleDateString('es-ES')}</small>
                    </div>
                    
                    {selectedVoucher.benefit.publication.original_price && selectedVoucher.benefit.discount_percentage && (
                      <>
                        <div className="col-6">
                          <small><strong>Precio original:</strong></small>
                        </div>
                        <div className="col-6">
                          <small>${selectedVoucher.benefit.publication.original_price}</small>
                        </div>
                        
                        <div className="col-6">
                          <small><strong>Precio con descuento:</strong></small>
                        </div>
                        <div className="col-6">
                          <small className="text-success">
                            <strong>${selectedVoucher.benefit.publication.discounted_price?.toFixed(2)}</strong>
                          </small>
                        </div>
                      </>
                    )}
                  </div>
                  
                  <hr />
                  
                  {/* Simulación de código QR */}
                  <div className="bg-white border rounded p-3 mb-3">
                    <div style={{
                      width: '120px',
                      height: '120px',
                      margin: '0 auto',
                      backgroundColor: '#000',
                      display: 'grid',
                      gridTemplate: 'repeat(12, 1fr) / repeat(12, 1fr)',
                      gap: '1px'
                    }}>
                      {Array.from({length: 144}).map((_, i) => (
                        <div 
                          key={i}
                          style={{ 
                            backgroundColor: Math.random() > 0.5 ? '#000' : '#fff' 
                          }}
                        />
                      ))}
                    </div>
                    <small className="text-muted mt-2">Código QR único</small>
                  </div>
                  
                  <small className="text-muted">
                    Presenta este comprobante en el establecimiento para aplicar tu beneficio.
                  </small>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowVoucherModal(false)}
                >
                  Cerrar
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => window.print()}
                >
                  📱 Imprimir/Guardar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de publicación */}
      {showPublicationModal && selectedPublication && (
        <PublicationDetailModal
          open={showPublicationModal}
          pub={selectedPublication}
          onClose={() => setShowPublicationModal(false)}
          me={me}
          token={token}
        />
      )}
    </div>
  );
}
