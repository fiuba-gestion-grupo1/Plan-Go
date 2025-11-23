from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any
from ..db import get_db
from ..models import Review, ReviewReport, User, PublicationPhoto
from .. import models
from .auth import get_current_user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "admin" and current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.get("/reports/pending")
async def get_pending_review_reports(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin)
):
    """Obtener reportes de reseñas pendientes (solo admin)"""
    reports = db.query(ReviewReport).filter(
        ReviewReport.status == "pending"
    ).all()
    
    result = []
    for report in reports:
        review = db.query(Review).filter(Review.id == report.review_id).first()
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        photos_data = []
        if review and review.publication:
            photos = db.query(PublicationPhoto).filter(
                PublicationPhoto.publication_id == review.publication.id
            ).order_by(PublicationPhoto.index_order).all()
            photos_data = [photo.url for photo in photos]
        
        report_data = {
            "id": report.id,
            "review_id": report.review_id,
            "reporter_username": reporter.username if reporter else "Unknown",
            "reason": report.reason,
            "comments": report.comments,
            "status": report.status,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None,
            "resolved_at": report.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if report.resolved_at else None,
            "review": {
                "id": review.id if review else None,
                "rating": review.rating if review else 0,
                "comment": review.comment if review else "",
                "author_username": review.author.username if review and review.author else "Unknown",
                "status": review.status if review else "unknown",
                "created_at": review.created_at.strftime("%Y-%m-%d %H:%M:%S") if review and review.created_at else None
            } if review else None,
            "publication": {
                "id": review.publication.id if review and review.publication else None,
                "place_name": review.publication.place_name if review and review.publication else "Unknown",
                "title": review.publication.place_name if review and review.publication else "Unknown",
                "address": review.publication.address if review and review.publication else "",
                "city": review.publication.city if review and review.publication else "",
                "province": review.publication.province if review and review.publication else "",
                "country": review.publication.country if review and review.publication else "",
                "rating_avg": review.publication.rating_avg if review and review.publication else 0.0,
                "rating_count": review.publication.rating_count if review and review.publication else 0,
                "cost_per_day": review.publication.cost_per_day if review and review.publication else 0.0,
                "categories": [cat.name for cat in review.publication.categories] if review and review.publication and review.publication.categories else [],
                "photos": photos_data
            } if review and review.publication else None
        }
        
        result.append(report_data)
    
    return result

@router.put("/reports/{report_id}/approve")
async def approve_review_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin)
):
    """Aprobar un reporte (ocultar la reseña)"""
    report = db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    review = db.query(Review).filter(Review.id == report.review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    report.status = "approved"
    review.status = "hidden"
    
    db.commit()
    
    return {"message": "Review hidden successfully"}

@router.put("/reports/{report_id}/reject")
async def reject_review_report(
    report_id: int,
    reject_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin)
):
    """Rechazar un reporte (mantener la reseña visible)"""
    report = db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    review = db.query(Review).filter(Review.id == report.review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    report.status = "rejected"
    report.rejection_reason = reject_data.get("reason", "") if reject_data else ""
    review.status = "approved"
    
    db.commit()
    
    return {"message": "Report rejected successfully"}
