import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import BizError

logger = logging.getLogger(__name__)

FIELD_LABELS = {
    "username": "用户名",
    "nickname": "昵称",
    "password": "密码",
    "confirm_password": "确认密码",
    "title": "书名",
    "author": "作者",
    "category_id": "图书分类",
    "condition": "新旧程度",
    "description": "图书简介",
    "cover_url": "封面图片",
    "content": "评论内容",
    "message": "留言",
    "name": "分类名称",
    "note": "驳回原因",
    "status": "状态",
    "book_id": "图书",
    "borrow_id": "借阅记录",
    "file": "文件",
    "page": "页码",
    "size": "每页条数",
}

HTTP_MESSAGES = {
    401: "请先登录",
    403: "无权访问",
    404: "资源不存在",
    405: "请求方法不允许",
}


def _fail(code: int, msg: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"code": code, "msg": msg, "data": None})


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "参数错误"
    err = errors[0]
    field = next((str(x) for x in reversed(err.get("loc", ())) if isinstance(x, str)), "")
    label = FIELD_LABELS.get(field, field or "参数")
    ctx = err.get("ctx") or {}
    match err.get("type"):
        case "missing":
            return f"{label}不能为空"
        case "string_too_short":
            if ctx.get("min_length") == 1:
                return f"{label}不能为空"
            return f"{label}长度不能少于 {ctx.get('min_length')} 个字符"
        case "string_too_long":
            return f"{label}长度不能超过 {ctx.get('max_length')} 个字符"
        case "string_pattern_mismatch":
            return f"{label}格式不正确"
        case "literal_error" | "enum":
            return f"{label}取值不合法"
        case "int_parsing" | "int_type":
            return f"{label}必须是整数"
        case "greater_than_equal" | "less_than_equal":
            return f"{label}超出允许范围"
        case "json_invalid":
            return "请求体不是合法的 JSON"
    return f"{label}：{err.get('msg', '参数错误')}"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizError)
    async def handle_biz_error(_: Request, exc: BizError):
        return _fail(exc.code, exc.msg)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException):
        msg = HTTP_MESSAGES.get(exc.status_code)
        if msg is None:
            msg = exc.detail if isinstance(exc.detail, str) else "请求错误"
        return _fail(exc.status_code, msg)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        return _fail(400, _validation_message(exc))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        logger.exception("unhandled error", exc_info=exc)
        return _fail(500, "服务器内部错误")
