import React, { useState, useEffect, useRef } from 'react';
import { api, BASE_URL } from '../api';

// 1. Creamos el componente para el modal de carga
const LoadingModal = ({ status }) => {
    // Si no hay status, no se muestra nada
    if (!status) return null;

    // Textos personalizados según la acción
    const messages = {
        subscribing: 'Procesando pago de suscripción...',
        cancelling: 'Cancelando suscripción...'
    };
    const title = {
        subscribing: 'Pagar Suscripción',
        cancelling: 'Cancelar Suscripción'
    };

    return (
        // Backdrop (fondo oscuro)
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999 // Asegura que esté por encima de todo
        }}>
            {/* Contenido del Modal (la tarjeta) */}
            <div className="card shadow-lg p-4" style={{ minWidth: '300px', maxWidth: '90%' }}>
                <div className="card-body text-center">
                    <h4 className="card-title mb-3">{title[status] || 'Procesando...'}</h4>
                    {/* La "ruedita" (spinner de Bootstrap) */}
                    <div className="spinner-border text-primary" role="status" style={{ width: '3rem', height: '3rem' }}>
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3 mb-0">{messages[status] || 'Por favor, espere.'}</p>
                </div>
            </div>
        </div>
    );
};

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

    // 1. Estado para manejar las notificaciones en pantalla
    const [notification, setNotification] = useState({ type: '', message: '' });

    // 2. Añadimos el nuevo estado para el modal de carga
    // Puede ser: null, 'subscribing', o 'cancelling'
    const [processingStatus, setProcessingStatus] = useState(null);

    // Efecto para que la notificación desaparezca sola después de 5 segundos
    useEffect(() => {
        if (notification.message) {
            const timer = setTimeout(() => {
                setNotification({ type: '', message: '' });
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

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
        setFormData(prev => ({ ...prev, [name]: value }));
    }

    function handlePasswordChange(e) {
        const { name, value } = e.target;
        setPasswordData(prev => ({ ...prev, [name]: value }));
    }

    // --- Funciones de envío actualizadas para usar notificaciones ---

    async function handleSubmit(e) {
        e.preventDefault();
        setNotification({ type: '', message: '' }); // Limpiar notificaciones previas
        try {
            const updatedUser = await api('/api/auth/me', { method: 'PUT', token, body: formData });
            setMe(updatedUser);
            // AQUÍ: Se establece el mensaje de éxito en el estado
            setNotification({ type: 'success', message: '¡Perfil actualizado con éxito!' });
            setViewMode('view');
        } catch (error) {
            setNotification({ type: 'danger', message: error.detail || 'Error al actualizar el perfil.' });
        }
    }

    async function handlePasswordSubmit(e) {
        e.preventDefault();
        setNotification({ type: '', message: '' });
        const { current_password, new_password, confirm_password } = passwordData;

        if (!current_password || !new_password || !confirm_password) {
            setNotification({ type: 'danger', message: 'Por favor, completa todos los campos.' });
            return;
        }
        if (new_password.length < 8) {
            setNotification({ type: 'danger', message: 'La nueva contraseña debe tener al menos 8 caracteres.' });
            return;
        }
        if (new_password !== confirm_password) {
            setNotification({ type: 'danger', message: 'Las nuevas contraseñas no coinciden.' });
            return;
        }

        try {
            await api('/api/auth/change-password', { method: 'POST', token, body: { current_password, new_password } });
            // AQUÍ: Se establece el mensaje de éxito en el estado
            setNotification({ type: 'success', message: '¡Contraseña actualizada con éxito!' });
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
            setViewMode('view');
        } catch (error) {
            setNotification({ type: 'danger', message: error.detail || 'Error al cambiar la contraseña.' });
        }
    }

    async function handlePhotoSubmit() {
        if (!selectedFile) {
            setNotification({ type: 'warning', message: 'Por favor, selecciona una foto primero.' });
            return;
        }
        setNotification({ type: '', message: '' });
        const data = new FormData();
        data.append("file", selectedFile);
        try {
            const updatedUser = await api('/api/users/me/photo', { method: 'PUT', token, body: data });
            setMe(updatedUser);
            // AQUÍ: Se establece el mensaje de éxito en el estado
            setNotification({ type: 'success', message: '¡Foto de perfil actualizada!' });
            setSelectedFile(null);
            setPreviewUrl(null);
        } catch (error) {
            setNotification({ type: 'danger', message: error.detail || 'Error al subir la foto.' });
        }
    }

    //Funcion de manejo de subscripcion
    async function handleSubscribe() {
        setNotification({ type: '', message: '' });

        // 1. Mostrar el modal de carga
        setProcessingStatus('subscribing');

        // 2. Simular espera de 5 segundos (5000 milisegundos)
        await new Promise(resolve => setTimeout(resolve, 5000));

        try {
            // 3. Llamar a la API
            const updatedUser = await api('/api/users/me/subscribe', { method: 'POST', token });
            setMe(updatedUser);
            setNotification({ type: 'success', message: '¡Felicidades! Ahora eres un usuario Premium.' });
        } catch (error) {
            setNotification({ type: 'danger', message: error.detail || 'Error al procesar la suscripción.' });
        } finally {
            // 4. Ocultar el modal (ya sea éxito or error)
            setProcessingStatus(null);
        }
    }

    //Funcion de cancelacion de subscripcion premium
    async function handleCancelSubscription() {
        setNotification({ type: '', message: '' });

        // 1. Mostrar el modal de carga
        setProcessingStatus('cancelling');

        // 2. Simular espera de 5 segundos
        await new Promise(resolve => setTimeout(resolve, 5000));

        try {
            // 3. Llamar a la API
            const updatedUser = await api('/api/users/me/cancel-subscription', { method: 'POST', token });
            setMe(updatedUser);
            setNotification({ type: 'success', message: 'Tu suscripción ha sido cancelada.' });
        } catch (error) {
            setNotification({ type: 'danger', message: error.detail || 'Error al cancelar la suscripción.' });
        } finally {
            // 4. Ocultar el modal
            setProcessingStatus(null);
        }
    }

    // --- Resto de funciones auxiliares (sin cambios) ---

    function handleFileChange(e) {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setPreviewUrl(URL.createObjectURL(file));
        }
    }

    function formatDisplayDate(dateString) {
        if (!dateString) return 'No especificado';
        try {
            return new Date(dateString).toLocaleDateString('es-AR', {
                day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC'
            });
        } catch (e) { return 'Fecha inválida'; }
    }

    // --- Estilos y URLs ---
    const photoStyle = {
        width: '150px',
        height: '150px',
        borderRadius: '50%',
        objectFit: 'cover',
        border: '4px solid #fff',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#e9ecef',
        color: '#6c757d',
        fontWeight: 'bold',
        fontSize: '1.2rem'
    };
    const imageUrl = me.profile_picture_url ? `${BASE_URL}${me.profile_picture_url}` : null;

    // Componente para renderizar la notificación
    const NotificationArea = () => (
        notification.message && (
            <div className={`alert alert-${notification.type} text-center`}>
                {notification.message}
            </div>
        )
    );

    // --- VISTAS RENDERIZADAS ---

    function formatTravelPreferencesDisplay(rawPrefs) {
        if (!rawPrefs) return 'No especificadas';
    
        // Si ya es un objeto, lo uso directo; si es string intento parsear
        let obj = rawPrefs;
        try {
            if (typeof rawPrefs === 'string') {
                obj = JSON.parse(rawPrefs);
            }
        } catch {
            // No es JSON válido → devuelvo el texto tal cual
            return rawPrefs;
        }
    
        if (!obj || typeof obj !== 'object') {
            return rawPrefs;
        }
    
        const parts = [];
    
        if (obj.city) {
            parts.push(obj.city);
        }
        if (Array.isArray(obj.destinations) && obj.destinations.length) {
            parts.push(`Destinos favoritos: ${obj.destinations.join(', ')}`);
        }
        if (obj.style) {
            parts.push(`Estilo de viaje: ${obj.style}`);
        }
        if (obj.budget) {
            parts.push(`Presupuesto: ${obj.budget}`);
        }
        if (obj.about) {
            parts.push(obj.about);
        }
    
        // Si pude armar algo lindo, lo devuelvo; si no, el texto original
        return parts.length ? parts.join(' · ') : rawPrefs;
    }
    

    // Vista para editar el perfil
    if (viewMode === 'edit') {
        return (
            <div className="container mt-4" style={{ maxWidth: '700px' }}>
                <div className="card shadow-sm">
                    <div className="card-body p-4 p-md-5">
                        <form onSubmit={handleSubmit}>
                            <h2 className="card-title text-center mb-4">Editar Perfil</h2>
                            <NotificationArea />
                            {/* Campos del formulario */}
                            <div className="mb-3">
                                <label className="form-label">Nombre</label>
                                <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} className="form-control" />
                            </div>
                            <div className="mb-3">
                                <label className="form-label">Apellido</label>
                                <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} className="form-control" />
                            </div>
                            <div className="mb-3">
                                <label className="form-label">Fecha de Nacimiento</label>
                                <input type="date" name="birth_date" value={formData.birth_date} onChange={handleChange} className="form-control" />
                            </div>
                            <div className="mb-4">
                                <label className="form-label">Preferencias de Viaje</label>
                                <textarea
                                    name="travel_preferences"
                                    value={formData.travel_preferences}
                                    onChange={handleChange}
                                    className="form-control"
                                    rows="3"
                                    placeholder="Ej: Me gusta la playa, prefiero hostels..."
                                ></textarea>
                            </div>
                            <div className="d-grid gap-2 d-md-flex justify-content-md-end">
                                <button type="button" onClick={() => setViewMode('view')} className="btn btn-secondary me-md-2">Cancelar</button>
                                <button type="submit" className="btn btn-outline-custom">Guardar Cambios</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }

    // Vista para cambiar la contraseña
    if (viewMode === 'password') {
        return (
            <div className="container mt-4" style={{ maxWidth: '700px' }}>
                <div className="card shadow-sm">
                    <div className="card-body p-4 p-md-5">
                        <form onSubmit={handlePasswordSubmit}>
                            <h2 className="card-title text-center mb-4">Cambiar Contraseña</h2>
                            <NotificationArea />
                            {/* Campos del formulario */}
                            <div className="mb-3">
                                <label className="form-label">Contraseña Actual</label>
                                <input type="password" name="current_password" value={passwordData.current_password} onChange={handlePasswordChange} className="form-control" />
                            </div>
                            <div className="mb-3">
                                <label className="form-label">Nueva Contraseña</label>
                                <input type="password" name="new_password" value={passwordData.new_password} onChange={handlePasswordChange} className="form-control" />
                            </div>
                            <div className="mb-4">
                                <label className="form-label">Confirmar Nueva Contraseña</label>
                                <input type="password" name="confirm_password" value={passwordData.confirm_password} onChange={handlePasswordChange} className="form-control" />
                            </div>
                            <div className="d-grid gap-2 d-md-flex justify-content-md-end">
                                <button type="button" onClick={() => setViewMode('view')} className="btn btn-secondary me-md-2">Cancelar</button>
                                <button type="submit" className="btn btn-outline-custom">Actualizar Contraseña</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }

    // --- VISTA PRINCIPAL (VER PERFIL) ---
    return (
        < div className="container mt-4" style={{ maxWidth: '700px' }
        }>
            {/*Renderizamos el modal (sólo se verá si processingStatus no es null) */}
            < LoadingModal status={processingStatus} />

            <div className="card shadow-sm">
                <div className="card-body p-4 p-md-5">
                    <h2 className="card-title text-center mb-4">Mi Perfil</h2>
                    <NotificationArea />

                    {/* Sección de la foto de perfil */}
                    <div className="text-center mb-4">
                        <div style={{ position: 'relative', display: 'inline-block' }}>
                            <img src={previewUrl || imageUrl || 'default-avatar.png'} alt="Perfil" style={photoStyle} />
                            <button onClick={() => fileInputRef.current.click()} style={{ position: 'absolute', bottom: '10px', right: '10px', borderRadius: '50%' }} className="btn btn-sm btn-light">
                                ✏️
                            </button>
                            <input type="file" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} accept="image/*" />
                        </div>
                        {selectedFile && (
                            <div className="mt-3">
                                <button onClick={handlePhotoSubmit} className="btn btn-success btn-sm">Confirmar Foto</button>
                                <button onClick={() => { setSelectedFile(null); setPreviewUrl(null); }} className="btn btn-outline-danger btn-sm ms-2">Cancelar</button>
                            </div>
                        )}
                    </div>

                    {/* Información del usuario */}
                    <ul className="list-group list-group-flush">
                        <li className="list-group-item d-flex justify-content-between align-items-center"><strong>Usuario:</strong> {me.username}</li>
                        <li className="list-group-item d-flex justify-content-between align-items-center"><strong>Email:</strong> {me.email}</li>
                        <li className="list-group-item d-flex justify-content-between align-items-center"><strong>Nombre:</strong> {me.first_name || 'No especificado'}</li>
                        <li className="list-group-item d-flex justify-content-between align-items-center"><strong>Apellido:</strong> {me.last_name || 'No especificado'}</li>
                        <li className="list-group-item d-flex justify-content-between align-items-center"><strong>Nacimiento:</strong> {formatDisplayDate(me.birth_date)}</li>
                        <li className="list-group-item"><strong>Preferencias:</strong><p className="text-muted mb-0">{formatTravelPreferencesDisplay(me.travel_preferences)}</p></li>
                    </ul>

                    {/* Sección de suscripción */}
                    <div className="card shadow-sm mt-4">
                        <div className="card-body">
                            {me.role === 'user' && (
                                <>
                                    <h5 className="card-title">Suscripción: <span className="badge bg-secondary">Estándar</span></h5>
                                    <p className="card-text fw-bold fs-5 text-primary">¡Convertite en Premium!</p>
                                    <p>Disfruta de todos los beneficios de nuestra plataforma:</p>
                                    <ul className="list-unstyled">
                                        <li className="mb-2">
                                            🚀 <strong>Publicá sin límites:</strong> creá publicaciones para otros usuarios sobre actividades y aventuras inigualables.
                                        </li>
                                        <li className="mb-2">
                                            📝 <strong>Dejá tus reseñas:</strong> compartí tus experiencias y ganá puntos por cada opinión.
                                        </li>
                                        <li className="mb-2">
                                            ⭐ <strong>Calificá tus actividades:</strong> puntuá lo que hiciste y acumulá más puntos.
                                        </li>
                                        <li className="mb-2">
                                            🎁 <strong>Accedé a recompensas:</strong> disfrutá beneficios y descuentos increíbles.
                                        </li>
                                        <li className="mb-2">
                                            💰 <strong>Dividí gastos de viajes:</strong> invitá amigos a tus viajes y compartí los gastos automáticamente.
                                        </li>
                                        <li className="mb-2">
                                            💰 <strong>Compartí itinerarios:</strong> compartí itinerarios a amigos vía mail.
                                        </li>
                                    </ul>

                                    <hr />
                                    <div className="d-flex justify-content-between align-items-center">
                                        <span className="fs-4 fw-bold">10 USD / mes</span>
                                        <button className="btn btn-success" onClick={handleSubscribe}>
                                            Convertirse en Premium
                                        </button>
                                    </div>
                                </>
                            )}

                            {me.role === 'premium' && (
                                <>
                                    <h5 className="card-title">Suscripción: <span className="badge bg-success">Premium</span></h5>
                                    <p className="card-text">Estás disfrutando de todos los beneficios de tu cuenta.</p>
                                    <p>Puedes cancelar tu suscripción en cualquier momento.</p>
                                    <hr />
                                    <div className="text-end">
                                        <button className="btn btn-outline-danger" onClick={handleCancelSubscription}>
                                            Cancelar Suscripción
                                        </button>
                                    </div>
                                </>
                            )}

                            {/* Opcional: Para admin u otros roles */}
                            {me.role !== 'user' && me.role !== 'premium' && (
                                <>
                                    <h5 className="card-title">Suscripción: <span className="badge bg-info text-dark">{me.role.charAt(0).toUpperCase() + me.role.slice(1)}</span></h5>
                                    <p className="card-text">Tienes permisos especiales en la plataforma.</p>
                                </>
                            )}
                        </div>
                    </div>
                    {/* Botones de acción */}
                    <div className="d-flex justify-content-end align-items-center mt-4 gap-3">
                        <button className="btn btn-outline-secondary" onClick={() => setViewMode('password')}>
                            Modificar Contraseña
                        </button>
                        <button className="btn btn-outline-custom" onClick={() => setViewMode('edit')}>
                            Editar Perfil
                        </button>
                    </div>
                </div>
            </div>
        </div >
    );
}