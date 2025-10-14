import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './api'


export default function App(){
    const [view, setView] = useState('login')
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [me, setMe] = useState(null)


    useEffect(()=>{ if(token){ localStorage.setItem('token', token); api('/api/auth/me', { token }).then(setMe).catch(()=>setToken('')) } }, [token])


    if(token && me){
        return (
            <div style={{display:'grid', placeItems:'center', height:'100vh', gap:16}}>
                <h1>Plan&Go</h1>
                <p>Bienvenido, <b>{me.email}</b></p>
                <button onClick={()=>{ localStorage.removeItem('token'); setToken(''); setMe(null) }}>Salir</button>
            </div>
        )
    }


    return (
        <div style={{display:'grid', placeItems:'center', height:'100vh', gap:24}}>
            <h1>Plan&Go</h1>
            <div style={{display:'flex', gap:24}}>
            {view === 'login' ? <Login setToken={setToken}/> : <Register/>}
            </div>
            <button onClick={()=> setView(view==='login'?'register':'login')}>
            {view==='login' ? 'Crear cuenta' : 'Ya tengo cuenta'}
            </button>
        </div>
    )
}