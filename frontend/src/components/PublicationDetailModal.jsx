import React, { useState, useEffect } from 'react';
// Importamos nuestros helpers centralizados
import { request } from '../utils/api'; // Ajusta la ruta si es necesario
import { Stars, RatingBadge } from './shared/UIComponents'; // Ajusta la ruta si es necesario

export default function PublicationDetailModal({ open, pub, onClose, onToggleFavorite, me, token }) {
    if (!open || !pub) return null;

    const [isFav, setIsFav] = useState(pub.is_favorite || false);
    useEffect(() => { setIsFav(pub.is_favorite || false); }, [pub?.id, pub?.is_favorite]);

    // --- logica de reseñas---
    const [list, setList] = useState([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");
    const [rating, setRating] = useState(5);
    const [comment, setComment] = useState("");

    const [commentInputs, setCommentInputs] = useState({});
    const isLoggedIn = token;

    const isPremium = me?.role === "premium" || me?.username === "admin";

    // Efecto para cargar reseñas
    useEffect(() => {
        if (!open || !pub?.id) {
            setList([]);
            setErr("");
            return;
        }
        let cancel = false;
        (async () => {
            setLoading(true);
            setErr("");
            try {
                const rows = await request(`/api/publications/${pub.id}/reviews`, { token });
                if (!cancel) setList(rows);
            } catch (e) {
                if (!cancel) setErr(e.message);
            } finally {
                if (!cancel) setLoading(false);
            }
        })();
        return () => { cancel = true; };
    }, [open, pub?.id, token]);

    // Función para enviar reseña
    async function submitReview(e) {
        e.preventDefault();
        if (!isPremium) { return; }
        if (!token) { alert("Iniciá sesión para publicar una reseña."); return; }
        try {
            await request(`/api/publications/${pub.id}/reviews`, {
                method: "POST",
                token,
                body: { rating: Number(rating), comment: comment || undefined }
            });
            setComment(""); setRating(5);
            const rows = await request(`/api/publications/${pub.id}/reviews`, { token });
            setList(rows);
        } catch (e) {
            alert(`Error creando reseña: ${e.message}`);
        }
    }

    //FUNCION LIKE REVIEW
    async function handleLikeReview(reviewId) {
        if (!isPremium) {
            alert("Solo los usuarios premium pueden dar me gusta a las reseñas.");
            return;
        }
        const originalList = list;
        setList(prevList => prevList.map(r =>
            r.id === reviewId
                ? {
                    ...r,
                    is_liked_by_me: !r.is_liked_by_me,
                    like_count: r.is_liked_by_me ? r.like_count - 1 : r.like_count + 1
                }
                : r
        ));

        try {
            const data = await request(`/api/publications/reviews/${reviewId}/like`, {
                method: "POST",
                token,
            });
            setList(prevList => prevList.map(r =>
                r.id === reviewId
                    ? { ...r, is_liked_by_me: data.is_liked, like_count: data.like_count }
                    : r
            ));
        } catch (e) {
            alert('Error al dar me gusta: ' + (e.message || 'Error desconocido'));
            setList(originalList);
        }
    }

    //FUNCION COMENTAR RESEÑA
    async function submitComment(e, reviewId) {
        e.preventDefault();
        const commentText = commentInputs[reviewId];
        if (!commentText || !commentText.trim()) return;
        if (!token) {
            alert("Debes iniciar sesión para comentar.");
            return;
        }

        try {
            const newComment = await request(`/api/publications/reviews/${reviewId}/comments`, {
                method: "POST",
                token,
                body: { comment: commentText }
            });
            setList(prevList =>
                prevList.map(review =>
                    review.id === reviewId
                        ? { ...review, comments: [...(review.comments || []), newComment] }
                        : review
                )
            );
            setCommentInputs(prev => ({ ...prev, [reviewId]: "" }));
        } catch (err) {
            alert("Error al publicar el comentario: " + (err?.message || "Error"));
        }
    }

    //FUNCION TOGGLE FAVORITE
    async function handleToggleFavorite(e) {
        if (e && e.stopPropagation) e.stopPropagation();
        const prev = isFav;
        setIsFav(!prev);
        try {
            if (onToggleFavorite) await onToggleFavorite(pub.id);
        } catch (err) {
            setIsFav(prev);
            alert('Error actualizando favoritos: ' + (err?.message || err));
        }
    }

    return (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
            style={{ background: "rgba(0,0,0,.4)", zIndex: 1050 }}>
            <div className="bg-white rounded-3 shadow-lg border" style={{ maxWidth: 600, maxHeight: "90vh", width: "90%" }}>

                {/* Header con botón cerrar */}
                <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">{pub.place_name}</h5>
                    <button className="btn-close" onClick={onClose}></button>
                </div>

                {/* Contenido scrolleable */}
                <div className="p-3" style={{ overflowY: "auto", maxHeight: "calc(90vh - 70px)" }}>

                    {/* Carrusel de imágenes */}
                    <div className="mb-3">
                        {pub.photos?.length > 0 ? (
                            <div id={`carousel-${pub.id}`} className="carousel slide" data-bs-ride="carousel">
                                <div className="carousel-inner">
                                    {pub.photos.map((img, i) => (
                                        <div key={i} className={`carousel-item ${i === 0 ? 'active' : ''}`}>
                                            <img src={img} className="d-block w-100 rounded" alt={`Imagen ${i + 1}`}
                                                style={{ height: "300px", objectFit: "cover" }} />
                                        </div>
                                    ))}
                                </div>
                                {pub.photos.length > 1 && (
                                    <>
                                        <button className="carousel-control-prev" type="button"
                                            data-bs-target={`#carousel-${pub.id}`} data-bs-slide="prev">
                                            <span className="carousel-control-prev-icon"></span>
                                        </button>
                                        <button className="carousel-control-next" type="button"
                                            data-bs-target={`#carousel-${pub.id}`} data-bs-slide="next">
                                            <span className="carousel-control-next-icon"></span>
                                        </button>
                                    </>
                                )}
                            </div>
                        ) : (
                            <div className="text-muted text-center p-4">Sin imágenes disponibles</div>
                        )}
                    </div>

                    {/* Información principal */}
                    <div className="mb-3">
                        <div className="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <RatingBadge avg={pub.rating_avg} count={pub.rating_count} />
                            </div>
                            <button
                                className={`btn ${isFav ? 'btn-danger' : 'btn-outline-danger'}`}
                                onClick={handleToggleFavorite}
                                title={isFav ? 'Quitar de favoritos' : 'Agregar a favoritos'}
                            >
                                {isFav ? '❤️ Favorito' : '🤍 Agregar a favoritos'}
                            </button>
                        </div>

                        {pub.description && (
                            <>
                                <h6 className="mt-3 mb-2">Descripción</h6>
                                <p className="mb-2" style={{ whiteSpace: "pre-wrap" }}>{pub.description}</p>
                            </>
                        )}

                        <h6 className="mt-3 mb-2">Categorías</h6>
                        <div className="d-flex flex-wrap gap-1 mb-3">
                            {pub.categories?.map(cat => (
                                <span key={cat} className="badge bg-secondary-subtle text-secondary border text-capitalize">
                                    {cat}
                                </span>
                            ))}
                        </div>

                        <h6 className="mt-3 mb-2">Ubicación</h6>
                        <p className="mb-2">
                            📍 {pub.address}, {pub.city}, {pub.province}
                        </p>

                        <h6 className="mt-3 mb-2">Precio</h6>
                        <p className="mb-2">
                            ${pub.cost_per_day} por día
                        </p>
                        <hr />
                        <h6 className="mt-3 mb-2">Reseñas</h6>

                        {/* Lista de reseñas */}
                        <div style={{ maxHeight: 250, overflow: "auto" }}>
                            {loading && <div className="text-muted">Cargando…</div>}
                            {err && <div className="alert alert-danger">{err}</div>}
                            {!loading && !err && list.length === 0 && <div className="text-muted">Sin reseñas todavía.</div>}
                            <ul className="list-unstyled mb-0">
                                {list.map((r) => (
                                    <li key={r.id} className="border rounded-3 p-3 mb-2">
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div className="d-flex align-items-center gap-3">
                                                <Stars value={r.rating} />
                                                <button
                                                    className={`btn btn-sm ${r.is_liked_by_me ? 'btn-danger' : 'btn-outline-danger'} ${!isPremium ? 'disabled' : ''}`}
                                                    onClick={() => handleLikeReview(r.id)}
                                                    disabled={!isPremium}
                                                    title={isPremium ? (r.is_liked_by_me ? "Quitar me gusta" : "Dar me gusta") : "Solo usuarios premium pueden dar me gusta"}
                                                    style={{ padding: '0.1rem 0.4rem' }}
                                                >
                                                    {r.is_liked_by_me ? '❤️' : '🤍'} {r.like_count}
                                                </button>
                                            </div>
                                            <small className="text-muted">{new Date(r.created_at).toLocaleString()}</small>
                                        </div>
                                        {r.comment && <div className="mt-1">{r.comment}</div>}
                                        <small className="text-muted d-block mt-1">por {r.author_username}</small>

                                        {/* Bloque de comentarios de la reseña */}
                                        <div className="mt-3 ps-3" style={{ borderLeft: '3px solid #eee' }}>
                                            {r.comments && r.comments.length > 0 && (
                                                <ul className="list-unstyled mb-2">
                                                    {r.comments.map(c => (
                                                        <li key={c.id} className="mb-2">
                                                            <div className="d-flex justify-content-between align-items-center">
                                                                <strong className="small">{c.author_username}</strong>
                                                                <small className="text-muted" style={{ fontSize: '0.75em' }}>
                                                                    {new Date(c.created_at).toLocaleString()}
                                                                </small>
                                                            </div>
                                                            <p className="mb-0 small" style={{ whiteSpace: 'pre-wrap' }}>{c.comment}</p>
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}

                                            {isLoggedIn && (
                                                <form onSubmit={(e) => submitComment(e, r.id)} className="d-flex gap-2">
                                                    <input
                                                        type="text"
                                                        className="form-control form-control-sm"
                                                        placeholder="Escribe una respuesta..."
                                                        value={commentInputs[r.id] || ""}
                                                        onChange={(e) => setCommentInputs(prev => ({ ...prev, [r.id]: e.target.value }))}
                                                    />
                                                    <button
                                                        className="btn btn-sm btn-celeste"
                                                        type="submit"
                                                        disabled={!commentInputs[r.id] || !commentInputs[r.id].trim()}
                                                    >
                                                        Enviar
                                                    </button>
                                                </form>
                                            )}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Formulario para nueva reseña */}
                        {isPremium ? (
                            <form className="p-3 border-top" onSubmit={submitReview}>
                                <div className="row g-2">
                                    <div className="col-12 col-md-2">
                                        <label className="form-label mb-1">Rating</label>
                                        <select className="form-select" value={rating} onChange={(e) => setRating(e.target.value)}>
                                            {[5, 4, 3, 2, 1].map(v => <option key={v} value={v}>{v}</option>)}
                                        </select>
                                    </div>
                                    <div className="col-12 col-md-8">
                                        <label className="form-label mb-1">Comentario (opcional)</label>
                                        <input className="form-control" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Contanos tu experiencia" />
                                    </div>
                                    <div className="col-12 col-md-2 d-flex align-items-end">
                                        <button className="btn btn-celeste w-100" type="submit">Publicar</button>
                                    </div>
                                </div>
                            </form>
                        ) : (
                            <div className="p-3 border-top">
                                <div className="alert alert-secondary mb-0">
                                    Solo los <strong>usuarios premium</strong> pueden publicar reseñas.
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}