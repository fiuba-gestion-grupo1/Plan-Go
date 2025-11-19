import React, { useState, useRef } from 'react';
import logo from '../assets/images/logo.png';
import { useOnClickOutside } from '../hooks/useOnClickOutside';
import './Sidebar.css';

export default function Sidebar({ me, onNavigate, onLogout, activeView }) {
  const isAdmin = me?.role === 'admin' || me?.username === 'admin';
  const isPremium = me?.role === 'premium';
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef();

  useOnClickOutside(menuRef, () => setShowUserMenu(false));

  const menuItems = isAdmin ? [
    { id: 'approved-publications', label: 'Publicaciones Aprobadas' },
    { id: 'all-publications', label: 'Todas las Publicaciones' },
    { id: 'pending-approvals', label: 'Solicitudes de aprobación' },
    { id: 'deletion-requests', label: 'Solicitudes de eliminación' },
    { id: 'review-reports', label: 'Reportes de reseñas' },
  ] : [
    { id: 'publications', label: '📰 Publicaciones' },
    // Mostrar "Mis publicaciones" solo si el usuario es premium
    ...(isPremium ? [{ id: 'my-publications', label: '✏️ Mis publicaciones' }] : []),
    
    // --- NUEVO HUB DE EXPERIENCIA VIAJERA ---
    // Este nuevo item reemplaza a 'favorites', 'my-itineraries' y 'expenses'
    { id: 'traveler-experience-hub', label: '🗺️ Experiencia Viajera' },

    // { id: 'favorites', label: '❤️ Mis favoritos' }, <-- ELIMINADO/MOVIDO
    { id: 'suggestions', label: '💡 Sugerencias' },
    { id: 'itinerary', label: '🤖 Generar itinerario con IA' },
    // { id: 'my-itineraries', label: '📅 Mis itinerarios' }, <-- ELIMINADO/MOVIDO
    // { id: 'expenses', label: '💰 Mis gastos' }, <-- ELIMINADO/MOVIDO
    
    // Mostrar "Beneficios" solo si el usuario es premium
    ...(isPremium ? [{ id: 'benefits', label: '🎁 Beneficios' }] : []),
    // Mostrar "Invitar amigos" solo si el usuario es premium
    ...(isPremium ? [{ id: 'invite-friends', label: '✉️ Invitar amigos' }] : [])
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
      {/* Header con logo y menú de usuario */}
      <div className="d-flex justify-content-between align-items-center p-3 border-bottom" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
        <img src={logo} alt="Plan&Go Logo" style={{ width: '120px' }} />
        
        {/* Menú desplegable de usuario */}
        <div className="position-relative" ref={menuRef}>
          <button
            className="btn btn-light p-2 rounded-circle"
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              width: '40px',
              height: '40px',
              border: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>⋯</span>
          </button>
          
          {showUserMenu && (
            <div
              className="position-absolute bg-white border rounded shadow-lg"
              style={{
                top: '45px',
                right: '0',
                minWidth: '200px',
                zIndex: 1001,
                borderColor: 'rgba(0,0,0,0.1)'
              }}
            >
              <div className="py-1">
                <button
                  className="btn w-100 text-start px-3 py-2"
                  onClick={() => {
                    onNavigate('preferences');
                    setShowUserMenu(false);
                  }}
                  style={{ border: 'none', backgroundColor: 'transparent' }}
                >
                  <span className="me-2">⚙️</span>
                  Configurar preferencias
                </button>
                <button
                  className="btn w-100 text-start px-3 py-2"
                  onClick={() => {
                    onNavigate('profile');
                    setShowUserMenu(false);
                  }}
                  style={{ border: 'none', backgroundColor: 'transparent' }}
                >
                  <span className="me-2">👤</span>
                  Ver Perfil
                </button>
                <hr className="my-1" style={{ margin: '0 16px' }} />
                <button
                  className="btn w-100 text-start px-3 py-2 text-danger"
                  onClick={() => {
                    onLogout();
                    setShowUserMenu(false);
                  }}
                  style={{ border: 'none', backgroundColor: 'transparent' }}
                >
                  <span className="me-2">🚪</span>
                  Cerrar Sesión
                </button>
              </div>
            </div>
          )}
        </div>
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
            <span className="me-2">{item.label.split(' ')[0]}</span> 
            {/* Aquí se asume que el primer elemento es el emoji */}
            <span>{item.label.substring(item.label.split(' ')[0].length).trim()}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}