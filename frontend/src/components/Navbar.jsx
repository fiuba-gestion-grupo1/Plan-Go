import React from 'react';
import logo from '../assets/images/logo.png'; 

// Recibe el usuario (me), la función de logout (onLogout)
// y la función para cambiar de vista (setAuthView)
export default function Navbar({ me, onLogout, setAuthView }) {
    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
            <div className="container">
                <a
                    className="navbar-brand"
                    href="#"
                    onClick={(e) => { e.preventDefault(); setAuthView('home'); }} // Al hacer clic en el logo, vamos a home
                >
                    <img src={logo} alt="Plan&Go Logo" style={{ width: '100px' }} />
                </a>
                <div className="ms-auto dropdown">
                    <button
                        className="btn btn-link nav-link dropdown-toggle fw-bold"
                        type="button"
                        id="profileDropdown"
                        data-bs-toggle="dropdown"
                        aria-expanded="false"
                    >
                        Hola, {me.username}
                    </button>

                    <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="profileDropdown">
                        <li>
                            <button
                                className="dropdown-item"
                                onClick={() => setAuthView('profile')}
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
        </nav>
    );
}