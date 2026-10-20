from app.models import Book, BookStatus


def test_full_borrow_and_return_loop(api, client):
    owner, alice, bob = api.user("owner"), api.user("alice"), api.user("bob")
    book_id = api.publish_available(owner)

    # A、B 同时申请
    a_borrow = api.borrow(alice, book_id, "想借两周").json()["data"]
    b_borrow = api.borrow(bob, book_id).json()["data"]
    assert a_borrow["status"] == "PENDING" and a_borrow["message"] == "想借两周"
    received = client.get("/api/borrows/received", headers=owner).json()["data"]
    assert received["total"] == 2

    # 同意 A：书变成已借出，B 的申请自动失效
    resp = client.post(f"/api/borrows/{a_borrow['id']}/approve", headers=owner)
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "APPROVED"
    assert api.book(book_id)["status"] == "BORROWED"
    assert book_id not in api.home_ids()
    b_status = client.get("/api/borrows/mine", headers=bob).json()["data"]["items"][0]["status"]
    assert b_status == "CANCELED"
    resp = client.post(f"/api/borrows/{b_borrow['id']}/approve", headers=owner)
    assert resp.status_code == 400

    # A 申请归还，发布人拒绝：书保持已借出
    r1 = api.apply_return(alice, a_borrow["id"], "已归还").json()["data"]
    assert r1["status"] == "PENDING"
    resp = api.apply_return(alice, a_borrow["id"])
    assert resp.status_code == 400 and resp.json()["msg"] == "已有待处理的归还申请，请等待发布人确认"
    resp = client.post(f"/api/returns/{r1['id']}/reject", headers=owner)
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "REJECTED"
    assert api.book(book_id)["status"] == "BORROWED"

    # A 再次申请，发布人确认：书回到待漂流
    r2 = api.apply_return(alice, a_borrow["id"], "这次真的还了").json()["data"]
    resp = client.post(f"/api/returns/{r2['id']}/confirm", headers=owner)
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "CONFIRMED"
    assert api.book(book_id)["status"] == "AVAILABLE"
    assert book_id in api.home_ids()
    assert client.post(f"/api/returns/{r2['id']}/confirm", headers=owner).status_code == 400

    # 流转记录：借阅记录变为已归还，并带有两次归还申请的历史
    mine = client.get("/api/borrows/mine", headers=alice).json()["data"]["items"][0]
    assert mine["status"] == "RETURNED"
    assert [r["status"] for r in mine["returns"]] == ["REJECTED", "CONFIRMED"]
    assert mine["handled_at"] is not None
    returns = client.get("/api/returns/mine", headers=alice).json()["data"]["items"]
    assert [r["status"] for r in returns] == ["CONFIRMED", "REJECTED"]
    assert client.get("/api/returns/received", headers=owner).json()["data"]["total"] == 2

    # 已归还的借阅不能再申请归还
    assert api.apply_return(alice, a_borrow["id"]).status_code == 400

    # B 可以再次借阅
    b2 = api.borrow(bob, book_id).json()["data"]
    assert client.post(f"/api/borrows/{b2['id']}/approve", headers=owner).status_code == 200
    assert api.book(book_id)["status"] == "BORROWED"


def test_reject_borrow_keeps_book_available(api, client):
    owner, alice = api.user("owner"), api.user("alice")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(alice, book_id).json()["data"]["id"]

    resp = client.post(f"/api/borrows/{borrow_id}/reject", headers=owner)
    assert resp.status_code == 200 and resp.json()["data"]["status"] == "REJECTED"
    assert api.book(book_id)["status"] == "AVAILABLE"
    assert client.post(f"/api/borrows/{borrow_id}/approve", headers=owner).status_code == 400
    # 被拒后可以重新申请
    assert api.borrow(alice, book_id).status_code == 200


def test_borrow_rules(api, client):
    owner, alice, bob = api.user("owner"), api.user("alice"), api.user("bob")
    book_id = api.publish_available(owner)

    resp = api.borrow(owner, book_id)
    assert resp.status_code == 400 and resp.json()["msg"] == "不能借阅自己发布的图书"

    assert api.borrow(alice, book_id).status_code == 200
    resp = api.borrow(alice, book_id)
    assert resp.status_code == 400 and resp.json()["msg"] == "你已提交过该图书的借阅申请，请等待发布人处理"

    pending_id = api.publish(owner, title="待审核的书")
    resp = api.borrow(alice, pending_id)
    assert resp.status_code == 400 and resp.json()["msg"] == "该图书当前不可借阅"

    borrow_id = client.get("/api/borrows/received", headers=owner).json()["data"]["items"][0]["id"]
    client.post(f"/api/borrows/{borrow_id}/approve", headers=owner)
    resp = api.borrow(bob, book_id)
    assert resp.status_code == 400 and resp.json()["msg"] == "该图书当前不可借阅"

    assert api.borrow(alice, 9999).status_code == 404


def test_return_requires_approved_borrow(api, client):
    owner, alice = api.user("owner"), api.user("alice")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(alice, book_id).json()["data"]["id"]

    resp = api.apply_return(alice, borrow_id)
    assert resp.status_code == 400 and resp.json()["msg"] == "该借阅不在借阅中，无法申请归还"
    assert api.apply_return(alice, 9999).status_code == 404


def test_approve_fails_when_book_is_no_longer_available(api, client, db):
    """模拟并发：申请仍是待处理，但图书已经被另一个事务改成已借出，条件更新影响 0 行。"""
    owner, alice = api.user("owner"), api.user("alice")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(alice, book_id).json()["data"]["id"]

    db.get(Book, book_id).status = BookStatus.BORROWED
    db.commit()

    resp = client.post(f"/api/borrows/{borrow_id}/approve", headers=owner)
    assert resp.status_code == 400
    assert resp.json()["msg"] == "图书当前不可借出，可能已借给他人或已下架"
    # 事务已回滚，申请仍是待处理
    assert client.get("/api/borrows/mine", headers=alice).json()["data"]["items"][0]["status"] == "PENDING"


def test_deleted_book_keeps_history_and_return_still_works(api, client):
    owner, alice, bob = api.user("owner"), api.user("alice"), api.user("bob")
    book_id = api.publish_available(owner)
    borrow_id = api.borrow(alice, book_id).json()["data"]["id"]
    client.post(f"/api/borrows/{borrow_id}/approve", headers=owner)

    other_id = api.publish_available(owner, title="另一本")
    bob_borrow = api.borrow(bob, other_id).json()["data"]["id"]

    admin = api.admin()
    assert client.delete(f"/api/admin/books/{book_id}", headers=admin).status_code == 200
    assert client.delete(f"/api/admin/books/{other_id}", headers=admin).status_code == 200
    assert client.get(f"/api/books/{book_id}").status_code == 404
    assert client.delete(f"/api/admin/books/{book_id}", headers=admin).status_code == 404

    # 待处理的申请失效
    assert client.get("/api/borrows/mine", headers=bob).json()["data"]["items"][0]["status"] == "CANCELED"
    assert client.post(f"/api/borrows/{bob_borrow}/approve", headers=owner).status_code == 400

    # 已借出的书仍可走完归还流程，历史记录保留
    return_id = api.apply_return(alice, borrow_id).json()["data"]["id"]
    assert client.post(f"/api/returns/{return_id}/confirm", headers=owner).status_code == 200
    record = client.get("/api/borrows/mine", headers=alice).json()["data"]["items"][0]
    assert record["status"] == "RETURNED"
    assert record["book"]["is_deleted"] is True
    assert book_id not in api.home_ids()
