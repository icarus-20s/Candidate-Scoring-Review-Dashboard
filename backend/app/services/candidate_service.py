import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from ..models import get_db, DATABASE_URL
import aiosqlite

# Returns a paginated, filtered list of active (non-archived) candidates with total count.
async def list_candidates(
    status: Optional[str] = None,
    role_applied: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    offset: int = 0,
    page_size: int = 20,
):
    db = await get_db()
    conditions = ["c.status != 'archived' AND c.deleted_at IS NULL"]
    params = []

    if status:
        conditions.append("c.status = ?")
        params.append(status)
    if role_applied:
        conditions.append("c.role_applied = ?")
        params.append(role_applied)
    if skill:
        conditions.append("c.skills LIKE ?")
        params.append(f"%{skill}%")
    if keyword:
        conditions.append("(c.name LIKE ? OR c.email LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    count_query = f"SELECT COUNT(*) as total FROM candidates c WHERE {where_clause}"
    cursor = await db.execute(count_query, params)
    row = await cursor.fetchone()
    total = row["total"]

    query = f"""
        SELECT c.* FROM candidates c
        WHERE {where_clause}
        ORDER BY c.created_at DESC
        LIMIT ? OFFSET ?
    """
    cursor = await db.execute(query, params + [page_size, offset])
    rows = await cursor.fetchall()
    await db.close()

    items = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item.get("skills", "[]"))
        items.append(item)

    return items, total


# Fetches a single active candidate by ID. Strips internal_notes for non-admin roles.
async def get_candidate(candidate_id: int, user_role: str = "reviewer"):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM candidates WHERE id = ? AND status != 'archived' AND deleted_at IS NULL", (candidate_id,))
    row = await cursor.fetchone()
    if not row:
        await db.close()
        return None

    candidate = dict(row)
    candidate["skills"] = json.loads(candidate.get("skills", "[]"))

    if user_role != "admin":
        candidate.pop("internal_notes", None)

    await db.close()
    return candidate


# Inserts a new candidate record and returns the created row.
async def create_candidate(data) -> dict:
    db = await get_db()
    skills_json = json.dumps(data.get("skills", []))
    cursor = await db.execute(
        """INSERT INTO candidates (name, email, role_applied, skills)
           VALUES (?, ?, ?, ?)""",
        (data["name"], data["email"], data["role_applied"], skills_json),
    )
    await db.commit()
    new_id = cursor.lastrowid
    cursor2 = await db.execute("SELECT * FROM candidates WHERE id = ?", (new_id,))
    row = await cursor2.fetchone()
    await db.close()
    result = dict(row)
    result["skills"] = json.loads(result["skills"])
    return result


# Updates candidate fields. Non-admin roles are prevented from modifying internal_notes.
async def update_candidate(candidate_id: int, data: dict, user_role: str = "admin") -> Optional[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    existing = await cursor.fetchone()
    if not existing:
        await db.close()
        return None

    if user_role != "admin":
        data.pop("internal_notes", None)

    fields = []
    params = []
    for key, value in data.items():
        if value is not None:
            if key == "skills":
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            params.append(value)

    if not fields:
        await db.close()
        return dict(existing)

    params.append(candidate_id)
    await db.execute(
        f"UPDATE candidates SET {', '.join(fields)} WHERE id = ?",
        params,
    )
    await db.commit()
    cursor2 = await db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    updated = await cursor2.fetchone()
    await db.close()
    result = dict(updated)
    result["skills"] = json.loads(result["skills"])
    return result


# Marks a candidate as archived with a deleted_at timestamp. Returns True if a row was updated.
async def soft_delete_candidate(candidate_id: int) -> bool:
    db = await get_db()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "UPDATE candidates SET status = 'archived', deleted_at = ? WHERE id = ? AND status != 'archived'",
        (now, candidate_id),
    )
    await db.commit()
    affected = cursor.rowcount
    await db.close()
    return affected > 0


# Inserts a score record and auto-advances candidate status from new to reviewed. Returns the created score with reviewer name.
async def add_score(candidate_id: int, data, reviewer_id: int) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id FROM candidates WHERE id = ? AND status != 'archived'",
        (candidate_id,),
    )
    if not await cursor.fetchone():
        await db.close()
        raise ValueError("Candidate not found or archived")

    cursor2 = await db.execute(
        """INSERT INTO scores (candidate_id, category, score, reviewer_id, note)
           VALUES (?, ?, ?, ?, ?)""",
        (candidate_id, data.category, data.score, reviewer_id, data.note or ""),
    )
    await db.commit()
    score_id = cursor2.lastrowid

    await db.execute(
        "UPDATE candidates SET status = 'reviewed' WHERE id = ? AND status = 'new'",
        (candidate_id,),
    )
    await db.commit()
    cursor3 = await db.execute(
        """SELECT s.*, u.name as reviewer_name
           FROM scores s
           JOIN users u ON s.reviewer_id = u.id
           WHERE s.id = ?""",
        (score_id,),
    )
    result = await cursor3.fetchone()
    await db.close()
    return dict(result)


