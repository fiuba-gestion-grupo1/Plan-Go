import React from 'react';
import logo from '../assets/images/logo.png';

// Recibe:
// - me: usuario actual
// - onLogout: función para cerrar sesión
// - onNavigate: función para cambiar la vista interna (home|profile|backoffice)
// - onSearch: función para manejar búsquedas
export default function Navbar({ me, onLogout, onNavigate }) {
  const isAdmin = me?.role === 'admin' || me?.username === 'admin';

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
      <div className="container">
        <a
          className="navbar-brand"
          href="#"
          onClick={(e) => { e.preventDefault(); onNavigate('home'); }}
        >
          <img src={logo} alt="Plan&Go Logo" style={{ width: '100px' }} />
        </a>

        <div className="d-flex align-items-center ms-auto">
          {/* Acceso visible sólo para admins */}
          {isAdmin && (
            <button
              className="btn btn-outline-primary me-3"
              onClick={() => onNavigate('backoffice')}
              title="Ir al Backoffice"
            >
              Backoffice
            </button>
          )}

          <div className="dropdown">
            <button
              className="btn btn-link nav-link dropdown-toggle fw-bold"
              type="button"
              id="profileDropdown"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Hola, {me.first_name || me.username}
            </button>

            <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="profileDropdown">
              <li>
                <button
                  className="dropdown-item"
                  onClick={() => onNavigate('profile')}
                >
                  Ver Perfil
                </button>
              </li>
              <li><hr className="dropdown-divider" /></li>
              <li>
                <button className="dropdown-item text-danger" onClick={onLogout}>
                  Cerrar Sesión
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </nav>
  );
}
