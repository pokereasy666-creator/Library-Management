from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginate(db: Session, model, conditions, order_by, page: int, size: int) -> dict:
    total = db.scalar(select(func.count()).select_from(model).where(*conditions))
    stmt = select(model).where(*conditions).order_by(*order_by).offset((page - 1) * size).limit(size)
    items = db.scalars(stmt).unique().all()
    return {"total": total, "items": items}
