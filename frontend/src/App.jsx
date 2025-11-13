// src/App.jsx
import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from 'react-router-dom'

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
import ShareItineraryPage from "./pages/ShareItineraryPage";
import "./styles/buttons.css";

// Premium only
import InviteFriend from "./pages/InviteFriend";

// ----- Shell con Router -----
export default function App() {
  return (
    <BrowserRouter>
      <AppWithRouter />
    </BrowserRouter>
  );
}

function AppWithRouter() {
  const [view, setView] = useState('login'); // login | register | forgot-password
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [me, setMe] = useState(null);
  const [authView, setAuthView] = useState('publications'); // navegación por sidebar

  const navigate = useNavigate();

  // Derivados de rol
  const isAdmin = me?.role === 'admin' || me?.username === 'admin';
  const isPremium = me?.role === 'premium';

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      (async () => {
        try {
          const meResp = await api('/api/auth/me', { token });
          setMe(meResp);
          const isAdminUser = meResp?.role === 'admin' || meResp?.username === 'admin';
          setAuthView(isAdminUser ? 'approved-publications' : 'publications');
        } catch {
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

  

  // Navegación interna (sidebar)
  function handleNavigate(nextView) {
    // Bloquea vistas de admin a no-admin
    if (['pending-approvals', 'deletion-requests', 'approved-publications', 'all-publications'].includes(nextView) && !isAdmin) {
      return setAuthView('publications');
    }
    // Bloquea vistas de usuario a admin
    if (['my-publications', 'favorites', 'preferences', 'invite-friends', 'suggestions'].includes(nextView) && isAdmin) {
      return setAuthView('approved-publications');
    }
    // ▶︎ Premium only: invitar amigos (la de compartir es por ruta)
    if (nextView === 'invite-friends' && !isPremium) {
         alert('Función disponible sólo para usuarios premium.');
         return; // quedarse en la vista actual
    }
    setAuthView(nextView);
  }

  // --------- Elemento principal (con o sin auth) ----------
  let mainElement = null;

  if (token && me) {
    mainElement = (
      <div className="d-flex" style={{ minHeight: '100vh' }}>
        {/* Sidebar */}
        <Sidebar
          me={me}
          onLogout={handleLogout}
          onNavigate={handleNavigate}
          activeView={authView}
        />

        {/* Contenido principal */}
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
            {/* Publicaciones */}
            {authView === 'publications' && (
              isAdmin ? (
                <Backoffice me={me} view="publications" />
              ) : (
                <Home
                  key="publications"
                  me={me}
                  view="publications"
                  onOpenShareItinerary={(id) => {
                    // Guard de premium también acá por si llamás callback directo
                    if (!isPremium) { alert('Función disponible sólo para usuarios premium.'); return; }
                    navigate(`/share-itinerary/${id}`);
                  }}
                />
              )
            )}

            {/* Usuario */}
            {authView === 'my-publications' && !isAdmin && (
              <Home
                key="my-publications"
                me={me}
                view="my-publications"
                onOpenShareItinerary={(id) => {
                  if (!isPremium) { alert('Función disponible sólo para usuarios premium.'); return; }
                  navigate(`/share-itinerary/${id}`);
                }}
              />
            )}
            {authView === 'favorites' && !isAdmin && (
              <Home
                key="favorites"
                me={me}
                view="favorites"
                onOpenShareItinerary={(id) => {
                  if (!isPremium) { alert('Función disponible sólo para usuarios premium.'); return; }
                  navigate(`/share-itinerary/${id}`);
                }}
              />
            )}
            {authView === 'preferences' && !isAdmin && (
              <Home key="preferences" me={me} view="preferences" />
            )}
            {authView === 'itinerary' && (
              <Home
                key="itinerary"
                me={me}
                view="itinerary"
                onOpenShareItinerary={(id) => {
                  if (!isPremium) { alert('Función disponible sólo para usuarios premium.'); return; }
                  navigate(`/share-itinerary/${id}`);
                }}
              />
            )}
            {authView === 'my-itineraries' && (
              <Home
                key="my-itineraries"
                me={me}
                view="my-itineraries"
                onOpenShareItinerary={(id) => {
                  if (!isPremium) { alert('Función disponible sólo para usuarios premium.'); return; }
                  navigate(`/share-itinerary/${id}`);
                }}
              />
            )}

            {authView === 'expenses' && !isAdmin && (
              <Home key="expenses" me={me} view="expenses" />
            )}

            {/* ▶︎ Premium only: Invitar amigos */}
            {authView === 'invite-friends' && !isAdmin && isPremium && (
              <InviteFriend token={token} />
            )}

            {/* Admin */}
            {authView === 'approved-publications' && isAdmin && <Backoffice me={me} view="publications" />}
            {authView === 'all-publications' && isAdmin && <Backoffice me={me} view="all-publications" />}
            {authView === 'pending-approvals' && isAdmin && <Backoffice me={me} view="pending" />}
            {authView === 'deletion-requests' && isAdmin && <Backoffice me={me} view="deletion-requests" />}
            {authView === 'review-reports' && isAdmin && <Backoffice me={me} view="review-reports" />}

            {/* Comunes */}
            {authView === 'profile' && <Profile me={me} token={token} setMe={setMe} />}
            {authView === 'suggestions' && !isAdmin && <Suggestions me={me} token={token} />}
          </div>
        </div>
      </div>
    );
  } else {
    // ---- Auth (Login/Register/ForgotPassword) ----
    mainElement = (
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
    );
  }

  // --------- Rutas (incluye compartir con guard premium) ----------
  return (
    <Routes>
      <Route path="/" element={mainElement} />
      <Route
        path="/share-itinerary/:id"
        element={
          token && isPremium
            ? <ShareItineraryPage />
            : <Navigate to="/" replace />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
