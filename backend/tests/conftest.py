import os
import tempfile

# 必须在导入 app 之前设置：测试使用内存 SQLite 和临时上传目录
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="library-test-uploads-")
os.environ["JWT_SECRET"] = "test-secret-for-pytest-only-0123456789abcdef"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["BCRYPT_ROUNDS"] = "4"  # 只为加快测试，生产保持默认 12
os.environ["ADMIN_PASSWORD"] = "admin123"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "secret123"


class Api:
    """测试辅助：封装常用的注册、登录、发布、审核操作。"""

    def __init__(self, client: TestClient):
        self.client = client

    def register(self, username: str, password: str = PASSWORD, confirm: str | None = None, nickname: str = ""):
        return self.client.post(
            "/api/auth/register",
            json={
                "username": username,
                "nickname": nickname or username,
                "password": password,
                "confirm_password": password if confirm is None else confirm,
            },
        )

    def login(self, username: str, password: str = PASSWORD) -> dict:
        resp = self.client.post("/api/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, resp.json()
        return {"Authorization": f"Bearer {resp.json()['data']['token']}"}

    def user(self, username: str) -> dict:
        assert self.register(username).status_code == 200
        return self.login(username)

    def admin(self) -> dict:
        return self.login("admin", "admin123")

    def category_id(self) -> int:
        return self.client.get("/api/categories").json()["data"][0]["id"]

    def book_payload(self, **fields) -> dict:
        payload = {
            "title": "三体",
            "author": "刘慈欣",
            "category_id": self.category_id(),
            "condition": "九成新",
            "description": "科幻小说",
            "cover_url": "",
        }
        payload.update(fields)
        return payload

    def publish(self, headers: dict, **fields) -> int:
        resp = self.client.post("/api/books", json=self.book_payload(**fields), headers=headers)
        assert resp.status_code == 200, resp.json()
        return resp.json()["data"]["id"]

    def publish_available(self, headers: dict, **fields) -> int:
        book_id = self.publish(headers, **fields)
        resp = self.client.post(f"/api/admin/books/{book_id}/approve", headers=self.admin())
        assert resp.status_code == 200, resp.json()
        return book_id

    def book(self, book_id: int, headers: dict | None = None) -> dict:
        return self.client.get(f"/api/books/{book_id}", headers=headers or {}).json()["data"]

    def borrow(self, headers: dict, book_id: int, message: str = ""):
        return self.client.post("/api/borrows", json={"book_id": book_id, "message": message}, headers=headers)

    def apply_return(self, headers: dict, borrow_id: int, message: str = ""):
        return self.client.post("/api/returns", json={"borrow_id": borrow_id, "message": message}, headers=headers)

    def home_ids(self, **params) -> list[int]:
        return [b["id"] for b in self.client.get("/api/books", params=params).json()["data"]["items"]]


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # 进入时触发 lifespan：建表 + 种子数据
        yield c


@pytest.fixture
def api(client) -> Api:
    return Api(client)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session
