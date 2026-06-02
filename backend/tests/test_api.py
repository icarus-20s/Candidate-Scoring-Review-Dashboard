import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

os.environ["JWT_SECRET"] = "test-secret-key-for-testing-purposes-only"


@pytest.fixture(scope="module")
def client():
    db_path = os.path.join(os.path.dirname(__file__), "..", "app.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    import app.models as models
    import asyncio

    async def setup():
        await models.init_db()
        from app.services.candidate_service import seed_admin, seed_sample_candidates
        await seed_admin()
        await seed_sample_candidates()

    asyncio.run(setup())

    from app.main import app
    with TestClient(app) as c:
        yield c


def get_admin_token(client):
    resp = client.post("/auth/login", json={"email": "admin@techkraft.com", "password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


_counter = 0

def unique_email(prefix="user"):
    global _counter
    _counter += 1
    return f"{prefix}_{_counter}@test.com"


def register_reviewer(client, name="Reviewer"):
    email = unique_email("reviewer")
    resp = client.post("/auth/register", json={"email": email, "password": "pass123", "name": name})
    assert resp.status_code == 200
    return resp.json()["access_token"], resp.json()["user"]


def pick_candidate_id(client, token):
    resp = client.get("/candidates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    return items[0]["id"]


def test_create_candidate_and_verify(client):
    token = get_admin_token(client)
    email = unique_email("create")
    resp = client.post(
        "/candidates",
        json={"name": "Test User", "email": email, "role_applied": "Backend Engineer", "skills": ["Python", "FastAPI"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test User"
    assert data["email"] == email
    assert data["role_applied"] == "Backend Engineer"
    assert data["status"] == "new"
    assert data["skills"] == ["Python", "FastAPI"]
    assert "internal_notes" in data


def test_reviewer_cannot_see_other_reviewer_scores(client):
    admin_token = get_admin_token(client)
    token1, _ = register_reviewer(client, "Reviewer One")
    token2, _ = register_reviewer(client, "Reviewer Two")
    candidate_id = pick_candidate_id(client, admin_token)

    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "Technical", "score": 4, "note": "Good skills"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    resp1 = client.get(f"/candidates/{candidate_id}/scores", headers={"Authorization": f"Bearer {token1}"})
    assert resp1.status_code == 200
    assert len(resp1.json()) == 1

    resp2 = client.get(f"/candidates/{candidate_id}/scores", headers={"Authorization": f"Bearer {token2}"})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


def test_reviewer_cannot_see_internal_notes(client):
    token, _ = register_reviewer(client, "Reviewer Three")

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item.get("internal_notes") is None


def test_soft_delete(client):
    admin_token = get_admin_token(client)
    email = unique_email("delete")
    resp = client.post(
        "/candidates",
        json={"name": "Delete Test", "email": email, "role_applied": "Engineer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    candidate_id = resp.json()["id"]

    resp = client.delete(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 204

    resp = client.get(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_ai_summary_generation(client):
    admin_token = get_admin_token(client)
    candidate_id = pick_candidate_id(client, admin_token)

    resp = client.post(f"/candidates/{candidate_id}/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert len(data["summary"]) > 0

    resp = client.get(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json().get("ai_summary") == data["summary"]



def test_auto_status_progression(client):
    admin_token = get_admin_token(client)

    email = unique_email("progression")
    resp = client.post(
        "/candidates",
        json={"name": "Progression Test", "email": email, "role_applied": "Engineer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    candidate_id = resp.json()["id"]
    assert resp.json()["status"] == "new"

    token, _ = register_reviewer(client, "Scorer")
    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "Communication", "score": 3},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = client.get(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.json()["status"] == "reviewed"


def test_admin_can_change_status(client):
    admin_token = get_admin_token(client)
    candidate_id = pick_candidate_id(client, admin_token)

    for status in ("hired", "rejected"):
        resp = client.patch(
            f"/candidates/{candidate_id}",
            json={"status": status},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == status


def test_reviewer_cannot_change_status(client):
    admin_token = get_admin_token(client)
    token, _ = register_reviewer(client, "Status Blocker")
    candidate_id = pick_candidate_id(client, admin_token)

    resp = client.patch(
        f"/candidates/{candidate_id}",
        json={"status": "hired"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_reviewer_cannot_edit_internal_notes(client):
    admin_token = get_admin_token(client)
    token, _ = register_reviewer(client, "Notes Blocker")
    candidate_id = pick_candidate_id(client, admin_token)

    resp = client.patch(
        f"/candidates/{candidate_id}",
        json={"internal_notes": "should not work"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_reviewer_sees_no_notes_on_detail(client):
    admin_token = get_admin_token(client)
    token, _ = register_reviewer(client, "Detail Viewer")

    candidate_id = pick_candidate_id(client, admin_token)
    client.patch(
        f"/candidates/{candidate_id}",
        json={"internal_notes": "secret admin note"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    resp = client.get(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json().get("internal_notes") is None


def test_pagination(client):
    admin_token = get_admin_token(client)

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {admin_token}"})
    total = resp.json()["total"]
    assert total >= 30

    resp = client.get("/candidates?page_size=5&offset=0", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_size"] == 5
    assert len(data["items"]) == 5
    assert data["total"] == total
    assert data["next_offset"] == 5

    resp = client.get(f"/candidates?page_size=5&offset=5", headers={"Authorization": f"Bearer {admin_token}"})
    assert len(resp.json()["items"]) == 5

    resp = client.get(f"/candidates?page_size={total}&offset=0", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.json()["next_offset"] is None


def test_page_size_max_50(client):
    admin_token = get_admin_token(client)
    resp = client.get("/candidates?page_size=100", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 422


def test_non_admin_cannot_delete(client):
    token, _ = register_reviewer(client, "Non-Admin Deleter")
    resp = client.delete("/candidates/1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_soft_deleted_hidden_from_list(client):
    admin_token = get_admin_token(client)
    email = unique_email("hidden")
    resp = client.post(
        "/candidates",
        json={"name": "Hidden Test", "email": email, "role_applied": "Engineer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = resp.json()["id"]
    client.delete(f"/candidates/{cid}", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {admin_token}"})
    ids = [item["id"] for item in resp.json()["items"]]
    assert cid not in ids
