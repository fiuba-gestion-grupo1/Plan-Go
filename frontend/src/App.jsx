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

// 👇 NUEVO
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
  const [view, setView] = useState('login') // login | register | forgot-password (solo para la vista pública)
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [me, setMe] = useState(null)
  const [authView, setAuthView] = useState('publications') // Nueva navegación por sidebar

  const navigate = useNavigate();

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

  // 🔹 Escucha el evento global que dispara Home: abre la ruta /share-itinerary/:id
  useEffect(() => {
    const openShare = (e) => {
      const id = e?.detail?.id;
      if (!id) return;
      navigate(`/share-itinerary/${id}`);
    };
    window.addEventListener('open-share-itinerary', openShare);
    return () => window.removeEventListener('open-share-itinerary', openShare);
  }, [navigate]);

  // Navegación interna protegida (sidebar)
  function handleNavigate(nextView) {
    const isAdmin = me?.role === 'admin' || me?.username === 'admin';
    // Evita que usuarios normales accedan a vistas de admin
    if (['pending-approvals', 'deletion-requests', 'approved-publications', 'all-publications'].includes(nextView) && !isAdmin) {
      return setAuthView('publications');
    }
    // Evita que admins accedan a vistas de usuarios (agrego invite-friends)
    if (['my-publications', 'favorites', 'preferences', 'invite-friends', 'suggestions'].includes(nextView) && isAdmin) {
      return setAuthView('approved-publications');
    }
    setAuthView(nextView);
  }

  // --------- Elemento principal (con o sin auth) ----------
  let mainElement = null;

  if (token && me) {
    const isAdmin = me?.role === 'admin' || me?.username === 'admin';

    mainElement = (
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
              isAdmin ? <Backoffice me={me} view="publications" /> : (
                <Home
                  key="publications"
                  me={me}
                  view="publications"
                  // (opcional) si luego querés llamar callback en lugar de evento:
                  onOpenShareItinerary={(id) => navigate(`/share-itinerary/${id}`)}
                />
              )
            )}
            
            {/* Vistas de Usuario */}
            {authView === 'my-publications' && !isAdmin && (
              <Home
                key="my-publications"
                me={me}
                view="my-publications"
                onOpenShareItinerary={(id) => navigate(`/share-itinerary/${id}`)}
              />
            )}
            {authView === 'favorites' && !isAdmin && (
              <Home
                key="favorites"
                me={me}
                view="favorites"
                onOpenShareItinerary={(id) => navigate(`/share-itinerary/${id}`)}
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
                onOpenShareItinerary={(id) => navigate(`/share-itinerary/${id}`)}
              />
            )}
            {authView === 'my-itineraries' && (
              <Home
                key="my-itineraries"
                me={me}
                view="my-itineraries"
                onOpenShareItinerary={(id) => navigate(`/share-itinerary/${id}`)}
              />
            )}

            {authView === 'expenses' && !isAdmin && (
              <Home key="expenses" me={me} view="expenses" />
            )}

            {/* 👇 NUEVO: vista Invitar amigos */}
            {authView === 'invite-friends' && !isAdmin && <InviteFriend token={token} />}

            {/* Vistas de Admin */}
            {authView === 'approved-publications' && isAdmin && <Backoffice me={me} view="publications" />}
            {authView === 'all-publications' && isAdmin && <Backoffice me={me} view="all-publications" />}
            {authView === 'pending-approvals' && isAdmin && <Backoffice me={me} view="pending" />}
            {authView === 'deletion-requests' && isAdmin && <Backoffice me={me} view="deletion-requests" />}
            {authView === 'review-reports' && isAdmin && <Backoffice me={me} view="review-reports" />}

            {/* Vistas comunes */}
            {authView === 'profile' && (
              <Profile me={me} token={token} setMe={setMe} />
            )}
            {authView === 'suggestions' && !isAdmin && <Suggestions me={me} token={token} />}
          </div>
        </div>
      </div>
    );
  } else {
    //---- Vista de autenticación (Login/Register/ForgotPassword) ----
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

  // --------- Definición de rutas (incluye la página de compartir) ----------
  return (
    <Routes>
      {/* Tu app tradicional (estado por authView) vive en "/" */}
      <Route path="/" element={mainElement} />
      {/* Nueva ruta con react-router para ShareItineraryPage */}
      <Route
        path="/share-itinerary/:id"
        element={token ? <ShareItineraryPage /> : <Navigate to="/" replace />}
      />
      {/* Catch-all: redirige a home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
