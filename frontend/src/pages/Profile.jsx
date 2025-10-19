import React, { useState, useEffect, useRef } from 'react';
import { api, BASE_URL } from '../api';

export default function Profile({ me, token, setMe }) {

    const [viewMode, setViewMode] = useState('view');
    const [formData, setFormData] = useState({
        first_name: me.first_name || '', 
        last_name: me.last_name || '',
        birth_date: me.birth_date || '',
        travel_preferences: me.travel_preferences || '',
    });
    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: '',
    });
    const [selectedFile, setSelectedFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        if (viewMode === 'edit') {
            setFormData({
                first_name: me.first_name || '',
                last_name: me.last_name || '',
                birth_date: me.birth_date ? me.birth_date.split('T')[0] : '', 
                travel_preferences: me.travel_preferences || '',
            });
        }
    }, [me, viewMode]);

    function handleChange(e) {
        const { name, value } = e.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: value,
        }));
    }

    function handlePasswordChange(e) {
        const { name, value } = e.target;
        setPasswordData(prevData => ({
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
            setViewMode('view');

        } catch (error) {
            console.error('Error al actualizar el perfil:', error);
            alert(`Error al actualizar el perfil: ${error.message || 'Revisa la consola.'}`);
        }
    }

    async function handlePasswordSubmit(e) {
        e.preventDefault();
        const { current_password, new_password, confirm_password } = passwordData;

        if (!current_password || !new_password || !confirm_password) {
            alert('Por favor, completa todos los campos de contraseña.');
            return;
        }
        if (new_password.length < 8) {
            alert('La nueva contraseña debe tener al menos 8 caracteres.');
            return;
        }
        if (new_password !== confirm_password) {
            alert('Las nuevas contraseñas no coinciden.');
            return;
        }

        try {
            await api('/api/auth/change-password', { method: 'POST', token, body: { current_password, new_password } });
            alert('¡Contraseña actualizada con éxito!');
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
            setViewMode('view'); 
        } catch (error) {
            console.error('Error al cambiar contraseña:', error);
            alert(`Error: ${error.detail || error.message}`);
        }
    }

    function handleFileChange(e) {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            // Creamos una URL local para la previsualización
            setPreviewUrl(URL.createObjectURL(file));
        }
    }

    async function handlePhotoSubmit() {
        if (!selectedFile) {
            alert("Por favor, selecciona una foto primero.");
            return;
        }

        const data = new FormData();
        data.append("file", selectedFile);

        try {
            const updatedUser = await api('/api/users/me/photo', {
                method: 'PUT',
                token: token,
                body: data
            });
            setMe(updatedUser); // Actualiza el estado global
            alert("¡Foto de perfil actualizada!");
            
            setSelectedFile(null);
            setPreviewUrl(null);
            
        } catch (error) {
            console.error("Error al subir la foto:", error);
            alert(`Error al subir la foto: ${error.detail || error.message}`);
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

    const photoStyle = {
        width: '150px',
        height: '150px',
        backgroundColor: '#e9ecef', 
        borderRadius: '50%',
        objectFit: 'cover',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#6c757d', 
        margin: '0 auto 1rem auto', 
        fontSize: '1.2rem',
        fontWeight: 'bold',
        border: '3px solid #dee2e6'
    };
    
    const imageUrl = me.profile_picture_url 
        ? `${BASE_URL}${me.profile_picture_url}` 
        : null;

    if (viewMode === 'edit') {
        // --- VISTA DE EDICIÓN ---
        return (
            <div className="container mt-4" style={{ maxWidth: '700px' }}>
                <div className="card shadow-sm">
                    <div className="card-body p-4 p-md-5">
                        <form onSubmit={handleSubmit}>
                            <h2 className="card-title text-center mb-4">Editar Perfil</h2>

                            <div className="text-center mb-4">
                                <img 
                                    src={previewUrl || imageUrl || 'https://via.placeholder.com/150'} 
                                    alt="Perfil" 
                                    style={photoStyle} 
                                    onClick={() => fileInputRef.current.click()} 
                                />
                                <input 
                                    type="file" 
                                    ref={fileInputRef} 
                                    onChange={handleFileChange} 
                                    style={{ display: 'none' }} 
                                    accept="image/png, image/jpeg"
                                />
                                {selectedFile && (
                                    <button type="button" className="btn btn-success mt-2" onClick={handlePhotoSubmit}>
                                        Guardar Foto
                                    </button>
                                )}
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

                            <div className="text-end mt-4">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary btn-lg me-2" 
                                    onClick={() => setViewMode('view')}
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

    if (viewMode === 'password') {
        return (
            <div className="container mt-4" style={{ maxWidth: '700px' }}>
                <div className="card shadow-sm">
                    <div className="card-body p-4 p-md-5">
                        <form onSubmit={handlePasswordSubmit}>
                            <h2 className="card-title text-center mb-4">Cambiar Contraseña</h2>
                            <div className="mb-3">
                                <label htmlFor="current_password" className="form-label">Contraseña Actual</label>
                                <input type="password" className="form-control" id="current_password" name="current_password" value={passwordData.current_password} onChange={handlePasswordChange} required />
                            </div>
                            <div className="mb-3">
                                <label htmlFor="new_password" className="form-label">Nueva Contraseña</label>
                                <input type="password" className="form-control" id="new_password" name="new_password" value={passwordData.new_password} onChange={handlePasswordChange} required minLength="8" />
                            </div>
                            <div className="mb-3">
                                <label htmlFor="confirm_password" className="form-label">Confirmar Nueva Contraseña</label>
                                <input type="password" className="form-control" id="confirm_password" name="confirm_password" value={passwordData.confirm_password} onChange={handlePasswordChange} required minLength="8" />
                            </div>
                            <div className="text-end mt-4">
                                <button type="button" className="btn btn-secondary me-2" onClick={() => setViewMode('view')}>Cancelar</button>
                                <button type="submit" className="btn btn-primary">Actualizar Contraseña</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }

    // --- VISTA "VER PERFIL" ---
    return (
        <div className="container mt-4" style={{ maxWidth: '700px' }}>
            <div className="card shadow-sm">
                <div className="card-body p-4 p-md-5">
                    <h2 className="card-title text-center mb-4">Mi Perfil</h2>

                    <div className="text-center mb-4">
                        {imageUrl ? (
                            <img src={imageUrl} alt="Perfil" style={photoStyle} />
                        ) : (
                            <div style={photoStyle}><span>Foto</span></div>
                        )}
                    </div>

                    <p className="fs-5 mb-2">
                        <strong className="d-block text-muted">Nombre de usuario:</strong> {me.username}
                    </p>
                    <p className="fs-5">
                        <strong className="d-block text-muted">Email:</strong> {me.email}
                    </p>

                    <hr className="my-4" />
                    <h4 className="h5 mb-3">Datos Adicionales</h4>

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

                    <div className="d-flex justify-content-end align-items-center mt-4">
                        <button className="btn btn-link me-3" onClick={() => setViewMode('password')}>
                            Modificar Contraseña
                        </button>
                        <button className="btn btn-primary btn-lg" onClick={() => setViewMode('edit')}>
                            Editar Perfil
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}