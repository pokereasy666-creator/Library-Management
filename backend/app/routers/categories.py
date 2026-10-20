from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.models import Category
from app.schemas import CategoryOut

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    categories = db.scalars(select(Category).order_by(Category.id)).all()
    return ok([CategoryOut.model_validate(c) for c in categories])
