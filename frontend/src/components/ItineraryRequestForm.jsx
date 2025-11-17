import React, { useState } from 'react';

export default function ItineraryRequestForm({ onSubmit, isLoading = false }) {
    const [destination, setDestination] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [budget, setBudget] = useState('');
    const [cantPersons, setCantPersons] = useState('');
    const [tripType, setTripType] = useState('');
    const [arrivalTime, setArrivalTime] = useState('');
    const [departureTime, setDepartureTime] = useState('');
    const [comments, setComments] = useState('');
    const [error, setError] = useState('');

    const tripTypes = [
        'Romántico',
        'Gastronómico',
        'Laboral',
        'Relajación',
        'Aventurero',
        'Cultural',
        'Familiar',
        'Deportivo', 
        'Compras',
        'No especificado'
    ];

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');

        // Validaciones básicas
        if (!destination || !startDate || !endDate || !budget || !tripType || !cantPersons) {
            setError('Por favor completa todos los campos obligatorios');
            return;
        }

        if (new Date(endDate) < new Date(startDate)) {
            setError('La fecha de fin debe ser posterior a la fecha de inicio');
            return;
        }

        if (parseInt(budget) <= 0) {
            setError('El presupuesto debe ser mayor a 0');
            return;
        }

        if (parseInt(cantPersons) <= 0) {
            setError('La cantidad de personas debe ser mayor a 0');
            return;
        }


        try {
            // Asegurar que las fechas estén en formato correcto (YYYY-MM-DD) sin problemas de zona horaria
            const formatDate = (dateStr) => {
                if (!dateStr) return null;
                const date = new Date(dateStr + 'T00:00:00'); // Forzar medianoche local
                return date.toISOString().split('T')[0];
            };

            const payload = {
                destination,
                start_date: formatDate(startDate),
                end_date: formatDate(endDate),
                budget: parseInt(budget),
                cant_persons: parseInt(cantPersons),
                trip_type: tripType,
                arrival_time: arrivalTime || null,
                departure_time: departureTime || null,
                comments: comments.trim() || null
            };

            await onSubmit(payload);
        } catch (e) {
            setError(e.message || 'Error al solicitar el itinerario');
        }
    }

    return (
        <form onSubmit={handleSubmit} className="border rounded-3 p-3 bg-white shadow-sm">
            {error && (
                <div className="alert alert-danger" role="alert">
                    {error}
                </div>
            )}

            <div className="mb-3">
                <label htmlFor="destination" className="form-label">
                    Destino <span className="text-danger">*</span>
                </label>
                <input
                    id="destination"
                    type="text"
                    className="form-control"
                    placeholder="Ej: Río de Janeiro, Brasil"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    required
                    disabled={isLoading}
                />
                <small className="form-text text-muted">
                    Ingresa el destino completo (ciudad, país)
                </small>
            </div>

            <div className="row">
                <div className="col-md-6 mb-3">
                    <label htmlFor="startDate" className="form-label">
                        Fecha de inicio <span className="text-danger">*</span>
                    </label>
                    <input
                        id="startDate"
                        type="date"
                        className="form-control"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        required
                        disabled={isLoading}
                    />
                </div>

                <div className="col-md-6 mb-3">
                    <label htmlFor="endDate" className="form-label">
                        Fecha de fin <span className="text-danger">*</span>
                    </label>
                    <input
                        id="endDate"
                        type="date"
                        className="form-control"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        required
                        disabled={isLoading}
                    />
                </div>
            </div>

            <div className="mb-3">
                <label htmlFor="budget" className="form-label">
                    Presupuesto estimado (USD) <span className="text-danger">*</span>
                </label>
                <input
                    id="budget"
                    type="number"
                    className="form-control"
                    placeholder="Ej: 1500"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    min="1"
                    required
                    disabled={isLoading}
                />
            </div>

            <div className="mb-3">
                <label htmlFor="cantPersons" className="form-label">
                    Cantidad de personas <span className="text-danger">*</span>
                </label>
                <input
                    id="cantPersons"
                    type="number"
                    className="form-control"
                    placeholder="Ingresa la cantidad de personas que viajarán"
                    value={cantPersons}
                    onChange={(e) => setCantPersons(e.target.value)}
                    min="1"
                    required
                    disabled={isLoading}
                />
            </div>

            <div className="mb-3">
                <label htmlFor="tripType" className="form-label">
                    Tipo de viaje <span className="text-danger">*</span>
                </label>
                <select
                    id="tripType"
                    className="form-select"
                    value={tripType}
                    onChange={(e) => setTripType(e.target.value)}
                    required
                    disabled={isLoading}
                >
                    <option value="">Selecciona un tipo</option>
                    {tripTypes.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>
            </div>

            <div className="row">
                <div className="col-md-6 mb-3">
                    <label htmlFor="arrivalTime" className="form-label">
                        Hora estimada de llegada (opcional)
                    </label>
                    <input
                        id="arrivalTime"
                        type="time"
                        className="form-control"
                        value={arrivalTime}
                        onChange={(e) => setArrivalTime(e.target.value)}
                        disabled={isLoading}
                    />
                </div>

                <div className="col-md-6 mb-3">
                    <label htmlFor="departureTime" className="form-label">
                        Hora estimada de salida (opcional)
                    </label>
                    <input
                        id="departureTime"
                        type="time"
                        className="form-control"
                        value={departureTime}
                        onChange={(e) => setDepartureTime(e.target.value)}
                        disabled={isLoading}
                    />
                </div>
            </div>

            <div className="mb-3">
                <label htmlFor="comments" className="form-label">
                    Comentarios (opcional)
                </label>
                <textarea
                    id="comments"
                    className="form-control"
                    placeholder="Ej: No quiero ir a lugares muy concurridos, prefiero actividades al aire libre, etc."
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    rows="3"
                    maxLength="500"
                    disabled={isLoading}
                />
                <small className="form-text text-muted">
                    Agrega cualquier comentario o preferencia especial para personalizar tu itinerario (máximo 500 caracteres)
                </small>
            </div>

            <div className="alert alert-info" role="alert">
                <strong>Nota:</strong> El itinerario se generará considerando tus preferencias de viaje 
                configuradas en tu perfil. Asegúrate de haberlas completado para obtener mejores resultados.
                ESTO PUEDE TARDAR UN MOMENTO, NO CIERRES LA PÁGINA HASTA QUE SE COMPLETE.
            </div>

            <button 
                type="submit" 
                className="btn btn-primary w-100"
                disabled={isLoading}
            >
                {isLoading ? (
                    <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Generando itinerario...
                    </>
                ) : (
                    'Solicitar Itinerario'
                )}
            </button>
        </form>
    );
}