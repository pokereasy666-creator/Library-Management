from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.response import BizError
from app.core.security import decode_token
from app.database import get_db
from app.models import Role, User, UserStatus

bearer = HTTPBearer(auto_error=False)


def _load_user(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User:
    if credentials is None:
        raise BizError("请先登录", 401)
    user_id = decode_token(credentials.credentials)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise BizError("登录已失效，请重新登录", 401)
    # JWT 本身无状态，每次请求查库确认账号状态，禁用后旧 token 立即失效
    if user.status == UserStatus.DISABLED:
        raise BizError("账号已被禁用，请联系管理员", 401)
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    return _load_user(credentials, db)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """公开接口使用：带了有效 token 就识别身份，否则按游客处理。"""
    try:
        return _load_user(credentials, db)
    except BizError:
        return None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise BizError("无管理员权限", 403)
    return user
