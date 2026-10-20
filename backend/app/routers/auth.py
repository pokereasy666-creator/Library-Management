from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.response import BizError, ok
from app.core.security import create_token, hash_password, verify_password
from app.database import get_db
from app.models import Role, User, UserStatus
from app.schemas import LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.password != data.confirm_password:
        raise BizError("两次输入的密码不一致")
    if db.scalar(select(User.id).where(User.username == data.username)) is not None:
        raise BizError("用户名已存在")
    user = User(
        username=data.username,
        nickname=data.nickname,
        password_hash=hash_password(data.password),
        role=Role.USER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError("用户名已存在")
    return ok(UserOut.model_validate(user), "注册成功")


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise BizError("用户名或密码错误")
    if user.status == UserStatus.DISABLED:
        raise BizError("账号已被禁用，请联系管理员", 403)
    token = create_token(user.id, user.role)
    return ok({"token": token, "user": UserOut.model_validate(user)}, "登录成功")
