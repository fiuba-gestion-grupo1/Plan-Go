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
import Backoffice from "./pages/Backoffice";
import Suggestions from "./pages/Suggestions";


export default function App() {
  const [view, setView] = useState('login') // login | register | forgot-password (solo para la vista pública)
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [me, setMe] = useState(null)
  const [authView, setAuthView] = useState('home') // home | profile | backoffice (dentro de sesión)

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      (async () => {
        try {
          const meResp = await api('/api/auth/me', { token });
          setMe(meResp);

          // Si es admin => llevarlo a backoffice, si no => home
          const isAdmin = meResp?.role === 'admin' || meResp?.username === 'admin';
          setAuthView(isAdmin ? 'backoffice' : 'home');
        } catch (e) {
          localStorage.removeItem('token');
          setToken('');
          setMe(null);
          setAuthView('home');
        }
      })();
    }
  }, [token]);

  function handleLogout() {
    localStorage.removeItem('token');
    setToken('');
    setMe(null);
    setAuthView('home');
  }

  // Navegación interna protegida (evita que un no-admin fuerce backoffice)
  function handleNavigate(nextView) {
    const isAdmin = me?.role === 'admin' || me?.username === 'admin';
    if (nextView === 'backoffice' && !isAdmin) {
      return setAuthView('home');
    }
    setAuthView(nextView);
  }

  // --- Vista de usuario autenticado ---
  if (token && me) {
    return (
      <div
        className="d-flex flex-column min-vh-100"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed'
        }}
      >
        <Navbar
          me={me}
          onLogout={handleLogout}
          onNavigate={handleNavigate}
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
          {authView === 'backoffice' && <Backoffice me={me} />}
          {authView === 'suggestions' && <Suggestions me={me} token={token} />}
        </div>
      </div>
    )
  }

  //---- Vista de autenticación (Login/Register/ForgotPassword) ----
  return (
    <div
      className="d-flex flex-column align-items-center min-vh-100 py-5"
      style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
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
