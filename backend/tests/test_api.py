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


def test_create_candidate_and_verify(client):
    token = get_admin_token(client)
    resp = client.post(
        "/candidates",
        json={
            "name": "Test User",
            "email": "testuser_unique@example.com",
            "role_applied": "Backend Engineer",
            "skills": ["Python", "FastAPI"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test User"
    assert data["email"] == "testuser_unique@example.com"
    assert data["role_applied"] == "Backend Engineer"
    assert data["status"] == "new"
    assert data["skills"] == ["Python", "FastAPI"]
    assert "internal_notes" in data


def test_reviewer_cannot_see_other_reviewer_scores(client):
    admin_token = get_admin_token(client)

    resp = client.post(
        "/auth/register",
        json={"email": "reviewer1_test@test.com", "password": "pass123", "name": "Reviewer One"},
    )
    assert resp.status_code == 200
    token1 = resp.json()["access_token"]

    resp = client.post(
        "/auth/register",
        json={"email": "reviewer2_test@test.com", "password": "pass123", "name": "Reviewer Two"},
    )
    assert resp.status_code == 200
    token2 = resp.json()["access_token"]

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    candidates = resp.json()["items"]
    assert len(candidates) > 0
    candidate_id = candidates[0]["id"]

    client.post(
        f"/candidates/{candidate_id}/scores",
        json={"category": "Technical", "score": 4, "note": "Good skills"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    resp1 = client.get(
        f"/candidates/{candidate_id}/scores",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp1.status_code == 200
    assert len(resp1.json()) == 1

    resp2 = client.get(
        f"/candidates/{candidate_id}/scores",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


def test_reviewer_cannot_see_internal_notes(client):
    resp = client.post(
        "/auth/register",
        json={"email": "reviewer3_test@test.com", "password": "pass123", "name": "Reviewer Three"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    if len(data) > 0:
        assert data[0].get("internal_notes") is None


def test_soft_delete(client):
    admin_token = get_admin_token(client)
    resp = client.post(
        "/candidates",
        json={
            "name": "Delete Test",
            "email": "deletetest_unique@example.com",
            "role_applied": "Engineer",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    candidate_id = resp.json()["id"]

    resp = client.delete(
        f"/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204

    resp = client.get(
        f"/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_ai_summary_generation(client):
    admin_token = get_admin_token(client)

    resp = client.get("/candidates", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    candidates = resp.json()["items"]
    assert len(candidates) > 0
    candidate_id = candidates[0]["id"]

    resp = client.post(
        f"/candidates/{candidate_id}/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert len(data["summary"]) > 0
