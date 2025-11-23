from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user
from .. import models, schemas

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("", response_model=schemas.ExpenseOut)
def create_expense(
    payload: schemas.ExpenseIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expense = models.Expense(
        user_id=user.id,
        trip_name=payload.trip_name,
        name=payload.name,
        category=payload.category,
        amount=payload.amount,
        date=payload.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return schemas.ExpenseOut.model_validate(expense.__dict__)


@router.get("", response_model=list[schemas.ExpenseOut])
def get_my_expenses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    expenses = db.query(models.Expense).filter_by(user_id=user.id).all()
    return [schemas.ExpenseOut.model_validate(e.__dict__) for e in expenses]


@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    payload: schemas.ExpenseIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    expense = db.query(models.Expense).filter_by(id=expense_id, user_id=user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(expense, k, v)

    db.commit()
    db.refresh(expense)
    return schemas.ExpenseOut.model_validate(expense.__dict__)


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    expense = db.query(models.Expense).filter_by(id=expense_id, user_id=user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
