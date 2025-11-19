import React, { useState } from 'react';
import { api } from '../api';

const SECURITY_QUESTIONS = [
    "¿Cuál es el nombre de tu primera mascota?",
    "¿Cuál es el apellido de tu madre?",
    "¿En qué ciudad naciste?",
    "¿Cuál es el nombre de tu escuela primaria?",
    "¿Cuál es tu comida favorita?"
];

export default function Register({ setView }) {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirm_password: '',
        security_question_1: SECURITY_QUESTIONS[0],
        security_answer_1: '',
        security_question_2: SECURITY_QUESTIONS[1],
        security_answer_2: ''
    });
    const [error, setError] = useState('');
    const [registrationSuccess, setRegistrationSuccess] = useState(false);

    function handleChange(e) {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    }

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');

        const { password, confirm_password, ...payload } = formData;

        if (password !== confirm_password) {
            setError('Las contraseñas no coinciden.');
            return;
        }
        if (password.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres.');
            return;
        }
        if (payload.security_question_1 === payload.security_question_2) {
            setError('Las preguntas de seguridad deben ser diferentes.');
            return;
        }
        if (!payload.security_answer_1 || !payload.security_answer_2) {
            setError('Debes responder ambas preguntas de seguridad.');
            return;
        }

        try {
            await api('/api/auth/register', { method: 'POST', body: { ...payload, password } });
            setRegistrationSuccess(true);
        } catch (err) {
            setError(err.detail || 'Error en el registro.');
        }
    }

    const available_q2 = SECURITY_QUESTIONS.filter(q => q !== formData.security_question_1);
    const available_q1 = SECURITY_QUESTIONS.filter(q => q !== formData.security_question_2);

    //Si el registro fue exitoso, muestra el mensaje de confirmación
    if (registrationSuccess) {
        return (
            <div className="text-center">
                <h3 className="mb-3">✅ ¡Registro exitoso!</h3>
                <p>Tu cuenta se ha creado correctamente. Ahora puedes iniciar sesión.</p>
                <button
                    onClick={() => setView('login')}
                    className="btn btn-primary w-100 mt-2"
                >
                    Ir a Iniciar Sesión
                </button>
            </div>
        );
    }

    //caso registro no exitoso, sigue mostrando el formulario
    return (
        <form onSubmit={handleSubmit}>
            <h3 className="mb-4">Crear cuenta</h3>

            <div className="mb-3">
                <label>Email</label>
                <input type="email" name="email" className="form-control" onChange={handleChange} required />
            </div>
            <div className="mb-3">
                <label>Nombre de usuario</label>
                <input type="text" name="username" className="form-control" onChange={handleChange} required />
            </div>
            <div className="mb-3">
                <label>Contraseña (mín. 8 caracteres)</label>
                <input type="password" name="password" className="form-control" onChange={handleChange} required />
            </div>
            <div className="mb-3">
                <label>Confirmar Contraseña</label>
                <input type="password" name="confirm_password" className="form-control" onChange={handleChange} required />
            </div>

            <hr className="my-4" />
            <h5 className="mb-3">Preguntas de Seguridad</h5>

            <div className="mb-3">
                <label>Pregunta 1</label>
                <select name="security_question_1" className="form-select" value={formData.security_question_1} onChange={handleChange}>
                    {available_q1.map(q => <option key={q} value={q}>{q}</option>)}
                </select>
            </div>
            <div className="mb-3">
                <label>Respuesta 1</label>
                <input type="text" name="security_answer_1" className="form-control" onChange={handleChange} required />
            </div>
            <div className="mb-3">
                <label>Pregunta 2</label>
                <select name="security_question_2" className="form-select" value={formData.security_question_2} onChange={handleChange}>
                    {available_q2.map(q => <option key={q} value={q}>{q}</option>)}
                </select>
            </div>
            <div className="mb-3">
                <label>Respuesta 2</label>
                <input type="text" name="security_answer_2" className="form-control" onChange={handleChange} required />
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <button type="submit" className="btn btn-primary w-100 mt-3">
                Registrarse
            </button>
        </form>
    );
}