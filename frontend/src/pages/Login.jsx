import React from 'react'
import AuthForm from '../components/AuthForm'
import { api } from '../api'

export default function Login({ setToken }) {
    async function handleLogin({ identifier, password }) {
        const { access_token } = await api('/api/auth/login', {
            method: 'POST',
            body: { identifier, password }
        });
        setToken(access_token);
    }

    return <AuthForm title="Iniciar sesión" onSubmit={handleLogin} />
}