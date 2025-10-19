import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './api'
import logo from './assets/images/logo.png'
import backgroundImage from './assets/images/background.png'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Profile from './pages/Profile'

export default function App() {
    const [view, setView] = useState('login')
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [me, setMe] = useState(null)
    const [authView, setAuthView] = useState('home')

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
        setAuthView('home');
    }

    // --- Vista de usuario autenticado ---
    if (token && me) {
        return (
            <div className="d-flex flex-column vh-100 bg-light">
                <Navbar 
                    me={me} 
                    onLogout={handleLogout} 
                    setAuthView={setAuthView} 
                />

                <div className="flex-grow-1">
                    {authView === 'home' && <Home me={me} />}
                    {authView === 'profile' && <Profile me={me} />}
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