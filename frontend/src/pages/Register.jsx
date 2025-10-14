import React from 'react'
import AuthForm from '../components/AuthForm'
import { api } from '../api'


export default function Register(){
    return <AuthForm title="Registrarse" onSubmit={({email, password})=> api('/api/auth/register', { method:'POST', body:{ email, password } }) } />
}
