import React, { useState, useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate,
  Navigate,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";

import TravelerExperience from "./pages/TravelerExperience";
import SearchUsers from "./pages/SearchUsers";
import TravelerProfile from "./pages/TravelerProfile";

import Home from "./pages/Home";
import Profile from "./pages/Profile";
import Backoffice from "./pages/Backoffice";
import Suggestions from "./pages/Suggestions";
import ShareItineraryPage from "./pages/ShareItineraryPage";

import InviteFriend from "./pages/InviteFriend";
import Benefits from "./pages/Benefits";
import ItinerarySelector from "./pages/ItinerarySelector";
import ItineraryRequest from "./pages/ItineraryRequest";
import CustomItinerary from "./pages/CustomItinerary";

import { api } from "./api";
import Sidebar from "./components/Sidebar";

import logo from "./assets/images/logo.png";
import backgroundImage from "./assets/images/background.png";

import "./styles/buttons.css";

export default function App() {
  return (
    <BrowserRouter>
      <AppWithRouter />
    </BrowserRouter>
  );
}

function AppWithRouter() {
  const [view, setView] = useState("login");
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [me, setMe] = useState(null);
  const [authView, setAuthView] = useState("publications");

  const navigate = useNavigate();

  const isAdmin = me?.role === "admin" || me?.username === "admin";
  const isPremium = me?.role === "premium";

  useEffect(() => {
    if (token) {
      localStorage.setItem("token", token);
      (async () => {
        try {
          const meResp = await api("/api/auth/me", { token });
          setMe(meResp);
          const isAdminUser =
            meResp?.role === "admin" || meResp?.username === "admin";

          const urlParams = new URLSearchParams(window.location.search);
          const viewParam = urlParams.get("view");
          const showIdParam = urlParams.get("showId");

          if (viewParam) {
            console.log("🔗 [URL] Vista desde URL:", viewParam);
            setAuthView(viewParam);
            if (showIdParam) {
              console.log("🔗 [URL] ID para mostrar:", showIdParam);
              localStorage.setItem("showItineraryId", showIdParam);
            }
          } else {
            setAuthView(isAdminUser ? "approved-publications" : "publications");
          }
        } catch {
          localStorage.removeItem("token");
          setToken("");
          setMe(null);
          setAuthView("publications");
        }
      })();
    }
  }, [token]);

  function handleLogout() {
    localStorage.removeItem("token");
    setToken("");
    setMe(null);
    setAuthView("publications");
    navigate("/");
  }

  function handleNavigate(nextView) {
    if (
      [
        "pending-approvals",
        "deletion-requests",
        "approved-publications",
        "all-publications",
      ].includes(nextView) &&
      !isAdmin
    ) {
      setAuthView("publications");
      navigate("/");
      return;
    }

    if (
      [
        "my-publications",
        "preferences",
        "invite-friends",
        "suggestions",
        "benefits",
      ].includes(nextView) &&
      isAdmin
    ) {
      setAuthView("approved-publications");
      navigate("/");
      return;
    }

    if (nextView === "invite-friends" && !isPremium) {
      alert("Función disponible sólo para usuarios premium.");
      return;
    }
    if (nextView === "benefits" && !isPremium) {
      alert("Función disponible sólo para usuarios premium.");
      return;
    }

    if (nextView === "search-travelers") {
      setAuthView("search-travelers");
      navigate("/viajeros");
      return;
    }

    if (nextView === "my-traveler-profile") {
      setAuthView("my-traveler-profile");
      navigate("/perfil");
      return;
    }

    setAuthView(nextView);
    navigate("/");
  }

  const backgroundStyle = {
    marginLeft: "280px",
    backgroundImage: `url(${backgroundImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    backgroundAttachment: "fixed",
    minHeight: "100vh",
    overflowY: "auto",
  };

  function renderShell(children) {
    return (
      <div className="d-flex" style={{ minHeight: "100vh" }}>
        <Sidebar
          me={me}
          onLogout={handleLogout}
          onNavigate={handleNavigate}
          activeView={authView}
        />
        <div className="flex-grow-1" style={backgroundStyle}>
          <div className="container-fluid p-4">{children}</div>
        </div>
      </div>
    );
  }

  let mainElement = null;

  if (token && me) {
    const hubContent = (
      <>
        {authView === "traveler-experience-hub" && (
          <TravelerExperience onNavigate={handleNavigate} me={me} />
        )}

        {authView === "favorites" && !isAdmin && (
          <Home
            key="favorites"
            me={me}
            view="favorites"
            onOpenShareItinerary={(id) => {
              if (!isPremium) {
                alert("Función disponible sólo para usuarios premium.");
                return;
              }
              navigate(`/share-itinerary/${id}`);
            }}
          />
        )}
        {authView === "my-itineraries" && (
          <Home
            key="my-itineraries"
            me={me}
            view="my-itineraries"
            onOpenShareItinerary={(id) => {
              if (!isPremium) {
                alert("Función disponible sólo para usuarios premium.");
                return;
              }
              navigate(`/share-itinerary/${id}`);
            }}
          />
        )}
        {authView === "expenses" && !isAdmin && (
          <Home key="expenses" me={me} view="expenses" />
        )}

        {authView === "search-travelers" && !isAdmin && (
          <SearchUsers
            me={me}
            onOpenMyProfile={() => handleNavigate("my-traveler-profile")}
          />
        )}

        {authView === "my-traveler-profile" && !isAdmin && (
          <TravelerProfile me={me} />
        )}

        {authView === "publications" &&
          (isAdmin ? (
            <Backoffice me={me} view="publications" />
          ) : (
            <Home
              key="publications"
              me={me}
              view="publications"
              onOpenShareItinerary={(id) => {
                if (!isPremium) {
                  alert("Función disponible sólo para usuarios premium.");
                  return;
                }
                navigate(`/share-itinerary/${id}`);
              }}
            />
          ))}

        {authView === "my-publications" && !isAdmin && (
          <Home
            key="my-publications"
            me={me}
            view="my-publications"
            onOpenShareItinerary={(id) => {
              if (!isPremium) {
                alert("Función disponible sólo para usuarios premium.");
                return;
              }
              navigate(`/share-itinerary/${id}`);
            }}
          />
        )}

        {authView === "preferences" && !isAdmin && (
          <Home key="preferences" me={me} view="preferences" />
        )}

        {authView === "itinerary" && (
          <ItinerarySelector onNavigate={handleNavigate} />
        )}

        {authView === "itinerary-ai" && <ItineraryRequest me={me} />}

        {authView === "itinerary-custom" && (
          <CustomItinerary me={me} token={token} />
        )}

        {authView === "invite-friends" && !isAdmin && isPremium && (
          <InviteFriend token={token} />
        )}

        {authView === "benefits" && !isAdmin && isPremium && (
          <Benefits token={token} me={me} />
        )}

        {authView === "approved-publications" && isAdmin && (
          <Backoffice me={me} view="publications" />
        )}
        {authView === "all-publications" && isAdmin && (
          <Backoffice me={me} view="all-publications" />
        )}
        {authView === "pending-approvals" && isAdmin && (
          <Backoffice me={me} view="pending" />
        )}
        {authView === "deletion-requests" && isAdmin && (
          <Backoffice me={me} view="deletion-requests" />
        )}
        {authView === "review-reports" && isAdmin && (
          <Backoffice me={me} view="review-reports" />
        )}

        {authView === "profile" && (
          <Profile me={me} token={token} setMe={setMe} />
        )}
        {authView === "suggestions" && !isAdmin && (
          <Suggestions me={me} token={token} />
        )}
      </>
    );

    mainElement = renderShell(hubContent);
  } else {
    mainElement = (
      <div
        className="d-flex flex-column align-items-center min-vh-100 py-5"
        style={{
          backgroundImage: `url(${backgroundImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          backgroundAttachment: "fixed",
        }}
      >
        <div
          className="text-center"
          style={{ maxWidth: "480px", width: "100%" }}
        >
          <div className="mb-4">
            <img
              src={logo}
              alt="Plan&Go Logo"
              style={{ width: "200px", height: "auto" }}
            />
          </div>

          <div className="card p-4 shadow-sm">
            {view === "login" && (
              <Login setToken={setToken} setView={setView} />
            )}
            {view === "register" && <Register setView={setView} />}
            {view === "forgot-password" && <ForgotPassword setView={setView} />}
          </div>

          <div className="text-center mt-3">
            <button
              onClick={() => setView(view === "login" ? "register" : "login")}
              className="btn btn-link text-blue fw-bold"
            >
              {view === "login"
                ? "¿No tenes cuenta? Registrate Acá!"
                : "Ya tengo una cuenta"}
            </button>

            {view === "login" && (
              <div className="mt-2">
                <button
                  onClick={() => setView("forgot-password")}
                  className="btn btn-link btn-sm"
                >
                  ¿Has olvidado tu contraseña?
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={mainElement} />

      <Route
        path="/share-itinerary/:id"
        element={
          token && isPremium ? (
            <ShareItineraryPage />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="/perfil"
        element={
          token && me ? (
            renderShell(<TravelerProfile me={me} />)
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="/viajeros"
        element={
          token && me ? (
            renderShell(
              <SearchUsers
                me={me}
                onOpenMyProfile={() => handleNavigate("my-traveler-profile")}
              />,
            )
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="/viajeros/:userId"
        element={
          token && me ? (
            renderShell(<TravelerProfile me={me} />)
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
