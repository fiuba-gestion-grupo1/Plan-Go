import React, { useState } from 'react'


export default function AuthForm({ title, onSubmit }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')


    async function handleSubmit(e){
        e.preventDefault()
        setError('')
        try{ await onSubmit({ email, password }) }catch(e){ setError(e.message) }
    }


    return (
        <form onSubmit={handleSubmit} style={{display:'grid', gap:12, maxWidth:320}}>
            <h2>{title}</h2>
            <input placeholder="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
            <input placeholder="Contraseña" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
            {error && <small style={{color:'crimson'}}>{error}</small>}
            <button>{title}</button>
        </form>
    )
}