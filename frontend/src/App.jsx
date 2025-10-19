import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './api'
import logo from './assets/images/logo.png'
import backgroundImage from './assets/images/background.png'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Profile from './pages/Profile'
import ForgotPassword from './pages/ForgotPassword'

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
                    {authView === 'profile' && (
                        <Profile 
                            me={me} 
                            token={token} 
                            setMe={setMe} 
                        />
                    )}
                </div>
            </div>
        )
    }

    //----Vista de autenticación (Login/Register)----
    return (
        <div
            // --- CAMBIOS AQUÍ ---
            // 1. Cambiamos 'vh-100' por 'min-vh-100'
            // 2. Quitamos 'justify-content-center'
            // 3. Agregamos 'py-5' (padding vertical)
            className="d-flex flex-column align-items-center min-vh-100 py-5" 
            style={{
                backgroundImage: `url(${backgroundImage})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat',
                // Agregamos esto para que el fondo se adapte al scroll
                backgroundAttachment: 'fixed' 
            }}
        >
            {/* Este contenedor de agrupación se mantiene igual que la vez anterior */}
            <div className="text-center" style={{ maxWidth: '480px', width: '100%' }}>
                
                <div className="mb-4">
                    <img src={logo} alt="Plan&Go Logo" style={{ width: '200px', height: 'auto' }} />
                </div>

                <div className="card p-4 shadow-sm">
                    {view === 'login' && <Login setToken={setToken} setView={setView} />}
                    {view === 'register' && <Register setView={setView} />}
                    {view === 'forgot-password' && <ForgotPassword setView={setView} />}
                </div>

                <div className="text-center mt-3">
                    <button onClick={() => setView(view === 'login' ? 'register' : 'login')} className="btn btn-link text-blue fw-bold">
                        {view === 'login' ? '¿No tenes cuenta? Registrate Acá!' : 'Ya tengo una cuenta'}
                    </button>
                    
                    {view === 'login' && (
                        <div className="mt-2">
                            <button onClick={() => setView('forgot-password')} className="btn btn-link btn-sm">
                                ¿Has olvidado tu contraseña?
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}