import React from 'react';

export default function Home({ me }) {
    return (
        <div className="container mt-4">
            <div className="p-5 mb-4 bg-light rounded-3">
                <div className="container-fluid py-5">
                    <h1 className="display-5 fw-bold">¡Bienvenido a Plan&Go, {me.username}!</h1>
                    <p className="col-md-8 fs-4">
                        Empieza a planificar nuevas aventuras! Utiliza el menú de navegación para explorar tu perfil.
                    </p>
                </div>
            </div>
        </div>
    );
}