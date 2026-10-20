import pytest

PROTECTED = [
    ("GET", "/api/users/me"),
    ("GET", "/api/users/me/books"),
    ("POST", "/api/books"),
    ("PUT", "/api/books/1"),
    ("POST", "/api/books/1/off-shelf"),
    ("POST", "/api/books/1/comments"),
    ("POST", "/api/uploads/cover"),
    ("POST", "/api/borrows"),
    ("GET", "/api/borrows/mine"),
    ("GET", "/api/borrows/received"),
    ("POST", "/api/borrows/1/approve"),
    ("POST", "/api/borrows/1/reject"),
    ("POST", "/api/returns"),
    ("GET", "/api/returns/mine"),
    ("GET", "/api/returns/received"),
    ("POST", "/api/returns/1/confirm"),
    ("POST", "/api/returns/1/reject"),
]

ADMIN_ONLY = [
    ("GET", "/api/admin/users"),
    ("PUT", "/api/admin/users/1/status"),
    ("GET", "/api/admin/books"),
    ("POST", "/api/admin/books/1/approve"),
    ("POST", "/api/admin/books/1/reject"),
    ("DELETE", "/api/admin/books/1"),
    ("POST", "/api/admin/categories"),
    ("PUT", "/api/admin/categories/1"),
    ("DELETE", "/api/admin/categories/1"),
    ("GET", "/api/admin/borrows"),
    ("GET", "/api/admin/returns"),
]


@pytest.mark.parametrize(("method", "path"), PROTECTED + ADMIN_ONLY)
def test_anonymous_is_rejected(client, method, path):
    resp = client.request(method, path)
    assert resp.status_code == 401
    assert resp.json() == {"code": 401, "msg": "请先登录", "data": None}


@pytest.mark.parametrize(("method", "path"), ADMIN_ONLY)
def test_normal_user_cannot_access_admin_api(api, client, method, path):
    resp = client.request(method, path, headers=api.user("alice"))
    assert resp.status_code == 403
    assert resp.json()["msg"] == "无管理员权限"


def test_public_endpoints_need_no_login(api, client):
    owner = api.user("owner")
    book_id = api.publish_available(owner)
    assert client.get("/api/books").status_code == 200
    assert client.get("/api/categories").status_code == 200
    assert client.get(f"/api/books/{book_id}").status_code == 200
    assert client.get(f"/api/books/{book_id}/comments").status_code == 200


def test_cannot_edit_or_off_shelf_others_book(api, client):
    owner, other = api.user("owner"), api.user("other")
    book_id = api.publish_available(owner)

    resp = client.put(f"/api/books/{book_id}", json=api.book_payload(title="改掉"), headers=other)
    assert resp.status_code == 403
    assert resp.json()["msg"] == "无权操作他人发布的图书"
    assert client.post(f"/api/books/{book_id}/off-shelf", headers=other).status_code == 403
    assert api.book(book_id)["title"] == "三体"
    assert api.book(book_id)["status"] == "AVAILABLE"


def test_cannot_handle_others_borrow_or_return(api, client):
    owner, borrower, stranger = api.user("owner"), api.user("borrower"), api.user("stranger")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(borrower, book_id).json()["data"]["id"]

    assert client.post(f"/api/borrows/{borrow_id}/approve", headers=stranger).status_code == 403
    assert client.post(f"/api/borrows/{borrow_id}/reject", headers=borrower).status_code == 403
    assert client.post(f"/api/borrows/{borrow_id}/approve", headers=owner).status_code == 200

    # 只有借书人本人能申请归还
    resp = api.apply_return(stranger, borrow_id)
    assert resp.status_code == 403
    assert resp.json()["msg"] == "只能归还自己借到的图书"
    assert api.apply_return(owner, borrow_id).status_code == 403

    return_id = api.apply_return(borrower, borrow_id).json()["data"]["id"]
    assert client.post(f"/api/returns/{return_id}/confirm", headers=stranger).status_code == 403
    assert client.post(f"/api/returns/{return_id}/confirm", headers=borrower).status_code == 403
    assert client.post(f"/api/returns/{return_id}/reject", headers=stranger).status_code == 403


def test_received_lists_only_show_own_data(api, client):
    owner, borrower, stranger = api.user("owner"), api.user("borrower"), api.user("stranger")
    book_id = api.publish_available(owner)
    api.borrow(borrower, book_id)

    assert client.get("/api/borrows/received", headers=owner).json()["data"]["total"] == 1
    assert client.get("/api/borrows/received", headers=stranger).json()["data"]["total"] == 0
    assert client.get("/api/borrows/mine", headers=borrower).json()["data"]["total"] == 1
    assert client.get("/api/borrows/mine", headers=stranger).json()["data"]["total"] == 0
