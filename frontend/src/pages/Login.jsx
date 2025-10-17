import React from 'react'
import AuthForm from '../components/AuthForm'
import { api } from '../api'

export default function Login({ setToken }) {
    async function handleLogin({ email, password }) {
        const { access_token } = await api('/api/auth/login', {
            method: 'POST',
            body: { email, password }
        });
        setToken(access_token);
    }

    return <AuthForm title="Iniciar sesión" onSubmit={handleLogin} />
}