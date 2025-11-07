import React from 'react';
import logo from '../assets/images/logo.png';
import './Sidebar.css';

export default function Sidebar({ me, onNavigate, onLogout, activeView }) {
  const isAdmin = me?.role === 'admin' || me?.username === 'admin';
  const isPremium = me?.role === 'premium';

  const menuItems = isAdmin ? [
    { id: 'approved-publications', label: 'Publicaciones Aprobadas' },
    { id: 'all-publications', label: 'Todas las Publicaciones' },
    { id: 'pending-approvals', label: 'Solicitudes de aprobación' },
    { id: 'deletion-requests', label: 'Solicitudes de eliminación' },
  ] : [
    { id: 'publications', label: '📰 Publicaciones' },
    // Mostrar "Mis publicaciones" solo si el usuario es premium
    ...(isPremium ? [{ id: 'my-publications', label: '✏️ Mis publicaciones' }] : []),
    { id: 'favorites', label: '❤️ Mis favoritos' },
    { id: 'preferences', label: '⚙️ Configurar preferencias' },
    { id: 'itinerary', label: '🤖🗺️Generar itinerario con IA' },
    { id: 'my-itineraries', label: '📅 Mis itinerarios' },
    { id: 'expenses', label: '💰 Mis gastos' },
    { id: 'invite-friends', label: '✉️ Invitar amigos' }
  ];

  return (
    <div
      className="d-flex flex-column text-dark vh-100 position-fixed shadow-lg"
      style={{
        width: '280px',
        top: 0,
        left: 0,
        overflowY: 'auto',
        zIndex: 1000,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(10px)'
      }}
    >
      {/* Logo */}
      <div className="p-3 text-center border-bottom" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
        <img src={logo} alt="Plan&Go Logo" style={{ width: '120px' }} />
      </div>

      {/* Menu items */}
      <nav className="flex-grow-1 p-2">
        <div className="mb-2 px-3 text-uppercase small text-muted fw-bold">Menú</div>
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`btn w-100 text-start mb-1 sidebar-menu-item ${activeView === item.id ? 'active' : 'btn-light text-dark'
              }`}
            onClick={() => onNavigate(item.id)}
            style={{
              borderRadius: '8px',
              padding: '10px 16px'
            }}
          >
            <span className="me-2">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* User actions */}
      <div className="p-3 border-top" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
        <button
          className="btn w-100 mb-2"
          onClick={() => onNavigate('profile')}
          style={{ borderColor: '#3A92B5', color: '#3A92B5' }}
        >
          Ver Perfil
        </button>
        {!isAdmin && (
          <button
            className="btn  w-100 mb-2"
            onClick={() => onNavigate('suggestions')}
            style={{ borderColor: '#3A92B5', color: '#3A92B5' }}
          >
            Sugerencias
          </button>
        )}
        <button
          className="btn btn-outline-danger w-100 mb-2"
          onClick={onLogout}
        >
          Cerrar Sesión
        </button>
      </div>
    </div>
  );
}
