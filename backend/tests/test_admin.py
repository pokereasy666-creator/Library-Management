def test_user_management(api, client):
    api.user("alice")
    admin = api.admin()
    users = client.get("/api/admin/users", headers=admin).json()["data"]
    assert users["total"] == 2
    assert {u["username"] for u in users["items"]} == {"admin", "alice"}

    found = client.get("/api/admin/users", params={"keyword": "ali"}, headers=admin).json()["data"]["items"]
    assert [u["username"] for u in found] == ["alice"]

    admin_id = next(u["id"] for u in users["items"] if u["username"] == "admin")
    resp = client.put(f"/api/admin/users/{admin_id}/status", json={"status": "DISABLED"}, headers=admin)
    assert resp.status_code == 400 and resp.json()["msg"] == "不能修改管理员账号的状态"

    resp = client.put("/api/admin/users/9999/status", json={"status": "DISABLED"}, headers=admin)
    assert resp.status_code == 404
    resp = client.put(f"/api/admin/users/{admin_id}/status", json={"status": "BANNED"}, headers=admin)
    assert resp.status_code == 400 and resp.json()["msg"] == "状态取值不合法"


def test_book_review(api, client):
    owner = api.user("owner")
    first, second = api.publish(owner, title="一"), api.publish(owner, title="二")
    admin = api.admin()

    pending = client.get("/api/admin/books", params={"status": "PENDING"}, headers=admin).json()["data"]
    assert {b["id"] for b in pending["items"]} == {first, second}

    assert client.post(f"/api/admin/books/{first}/approve", headers=admin).json()["data"]["status"] == "AVAILABLE"
    rejected = client.post(f"/api/admin/books/{second}/reject", json={}, headers=admin).json()["data"]
    assert rejected["status"] == "OFF_SHELF" and rejected["review_note"] == "审核未通过"

    # 非待审核状态不能再审核
    resp = client.post(f"/api/admin/books/{first}/approve", headers=admin)
    assert resp.status_code == 400 and resp.json()["msg"] == "该图书不是待审核状态"

    pending = client.get("/api/admin/books", params={"status": "PENDING"}, headers=admin).json()["data"]
    assert pending["total"] == 0


def test_category_management(api, client):
    admin = api.admin()
    resp = client.post("/api/admin/categories", json={"name": "漫画"}, headers=admin)
    assert resp.status_code == 200
    comic_id = resp.json()["data"]["id"]

    resp = client.post("/api/admin/categories", json={"name": "漫画"}, headers=admin)
    assert resp.status_code == 400 and resp.json()["msg"] == "分类名称已存在"

    resp = client.put(f"/api/admin/categories/{comic_id}", json={"name": "动漫"}, headers=admin)
    assert resp.json()["data"]["name"] == "动漫"
    assert "动漫" in [c["name"] for c in client.get("/api/categories").json()["data"]]

    # 有图书引用（包括已软删除的图书）时不能删除
    owner = api.user("owner")
    book_id = api.publish(owner, category_id=comic_id)
    client.delete(f"/api/admin/books/{book_id}", headers=admin)
    resp = client.delete(f"/api/admin/categories/{comic_id}", headers=admin)
    assert resp.status_code == 400 and resp.json()["msg"] == "该分类下存在图书，无法删除"

    unused_id = client.post("/api/admin/categories", json={"name": "临时"}, headers=admin).json()["data"]["id"]
    assert client.delete(f"/api/admin/categories/{unused_id}", headers=admin).status_code == 200
    assert client.delete(f"/api/admin/categories/{unused_id}", headers=admin).status_code == 404


def test_admin_borrow_and_return_records(api, client):
    owner, alice, bob = api.user("owner"), api.user("alice"), api.user("bob")
    book_id = api.publish_available(owner)
    a = api.borrow(alice, book_id).json()["data"]["id"]
    api.borrow(bob, book_id)
    client.post(f"/api/borrows/{a}/approve", headers=owner)
    return_id = api.apply_return(alice, a).json()["data"]["id"]

    admin = api.admin()
    borrows = client.get("/api/admin/borrows", headers=admin).json()["data"]
    assert borrows["total"] == 2
    assert {b["status"] for b in borrows["items"]} == {"APPROVED", "CANCELED"}
    approved = client.get("/api/admin/borrows", params={"status": "APPROVED"}, headers=admin).json()["data"]
    assert [b["borrower"]["username"] for b in approved["items"]] == ["alice"]

    returns = client.get("/api/admin/returns", headers=admin).json()["data"]
    assert [(r["id"], r["status"]) for r in returns["items"]] == [(return_id, "PENDING")]
    client.post(f"/api/returns/{return_id}/confirm", headers=owner)
    confirmed = client.get("/api/admin/returns", params={"status": "CONFIRMED"}, headers=admin).json()["data"]
    assert confirmed["total"] == 1
