import React, { useState } from "react";
import { api } from "../api";

export default function ForgotPassword({ setView }) {
  const [step, setStep] = useState("enter-email");
  const [identifier, setIdentifier] = useState("");
  const [questions, setQuestions] = useState(null);
  const [answers, setAnswers] = useState({
    security_answer_1: "",
    security_answer_2: "",
  });
  const [resetToken, setResetToken] = useState("");
  const [passwords, setPasswords] = useState({
    new_password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function handleEmailSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api("/api/auth/forgot-password/get-questions", {
        method: "POST",
        body: { identifier },
      });
      setQuestions(data);
      setStep("answer-questions");
    } catch (err) {
      setError(
        err.detail || "Usuario no encontrado o sin preguntas configuradas.",
      );
    }
  }

  async function handleAnswersSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api("/api/auth/forgot-password/verify-answers", {
        method: "POST",
        body: { ...answers, identifier },
      });
      setResetToken(data.access_token);
      setStep("set-password");
    } catch (err) {
      setError(err.detail || "Respuestas incorrectas.");
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setError("");
    if (
      passwords.new_password.length < 8 ||
      passwords.new_password !== passwords.confirm_password
    ) {
      setError("Las contraseñas no coinciden o son muy cortas.");
      return;
    }
    try {
      const data = await api("/api/auth/forgot-password/set-new-password", {
        method: "POST",
        token: resetToken,
        body: { new_password: passwords.new_password },
      });
      setMessage(data.message);
      setStep("success");
    } catch (err) {
      setError(
        err.detail ||
          "Error al cambiar la contraseña. El permiso puede haber expirado.",
      );
    }
  }

  if (step === "success") {
    return (
      <div>
        <div className="alert alert-success">{message}</div>
        <button
          onClick={() => setView("login")}
          className="btn btn-outline-custom w-100"
        >
          Volver a Iniciar Sesión
        </button>
      </div>
    );
  }

  if (step === "set-password") {
    return (
      <div>
        <h3 className="mb-4">Crear Nueva Contraseña</h3>
        <form onSubmit={handlePasswordSubmit}>
          <div className="mb-3">
            <label>Nueva Contraseña</label>
            <input
              type="password"
              name="new_password"
              className="form-control"
              onChange={(e) =>
                setPasswords((p) => ({ ...p, new_password: e.target.value }))
              }
              required
            />
          </div>
          <div className="mb-3">
            <label>Confirmar Contraseña</label>
            <input
              type="password"
              name="confirm_password"
              className="form-control"
              onChange={(e) =>
                setPasswords((p) => ({
                  ...p,
                  confirm_password: e.target.value,
                }))
              }
              required
            />
          </div>
          {error && <div className="alert alert-danger">{error}</div>}
          <button type="submit" className="btn btn-outline-custom w-100">
            Guardar Contraseña
          </button>
        </form>
      </div>
    );
  }

  if (step === "answer-questions") {
    return (
      <div>
        <h3 className="mb-4">Responder Preguntas</h3>
        <p>
          Hola, <strong>{questions.username}</strong>. Responde tus preguntas de
          seguridad.
        </p>
        <form onSubmit={handleAnswersSubmit}>
          <div className="mb-3">
            <label className="form-label text-muted">
              {questions.security_question_1}
            </label>
            <input
              type="text"
              name="security_answer_1"
              className="form-control"
              onChange={(e) =>
                setAnswers((a) => ({ ...a, security_answer_1: e.target.value }))
              }
              required
              value={answers.security_answer_1}
              autoComplete="off"
            />
          </div>
          <div className="mb-3">
            <label className="form-label text-muted">
              {questions.security_question_2}
            </label>
            <input
              type="text"
              name="security_answer_2"
              className="form-control"
              onChange={(e) =>
                setAnswers((a) => ({ ...a, security_answer_2: e.target.value }))
              }
              required
              value={answers.security_answer_2}
              autoComplete="off"
            />
          </div>
          {error && <div className="alert alert-danger">{error}</div>}
          <button type="submit" className="btn btn-outline-custom w-100">
            Verificar Respuestas
          </button>
          <div className="text-center mt-3">
            <button onClick={() => setView("login")} className="btn btn-link">
              Volver a Iniciar Sesión
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-4">Recuperar Contraseña</h3>
      <p className="text-muted">
        Ingresa tu email o nombre de usuario para empezar.
      </p>
      <form onSubmit={handleEmailSubmit}>
        <div className="mb-3">
          <label htmlFor="identifier" className="form-label">
            Email o Nombre de Usuario
          </label>
          <input
            type="text"
            className="form-control"
            id="identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <button type="submit" className="btn btn-outline-custom w-100">
          Buscar Preguntas
        </button>
      </form>
      <div className="text-center mt-3">
        <button onClick={() => setView("login")} className="btn btn-link">
          Volver a Iniciar Sesión
        </button>
      </div>
    </div>
  );
}
