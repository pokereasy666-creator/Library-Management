from tests.conftest import PASSWORD


def test_register_login_and_me(api, client):
    resp = api.register("alice", nickname="爱丽丝")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200 and body["msg"] == "注册成功"
    assert body["data"]["role"] == "USER"
    assert "password_hash" not in body["data"]

    headers = api.login("alice")
    me = client.get("/api/users/me", headers=headers).json()["data"]
    assert me["username"] == "alice" and me["nickname"] == "爱丽丝"


def test_register_rejects_duplicate_username(api):
    api.register("alice")
    resp = api.register("alice")
    assert resp.status_code == 400
    assert resp.json()["msg"] == "用户名已存在"


def test_register_rejects_password_mismatch(api):
    resp = api.register("alice", password="secret123", confirm="secret456")
    assert resp.status_code == 400
    assert resp.json()["msg"] == "两次输入的密码不一致"


def test_register_validation_message_is_readable(api):
    resp = api.register("alice", password="123")
    assert resp.status_code == 400
    assert resp.json() == {"code": 400, "msg": "密码长度不能少于 6 个字符", "data": None}

    resp = api.register("a!", password=PASSWORD)
    assert resp.status_code == 400
    assert resp.json()["msg"].startswith("用户名")


def test_password_is_stored_hashed(api, db):
    from app.models import User

    api.register("alice")
    user = db.query(User).filter_by(username="alice").one()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$2")


def test_login_with_wrong_password(api, client):
    api.register("alice")
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "wrong-pass"})
    assert resp.status_code == 400
    assert resp.json()["msg"] == "用户名或密码错误"

    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong-pass"})
    assert resp.json()["msg"] == "用户名或密码错误"


def test_disabled_user_cannot_login_and_old_token_is_revoked(api, client):
    headers = api.user("alice")
    alice_id = client.get("/api/users/me", headers=headers).json()["data"]["id"]

    resp = client.put(f"/api/admin/users/{alice_id}/status", json={"status": "DISABLED"}, headers=api.admin())
    assert resp.status_code == 200

    resp = client.get("/api/users/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["msg"] == "账号已被禁用，请联系管理员"

    resp = client.post("/api/auth/login", json={"username": "alice", "password": PASSWORD})
    assert resp.status_code == 403

    client.put(f"/api/admin/users/{alice_id}/status", json={"status": "ACTIVE"}, headers=api.admin())
    assert client.get("/api/users/me", headers=headers).status_code == 200


def test_invalid_token_is_rejected(client):
    resp = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
    assert resp.json()["msg"] == "登录已失效，请重新登录"
