import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './api'
import logo from './assets/images/logo.png'
import backgroundImage from './assets/images/background.png'

export default function App() {
    const [view, setView] = useState('login')
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [me, setMe] = useState(null)

    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
            api('/api/auth/me', { token })
                .then(setMe)
                .catch(() => {
                    localStorage.removeItem('token');
                    setToken('');
                });
        }
    }, [token]);

    function handleLogout() {
        localStorage.removeItem('token');
        setToken('');
        setMe(null);
    }

    // --- Vista de usuario autenticado ---
    if (token && me) {
        return (
            <div className="d-flex vh-100 bg-light">
                <div className="container m-auto text-center">
                    <div className="card p-4 shadow-sm" style={{ maxWidth: '400px', margin: 'auto' }}>
                        <img src={logo} alt="Plan&Go Logo" className="mb-4" style={{ width: '150px', margin: '0 auto' }} />
                        <p className="lead">Bienvenido, <strong>{me.username}</strong></p>
                        <button onClick={handleLogout} className="btn btn-danger mt-3">
                            Salir
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    //----Vista de autenticación (Login/Register)----
    return (
        <div
            className="d-flex vh-100"
            style={{
                backgroundImage: `url(${backgroundImage})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat'
            }}
        >
            <div className="container m-auto" style={{ maxWidth: '480px' }}>
                <div className="text-center mb-4">
                    <img src={logo} alt="Plan&Go Logo" style={{ width: '200px', height: 'auto' }} />
                </div>

                <div className="card p-4 shadow-sm">
                    {view === 'login'
                        ? <Login setToken={setToken} />
                        : <Register setView={setView} />
                    }
                </div>

                <div className="text-center mt-3">
                    <button onClick={() => setView(view === 'login' ? 'register' : 'login')} className="btn btn-link text-blue fw-bold">
                        {view === 'login' ? '¿No tenes cuenta? Registrate Acá!' : 'Ya tengo una cuenta'}
                    </button>
                </div>
            </div>
        </div>
    )
}