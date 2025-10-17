import React, { useState } from 'react'

export default function AuthForm({ title, onSubmit }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    async function handleSubmit(e) {
        e.preventDefault()
        setError('')
        try {
            await onSubmit({ email, password })
        } catch (e) {
            setError(e.message)
        }
    }

    return (
        <form onSubmit={handleSubmit}>
            <h2 className="text-center mb-4">{title}</h2>

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

            <button type="submit" className="btn btn-primary w-100 mt-3">{title}</button>
        </form>
    )
}