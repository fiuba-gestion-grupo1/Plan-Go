import React, { useState } from 'react'

export default function AuthForm({ title, onSubmit, isRegister = false }) {
    // Estados para los campos de registro
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');

    // Estado para el campo de login ('identifier')
    const [identifier, setIdentifier] = useState('');

    // Estado común para la contraseña
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');
        try {
            // Construye el payload correcto dependiendo de si es registro o login
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
                //---CAMPOS PARA LA VISTA DE REGISTRO---
                <>
                    <div className="mb-3">
                        <label htmlFor="usernameInput" className="form-label">Nombre de usuario</label>
                        <input
                            id="usernameInput"
                            placeholder="tu nombre de usuario"
                            type="text"
                            className="form-control"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="mb-3">
                        <label htmlFor="emailInput" className="form-label">Correo electrónico</label>
                        <input
                            id="emailInput"
                            placeholder="ejemplo@correo.com"
                            type="email"
                            className="form-control"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            required
                        />
                    </div>
                </>
            ) : (
                // ---CAMPO PARA LA VISTA DE LOGIN---
                <div className="mb-3">
                    <label htmlFor="identifierInput" className="form-label">Email o Nombre de usuario</label>
                    <input
                        id="identifierInput"
                        placeholder="tu usuario o correo electronico"
                        type="text"
                        className="form-control"
                        value={identifier}
                        onChange={e => setIdentifier(e.target.value)}
                        required
                    />
                </div>
            )}

            {/*---CAMPO COMÚN DE CONTRASEÑA---*/}
            <div className="mb-3">
                <label htmlFor="passwordInput" className="form-label">Contraseña</label>
                <input
                    id="passwordInput"
                    placeholder="Contraseña"
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />
            </div>

            {error && <div className="alert alert-danger p-2 text-center">{error}</div>}
            <button type="submit" className="btn btn-outline-custom w-100 mt-3">{title}</button>
        </form>
    )
}