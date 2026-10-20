import io


def test_published_book_waits_for_review(api, client):
    owner = api.user("owner")
    book_id = api.publish(owner)

    assert api.book(book_id, owner)["status"] == "PENDING"
    assert book_id not in api.home_ids()
    # 待审核的书只有发布人和管理员能看到详情
    assert client.get(f"/api/books/{book_id}").status_code == 404
    assert client.get(f"/api/books/{book_id}", headers=api.user("other")).status_code == 404
    assert client.get(f"/api/books/{book_id}", headers=api.admin()).status_code == 200

    client.post(f"/api/admin/books/{book_id}/approve", headers=api.admin())
    assert book_id in api.home_ids()
    detail = client.get(f"/api/books/{book_id}").json()["data"]
    assert detail["status"] == "AVAILABLE"
    assert detail["owner"]["username"] == "owner"
    assert detail["category_name"]


def test_home_search_by_title_or_author_and_category(api, client):
    owner = api.user("owner")
    categories = client.get("/api/categories").json()["data"]
    a = api.publish_available(owner, title="三体", author="刘慈欣", category_id=categories[0]["id"])
    b = api.publish_available(owner, title="活着", author="余华", category_id=categories[1]["id"])
    c = api.publish_available(owner, title="球状闪电", author="刘慈欣", category_id=categories[0]["id"])

    assert set(api.home_ids()) == {a, b, c}
    assert api.home_ids(keyword="三") == [a]
    assert set(api.home_ids(keyword="刘慈")) == {a, c}
    assert api.home_ids(keyword="余华") == [b]
    assert api.home_ids(keyword="%") == []
    assert set(api.home_ids(category_id=categories[0]["id"])) == {a, c}

    page = client.get("/api/books", params={"page": 1, "size": 2}).json()["data"]
    assert page["total"] == 3 and len(page["items"]) == 2


def test_edit_resets_to_pending_and_cancels_pending_borrows(api, client):
    owner, borrower = api.user("owner"), api.user("borrower")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(borrower, book_id).json()["data"]["id"]

    resp = client.put(f"/api/books/{book_id}", json=api.book_payload(title="三体（典藏版）"), headers=owner)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PENDING"
    assert resp.json()["data"]["title"] == "三体（典藏版）"
    assert book_id not in api.home_ids()

    mine = client.get("/api/borrows/mine", headers=borrower).json()["data"]["items"]
    assert [(b["id"], b["status"]) for b in mine] == [(borrow_id, "CANCELED")]


def test_rejected_book_can_be_edited_and_resubmitted(api, client):
    owner = api.user("owner")
    book_id = api.publish(owner)
    resp = client.post(f"/api/admin/books/{book_id}/reject", json={"note": "封面不清晰"}, headers=api.admin())
    assert resp.status_code == 200

    my_books = client.get("/api/users/me/books", headers=owner).json()["data"]["items"]
    assert my_books[0]["status"] == "OFF_SHELF"
    assert my_books[0]["review_note"] == "封面不清晰"

    resp = client.put(f"/api/books/{book_id}", json=api.book_payload(), headers=owner)
    assert resp.json()["data"]["status"] == "PENDING"
    assert resp.json()["data"]["review_note"] == ""


def test_edit_can_change_category(api, client):
    owner = api.user("owner")
    categories = client.get("/api/categories").json()["data"]
    book_id = api.publish(owner, category_id=categories[0]["id"])
    resp = client.put(f"/api/books/{book_id}", json=api.book_payload(category_id=categories[2]["id"]), headers=owner)
    assert resp.json()["data"]["category_id"] == categories[2]["id"]
    assert resp.json()["data"]["category_name"] == categories[2]["name"]


def test_off_shelf_hides_book_and_cancels_pending_borrows(api, client):
    owner, borrower = api.user("owner"), api.user("borrower")
    book_id = api.publish_available(owner)
    api.borrow(borrower, book_id)

    resp = client.post(f"/api/books/{book_id}/off-shelf", headers=owner)
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "OFF_SHELF"
    assert book_id not in api.home_ids()
    assert client.get(f"/api/books/{book_id}").status_code == 404
    assert client.get("/api/borrows/mine", headers=borrower).json()["data"]["items"][0]["status"] == "CANCELED"

    resp = client.post(f"/api/books/{book_id}/off-shelf", headers=owner)
    assert resp.status_code == 400


def test_borrowed_book_cannot_be_edited_or_taken_off_shelf(api, client):
    owner, borrower = api.user("owner"), api.user("borrower")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(borrower, book_id).json()["data"]["id"]
    client.post(f"/api/borrows/{borrow_id}/approve", headers=owner)

    resp = client.put(f"/api/books/{book_id}", json=api.book_payload(), headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "图书已借出，归还后才能编辑"
    resp = client.post(f"/api/books/{book_id}/off-shelf", headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "图书已借出，归还后才能下架"


def test_publish_validation(api, client):
    owner = api.user("owner")
    resp = client.post("/api/books", json=api.book_payload(category_id=9999), headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "图书分类不存在"

    resp = client.post("/api/books", json=api.book_payload(condition="很新"), headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "新旧程度取值不合法"

    resp = client.post("/api/books", json=api.book_payload(title="   "), headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "书名不能为空"

    resp = client.post("/api/books", json=api.book_payload(cover_url="https://evil.example/x.png"), headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "封面图片格式不正确"


def test_upload_cover(api, client):
    owner = api.user("owner")
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    resp = client.post("/api/uploads/cover", files={"file": ("a.png", io.BytesIO(png), "image/png")}, headers=owner)
    assert resp.status_code == 200
    url = resp.json()["data"]["url"]
    assert url.startswith("/uploads/covers/") and url.endswith(".png")
    assert client.get(url).content == png

    # 用上传结果作为封面发布
    book_id = api.publish(owner, cover_url=url)
    assert api.book(book_id, owner)["cover_url"] == url

    # 伪装成图片的文本文件被拒绝
    fake = io.BytesIO(b"<script>alert(1)</script>")
    resp = client.post("/api/uploads/cover", files={"file": ("x.png", fake, "image/png")}, headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "仅支持 JPG、PNG、WEBP 格式的图片"

    big = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (2 * 1024 * 1024))
    resp = client.post("/api/uploads/cover", files={"file": ("big.jpg", big, "image/jpeg")}, headers=owner)
    assert resp.status_code == 400 and resp.json()["msg"] == "图片不能超过 2MB"


def test_comments(api, client):
    owner, reader = api.user("owner"), api.user("reader")
    book_id = api.publish_available(owner)

    assert client.post(f"/api/books/{book_id}/comments", json={"content": "想看"}).status_code == 401
    resp = client.post(f"/api/books/{book_id}/comments", json={"content": "想看"}, headers=reader)
    assert resp.status_code == 200
    client.post(f"/api/books/{book_id}/comments", json={"content": "欢迎借阅"}, headers=owner)

    comments = client.get(f"/api/books/{book_id}/comments").json()["data"]
    assert [(c["user"]["username"], c["content"]) for c in comments] == [("reader", "想看"), ("owner", "欢迎借阅")]

    resp = client.post(f"/api/books/{book_id}/comments", json={"content": ""}, headers=reader)
    assert resp.status_code == 400 and resp.json()["msg"] == "评论内容不能为空"


def test_unknown_book_returns_404(client):
    resp = client.get("/api/books/9999")
    assert resp.status_code == 404
    assert resp.json() == {"code": 404, "msg": "图书不存在", "data": None}
