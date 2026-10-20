from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile

from app.config import settings
from app.core.deps import get_current_user
from app.core.response import BizError, ok
from app.models import User

router = APIRouter(prefix="/uploads", tags=["上传"])


def _detect_image_type(data: bytes) -> str | None:
    # 按文件头判断真实类型，不信任客户端传来的文件名和 Content-Type
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("/cover")
async def upload_cover(file: UploadFile, _: User = Depends(get_current_user)):
    data = await file.read(settings.max_upload_bytes + 1)
    if not data:
        raise BizError("文件为空")
    if len(data) > settings.max_upload_bytes:
        raise BizError(f"图片不能超过 {settings.max_upload_bytes // 1024 // 1024}MB")
    ext = _detect_image_type(data)
    if ext is None:
        raise BizError("仅支持 JPG、PNG、WEBP 格式的图片")
    name = f"{uuid4().hex}.{ext}"
    target = Path(settings.upload_dir) / "covers"
    target.mkdir(parents=True, exist_ok=True)
    (target / name).write_bytes(data)
    return ok({"url": f"/uploads/covers/{name}"}, "上传成功")