# Returns scores for a candidate. Admins see all scores; reviewers see only their own.
async def get_scores_for_candidate(candidate_id: int, user_id: int, user_role: str) -> List[dict]:
    db = await get_db()
    if user_role == "admin":
        cursor = await db.execute(
            """SELECT s.*, u.name as reviewer_name
               FROM scores s
               JOIN users u ON s.reviewer_id = u.id
               WHERE s.candidate_id = ?
               ORDER BY s.created_at DESC""",
            (candidate_id,),
        )
    else:
        cursor = await db.execute(
            """SELECT s.*, u.name as reviewer_name
               FROM scores s
               JOIN users u ON s.reviewer_id = u.id
               WHERE s.candidate_id = ? AND s.reviewer_id = ?
               ORDER BY s.created_at DESC""",
            (candidate_id, user_id),
        )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]


# Simulates a 2-second async LLM call, computes average scores per category, persists the summary to the candidate record, and returns it.
async def generate_ai_summary(candidate_id: int) -> str:
    await asyncio.sleep(2)
    db = await get_db()
    cursor = await db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    candidate = await cursor.fetchone()
    if not candidate:
        await db.close()
        raise ValueError("Candidate not found")

    scores_cursor = await db.execute(
        "SELECT * FROM scores WHERE candidate_id = ?", (candidate_id,)
    )
    scores = await scores_cursor.fetchall()
    await db.close()

    candidate = dict(candidate)
    categories = {}
    for s in scores:
        s = dict(s)
        cat = s["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(s["score"])

    avg_scores = {cat: round(sum(v) / len(v), 1) for cat, v in categories.items()}
    total_scores = sum(len(v) for v in categories.values())

    if total_scores == 0:
        summary = (
            f"{candidate['name']} has applied for {candidate['role_applied']}. "
            "No scores have been submitted yet. "
            "Awaiting reviewer evaluations across categories."
        )
    else:
        overall = round(sum(avg_scores.values()) / len(avg_scores), 1) if avg_scores else 0
        ratings = "; ".join(f"{cat}: {avg}" for cat, avg in avg_scores.items())
        summary = (
            f"Candidate {candidate['name']} (applying for {candidate['role_applied']}) "
            f"has an overall score of {overall}/5 based on {total_scores} evaluations across "
            f"{len(avg_scores)} categories. Breakdown: {ratings}. "
            f"Current status: {candidate['status']}."
        )

    db2 = await get_db()
    await db2.execute(
        "UPDATE candidates SET ai_summary = ? WHERE id = ?",
        (summary, candidate_id),
    )
    await db2.commit()
    await db2.close()

    return summary


# Creates a new user with a hashed password. Raises ValueError on duplicate email.
async def create_user(email: str, password: str, name: str, role: str = "reviewer") -> dict:
    from ..auth import hash_password

    db = await get_db()
    hashed = hash_password(password)
    try:
        cursor = await db.execute(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            (email, hashed, name, role),
        )
        await db.commit()
        user_id = cursor.lastrowid
        from datetime import datetime, timezone
        return {"id": user_id, "email": email, "name": name, "role": role, "created_at": datetime.now(timezone.utc).isoformat()}
    except aiosqlite.IntegrityError:
        await db.close()
        raise ValueError("Email already exists")
    finally:
        await db.close()


# Looks up a user by email, returns None if not found.
async def get_user_by_email(email: str) -> Optional[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = await cursor.fetchone()
    await db.close()
    return dict(row) if row else None


# Idempotent: creates the default admin user if it does not exist.
async def seed_admin():
    db = await get_db()
    cursor = await db.execute("SELECT id FROM users WHERE email = ?", ("admin@techkraft.com",))
    if await cursor.fetchone():
        await db.close()
        return

    from ..auth import hash_password
    hashed = hash_password("admin123")
    await db.execute(
        "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
        ("admin@techkraft.com", hashed, "Admin User", "admin"),
    )
    await db.commit()
    await db.close()


# Idempotent: inserts 30 sample candidates across various roles and statuses if the table is empty.
async def seed_sample_candidates():
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM candidates")
    row = await cursor.fetchone()
    if row["cnt"] > 0:
        await db.close()
        return

    samples = [
        ("Alice Johnson", "alice@example.com", "Frontend Engineer", "new", '["React", "TypeScript", "CSS"]'),
        ("Bob Smith", "bob@example.com", "Backend Engineer", "new", '["Python", "FastAPI", "PostgreSQL"]'),
        ("Carol Davis", "carol@example.com", "Full Stack Engineer", "reviewed", '["React", "Python", "Docker"]'),
        ("David Wilson", "david@example.com", "DevOps Engineer", "new", '["AWS", "Docker", "Kubernetes"]'),
        ("Eve Martin", "eve@example.com", "Data Engineer", "hired", '["Python", "Spark", "SQL"]'),
        ("Frank Brown", "frank@example.com", "Frontend Engineer", "rejected", '["Vue", "JavaScript"]'),
        ("Grace Lee", "grace@example.com", "Backend Engineer", "new", '["Go", "PostgreSQL", "Redis"]'),
        ("Henry Taylor", "henry@example.com", "Full Stack Engineer", "reviewed", '["React", "Node.js", "MongoDB"]'),
        ("Ivy Chen", "ivy@example.com", "Frontend Engineer", "new", '["React", "Next.js", "Tailwind"]'),
        ("Jack Williams", "jack@example.com", "Backend Engineer", "new", '["Rust", "PostgreSQL", "Docker"]'),
        ("Kate Miller", "kate@example.com", "Data Engineer", "reviewed", '["Python", "Airflow", "Snowflake"]'),
        ("Liam Garcia", "liam@example.com", "DevOps Engineer", "new", '["Terraform", "AWS", "CI/CD"]'),
        ("Mia Robinson", "mia@example.com", "Full Stack Engineer", "hired", '["React", "Django", "PostgreSQL"]'),
        ("Noah Clark", "noah@example.com", "Frontend Engineer", "new", '["Angular", "TypeScript", "RxJS"]'),
        ("Olivia Lewis", "olivia@example.com", "Backend Engineer", "reviewed", '["Java", "Spring", "Kafka"]'),
        ("Patrick Hall", "patrick@example.com", "Data Engineer", "new", '["Python", "dbt", "Redshift"]'),
        ("Quinn Young", "quinn@example.com", "DevOps Engineer", "rejected", '["Kubernetes", "Helm", "Prometheus"]'),
        ("Rachel King", "rachel@example.com", "Frontend Engineer", "new", '["Svelte", "TypeScript", "Vite"]'),
        ("Samuel Wright", "samuel@example.com", "Backend Engineer", "hired", '["Python", "FastAPI", "MongoDB"]'),
        ("Tara Lopez", "tara@example.com", "Full Stack Engineer", "new", '["Vue", "Node.js", "GraphQL"]'),
        ("Uma Patel", "uma@example.com", "Data Engineer", "new", '["Python", "Spark", "Kafka"]'),
        ("Victor Adams", "victor@example.com", "DevOps Engineer", "reviewed", '["AWS", "Pulumi", "Docker"]'),
        ("Wendy Scott", "wendy@example.com", "Frontend Engineer", "new", '["React", "Redux", "Jest"]'),
        ("Xander Torres", "xander@example.com", "Backend Engineer", "new", '["Go", "gRPC", "Redis"]'),
        ("Yara Nelson", "yara@example.com", "Full Stack Engineer", "rejected", '["React", "Flask", "SQLAlchemy"]'),
        ("Zack Hill", "zack@example.com", "DevOps Engineer", "new", '["Docker", "Ansible", "Jenkins"]'),
        ("Aria Baker", "aria@example.com", "Data Engineer", "reviewed", '["Python", "Kafka", "ClickHouse"]'),
        ("Blake Green", "blake@example.com", "Backend Engineer", "new", '["C#", ".NET", "SQL Server"]'),
        ("Chloe Adams", "chloe@example.com", "Frontend Engineer", "new", '["React", "Storybook", "Cypress"]'),
        ("Dylan Foster", "dylan@example.com", "Full Stack Engineer", "reviewed", '["Next.js", "Prisma", "Tailwind"]'),
    ]
    await db.executemany(
        "INSERT INTO candidates (name, email, role_applied, status, skills) VALUES (?, ?, ?, ?, ?)",
        samples,
    )
    await db.commit()
    await db.close()
