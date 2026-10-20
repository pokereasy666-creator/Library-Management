from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import BOOK_CONDITIONS


def Text(min_length: int, max_length: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)]


# 封面只能使用本系统上传接口返回的地址，防止填入任意外链
COVER_URL_PATTERN = r"^(/uploads/covers/[0-9a-f]{32}\.(jpg|png|webp))?$"


class OutModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- 用户 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    nickname: Text(1, 32)
    password: str = Field(min_length=6, max_length=32, pattern=r"^\S+$")
    confirm_password: str = Field(min_length=1, max_length=32)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)


class UserOut(OutModel):
    id: int
    username: str
    nickname: str
    role: str
    status: str
    created_at: datetime


class UserBrief(OutModel):
    id: int
    username: str
    nickname: str


class UserStatusIn(BaseModel):
    status: Literal["ACTIVE", "DISABLED"]


# ---------- 分类 ----------
class CategoryIn(BaseModel):
    name: Text(1, 32)


class CategoryOut(OutModel):
    id: int
    name: str


# ---------- 图书 ----------
class BookIn(BaseModel):
    title: Text(1, 100)
    author: Text(1, 50)
    category_id: int
    condition: Literal[BOOK_CONDITIONS]
    description: Text(0, 2000) = ""
    cover_url: str = Field("", pattern=COVER_URL_PATTERN)


class BookOut(OutModel):
    id: int
    title: str
    author: str
    category_id: int
    category_name: str
    condition: str
    description: str
    cover_url: str
    status: str
    review_note: str
    owner: UserBrief
    created_at: datetime
    updated_at: datetime


class BookBrief(OutModel):
    id: int
    title: str
    author: str
    cover_url: str
    status: str
    is_deleted: bool


class RejectIn(BaseModel):
    note: Text(0, 255) = ""


# ---------- 评论 ----------
class CommentIn(BaseModel):
    content: Text(1, 500)


class CommentOut(OutModel):
    id: int
    content: str
    user: UserBrief
    created_at: datetime


# ---------- 借阅 / 归还 ----------
class BorrowIn(BaseModel):
    book_id: int
    message: Text(0, 255) = ""


class ReturnIn(BaseModel):
    borrow_id: int
    message: Text(0, 255) = ""


class ReturnBrief(OutModel):
    id: int
    message: str
    status: str
    created_at: datetime
    handled_at: datetime | None


class BorrowOut(OutModel):
    id: int
    book: BookBrief
    borrower: UserBrief
    owner: UserBrief
    message: str
    status: str
    created_at: datetime
    handled_at: datetime | None
    returns: list[ReturnBrief]


class ReturnOut(OutModel):
    id: int
    borrow_id: int
    book: BookBrief
    borrower: UserBrief
    owner: UserBrief
    message: str
    status: str
    created_at: datetime
    handled_at: datetime | None


def page_of(result: dict, schema: type[OutModel]) -> dict:
    return {"total": result["total"], "items": [schema.model_validate(x) for x in result["items"]]}
