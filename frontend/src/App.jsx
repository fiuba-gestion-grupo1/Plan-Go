import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './api'
import logo from './assets/images/logo.png'
import backgroundImage from './assets/images/background.png'
import Sidebar from './components/Sidebar'
import Home from './pages/Home'
import Profile from './pages/Profile'
import ForgotPassword from './pages/ForgotPassword'
import Backoffice from "./pages/Backoffice";
import Suggestions from "./pages/Suggestions";


export default function App() {
  const [view, setView] = useState('login') // login | register | forgot-password (solo para la vista pública)
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [me, setMe] = useState(null)
  const [authView, setAuthView] = useState('publications') // Nueva navegación por sidebar

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      (async () => {
        try {
          const meResp = await api('/api/auth/me', { token });
          setMe(meResp);

          // Si es admin => approved-publications por defecto, si no => publications
          const isAdminUser = meResp?.role === 'admin' || meResp?.username === 'admin';
          setAuthView(isAdminUser ? 'approved-publications' : 'publications');
        } catch (e) {
          localStorage.removeItem('token');
          setToken('');
          setMe(null);
          setAuthView('publications');
        }
      })();
    }
  }, [token]);

  function handleLogout() {
    localStorage.removeItem('token');
    setToken('');
    setMe(null);
    setAuthView('publications');
  }

  // Navegación interna protegida
  function handleNavigate(nextView) {
    const isAdmin = me?.role === 'admin' || me?.username === 'admin';
    // Evita que usuarios normales accedan a vistas de admin
    if (['pending-approvals', 'deletion-requests', 'approved-publications', 'all-publications'].includes(nextView) && !isAdmin) {
      return setAuthView('publications');
    }
    // Evita que admins accedan a vistas de usuarios (excepto itinerary e my-itineraries)
    if (['my-publications', 'favorites', 'preferences'].includes(nextView) && isAdmin) {
      return setAuthView('approved-publications');
    }
    setAuthView(nextView);
  }

  // --- Vista de usuario autenticado ---
  if (token && me) {
    const isAdmin = me?.role === 'admin' || me?.username === 'admin';

    return (
      <div className="d-flex" style={{ minHeight: '100vh' }}>
        {/* Sidebar fijo a la izquierda */}
        <Sidebar
          me={me}
          onLogout={handleLogout}
          onNavigate={handleNavigate}
          activeView={authView}
        />

        {/* Contenido principal con margen para el sidebar */}
        <div
          className="flex-grow-1"
          style={{
            marginLeft: '280px',
            backgroundImage: `url(${backgroundImage})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            backgroundAttachment: 'fixed',
            minHeight: '100vh',
            overflowY: 'auto'
          }}
        >
          <div className="container-fluid p-4">
            {/* Vista de Publicaciones (común para todos) */}
            {authView === 'publications' && (
              isAdmin ? <Backoffice me={me} view="publications" /> : <Home me={me} view="publications" />
            )}
            
            {/* Vistas de Usuario */}
            {authView === 'my-publications' && !isAdmin && <Home me={me} view="my-publications" />}
            {authView === 'favorites' && !isAdmin && <Home me={me} view="favorites" />}
            {authView === 'preferences' && !isAdmin && <Home me={me} view="preferences" />}
            {authView === 'itinerary' && <Home me={me} view="itinerary" />}
            {authView === 'my-itineraries' && <Home me={me} view="my-itineraries" />}
            
            {/* Vistas de Admin */}
            {authView === 'approved-publications' && isAdmin && <Backoffice me={me} view="publications" />}
            {authView === 'all-publications' && isAdmin && <Backoffice me={me} view="all-publications" />}
            {authView === 'pending-approvals' && isAdmin && <Backoffice me={me} view="pending" />}
            {authView === 'deletion-requests' && isAdmin && <Backoffice me={me} view="deletion-requests" />}
            
            {/* Vistas comunes */}
            {authView === 'profile' && (
              <Profile me={me} token={token} setMe={setMe} />
            )}
            {authView === 'suggestions' && !isAdmin && <Suggestions me={me} token={token} />}
          </div>
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
