import React, { useState } from 'react'
import AuthForm from '../components/AuthForm'
import { api } from '../api'


export default function Register({ setView }) {
    // Nuevo estado para controlar si el registro fue exitoso
    const [registrationSuccess, setRegistrationSuccess] = useState(false)

    async function handleRegister({ username, email, password }) {
        await api('/api/auth/register', {
            method: 'POST',
            body: { username, email, password }
        });
        setRegistrationSuccess(true)
    }

    // Si el registro fue exitoso, mostramos el mensaje y el boton
    if (registrationSuccess) {
        return (
            <div className="text-center">
                <h3 className="mb-3">✅ ¡Registro exitoso!</h3>
                <p>Tu cuenta se ha creado correctamente. Ahora puedes iniciar sesión.</p>
                <button
                    onClick={() => setView('login')}
                    className="btn btn-primary w-100 mt-2"
                >
                    Ir a Iniciar Sesión
                </button>
            </div>
        )
    }

    // Si no funciono elr egister (caso mail ya registrado), mostramos el formulario
    return <AuthForm title="Registrarse" onSubmit={handleRegister} isRegister={true} />
}