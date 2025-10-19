import React from 'react';

export default function Profile({ me }) {
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

    return (
        <div className="container mt-4" style={{ maxWidth: '600px' }}>
            <div className="card shadow-sm">
                <div className="card-body p-4 text-center"> 
                    
                    <div style={photoPlaceholderStyle}>
                        <span>Foto</span>
                    </div>
                    
                    <h2 className="card-title mb-4">Mi Perfil</h2>
                    
                    <p className="fs-5">
                        <strong>Nombre de usuario:</strong> {me.username}
                    </p>
                    <p className="fs-5">
                        <strong>Email:</strong> {me.email || 'No especificado'}
                    </p>
                    
                    <button className="btn btn-primary mt-3">Editar Perfil (Próximamente)</button>
                </div>
            </div>
        </div>
    );
}