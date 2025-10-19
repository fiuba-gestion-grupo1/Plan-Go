import React from 'react';
import { useState, useEffect } from 'react';
import { api } from '../api';

export default function Profile({ me, token, setMe }) {

    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        first_name: me.first_name || '', 
        last_name: me.last_name || '',
        birth_date: me.birth_date || '',
        travel_preferences: me.travel_preferences || '',
    });

    useEffect(() => {
        setFormData({
            first_name: me.first_name || '',
            last_name: me.last_name || '',
            birth_date: me.birth_date ? me.birth_date.split('T')[0] : '', 
            travel_preferences: me.travel_preferences || '',
        });
    }, [me]);

    function handleChange(e) {
        const { name, value } = e.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: value,
        }));
    }

    async function handleSubmit(e) {
        e.preventDefault();
        try {
            const updatedUser = await api('/api/auth/me', {
                method: 'PUT',
                token: token, 
                body: formData
            });

            setMe(updatedUser); 
            alert('¡Perfil actualizado con éxito!');
            setIsEditing(false);

        } catch (error) {
            console.error('Error al actualizar el perfil:', error);
            alert(`Error al actualizar el perfil: ${error.message || 'Revisa la consola.'}`);
        }
    }

    function formatDisplayDate(dateString) {
        if (!dateString) return 'No especificado';
        try {
            return new Date(dateString).toLocaleDateString('es-AR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                timeZone: 'UTC' 
            });
        } catch (e) {
            return 'Fecha inválida';
        }
    }

    const photoPlaceholderStyle = {
        width: '150px',
        height: '150px',
        backgroundColor: '#e9ecef', 
        borderRadius: '50%', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#6c757d', 
        margin: '0 auto 2rem auto', 
        fontSize: '1.2rem',
        fontWeight: 'bold',
    };

    if (isEditing) {
        // --- VISTA DE EDICIÓN (El formulario que ya tenías) ---
        return (
            <div className="container mt-4" style={{ maxWidth: '700px' }}>
                <div className="card shadow-sm">
                    <div className="card-body p-4 p-md-5">
                        <form onSubmit={handleSubmit}>
                            <h2 className="card-title text-center mb-4">Editar Perfil</h2>

                            <div className="text-center mb-4">
                                <div style={photoPlaceholderStyle}><span>Foto</span></div>
                                <button type="button" className="btn btn-sm btn-link mt-2" disabled>
                                    (Subir foto próximamente)
                                </button>
                            </div>

                            <div className="mb-3">
                                <label className="form-label fw-bold">Nombre de usuario</label>
                                <input type="text" className="form-control" value={me.username} disabled readOnly />
                            </div>
                            <div className="mb-3">
                                <label className="form-label fw-bold">Email</label>
                                <input type="email" className="form-control" value={me.email || ''} disabled readOnly />
                            </div>

                            <hr className="my-4" />
                            <h4 className="h5 mb-3">Datos Opcionales</h4>
                            
                            <div className="row g-3 mb-3">
                                <div className="col-md-6">
                                    <label htmlFor="first_name" className="form-label">Nombre</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        id="first_name"
                                        name="first_name"
                                        value={formData.first_name}
                                        onChange={handleChange}
                                    />
                                </div>
                                <div className="col-md-6">
                                    <label htmlFor="last_name" className="form-label">Apellido</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        id="last_name"
                                        name="last_name"
                                        value={formData.last_name}
                                        onChange={handleChange}
                                    />
                                </div>
                            </div>
                            <div className="mb-3">
                                <label htmlFor="birth_date" className="form-label">Fecha de Nacimiento</label>
                                <input
                                    type="date"
                                    className="form-control"
                                    id="birth_date"
                                    name="birth_date"
                                    value={formData.birth_date}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="mb-3">
                                <label htmlFor="travel_preferences" className="form-label">Preferencias de Viaje</label>
                                <textarea
                                    className="form-control"
                                    id="travel_preferences"
                                    name="travel_preferences"
                                    rows="4"
                                    placeholder="Ej: Me gusta la playa, prefiero hostels..."
                                    value={formData.travel_preferences}
                                    onChange={handleChange}
                                ></textarea>
                            </div>

                            {/* --- BOTONES MODIFICADOS --- */}
                            <div className="text-end mt-4">
                                <button 
                                    type="button" // Importante: 'type="button"' para no enviar el form
                                    className="btn btn-secondary btn-lg me-2" 
                                    onClick={() => setIsEditing(false)} // Botón para cancelar
                                >
                                    Cancelar
                                </button>
                                <button type="submit" className="btn btn-primary btn-lg">
                                    Guardar Cambios
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }

    // --- VISTA "VER PERFIL" (Solo lectura, por defecto) ---
    return (
        <div className="container mt-4" style={{ maxWidth: '700px' }}>
            <div className="card shadow-sm">
                <div className="card-body p-4 p-md-5">
                    <h2 className="card-title text-center mb-4">Mi Perfil</h2>

                    <div className="text-center mb-4">
                        <div style={photoPlaceholderStyle}><span>Foto</span></div>
                    </div>

                    {/* Mostramos los datos fijos */}
                    <p className="fs-5 mb-2">
                        <strong className="d-block text-muted">Nombre de usuario:</strong> {me.username}
                    </p>
                    <p className="fs-5">
                        <strong className="d-block text-muted">Email:</strong> {me.email}
                    </p>

                    <hr className="my-4" />
                    <h4 className="h5 mb-3">Datos Adicionales</h4>

                    {/* Mostramos los datos opcionales */}
                    <p className="fs-5 mb-2">
                        <strong className="d-block text-muted">Nombre:</strong> 
                        {me.first_name || 'No especificado'}
                    </p>
                    <p className="fs-5 mb-2">
                        <strong className="d-block text-muted">Apellido:</strong> 
                        {me.last_name || 'No especificado'}
                    </p>
                    <p className="fs-5 mb-3">
                        <strong className="d-block text-muted">Fecha de Nacimiento:</strong> 
                        {formatDisplayDate(me.birth_date)}
                    </p>

                    <strong className="d-block text-muted fs-5 mb-2">Preferencias de Viaje:</strong>
                    <div className="p-3 bg-light rounded" style={{ minHeight: '100px', whiteSpace: 'pre-wrap' }}>
                        {me.travel_preferences || 'No especificadas'}
                    </div>

                    {/* Botón para entrar en modo edición */}
                    <div className="text-end mt-4">
                        <button 
                            className="btn btn-primary btn-lg" 
                            onClick={() => setIsEditing(true)}
                        >
                            Editar Perfil
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}