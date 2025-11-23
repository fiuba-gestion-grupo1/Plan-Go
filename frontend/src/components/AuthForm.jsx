import React, { useState } from "react";

export default function AuthForm({ title, onSubmit, isRegister = false }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  const [identifier, setIdentifier] = useState("");

  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const payload = isRegister
        ? { username, email, password }
        : { identifier, password };

      await onSubmit(payload);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2 className="text-center mb-4">{title}</h2>

      {isRegister ? (
        <>
          <div className="mb-3">
            <label htmlFor="usernameInput" className="form-label">
              Nombre de usuario
            </label>
            <input
              id="usernameInput"
              placeholder="tu nombre de usuario"
              type="text"
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="emailInput" className="form-label">
              Correo electrónico
            </label>
            <input
              id="emailInput"
              placeholder="ejemplo@correo.com"
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </>
      ) : (
        <div className="mb-3">
          <label htmlFor="identifierInput" className="form-label">
            Email o Nombre de usuario
          </label>
          <input
            id="identifierInput"
            placeholder="tu usuario o correo electronico"
            type="text"
            className="form-control"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
        </div>
      )}

      <div className="mb-3">
        <label htmlFor="passwordInput" className="form-label">
          Contraseña
        </label>
        <input
          id="passwordInput"
          placeholder="Contraseña"
          type="password"
          className="form-control"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>

      {error && (
        <div className="alert alert-danger p-2 text-center">{error}</div>
      )}
      <button type="submit" className="btn btn-outline-custom w-100 mt-3">
        {title}
      </button>
    </form>
  );
}
