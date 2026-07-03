import sqlite3
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from app.database import conn
from app.schemas.job import JobCreated, JobUpdate, JobResponse
from app.auth import get_current_user
from app.auth import require_admin

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", dependencies=[Depends(require_admin)], response_model=JobResponse, status_code=201)
def created_job(job: JobCreated, current_user: dict = Depends(get_current_user),):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = conn.cursor()
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        cursor.execute(
            """
            INSERT INTO jobs (title, company, location, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                job.title,
                job.company,
                job.location,
                job.description,
                created_at,
            )
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Job already exists")

    job_id = cursor.lastrowid

    return {
        "id": job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "created_at": created_at,
    }


@router.get("/{job_id}", response_model=JobResponse)
def read_job(job_id: int):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, company, location, description, created_at FROM jobs WHERE id=?"
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return dict(row)


@router.get("/", response_model=list[JobResponse])
def read_all_jobs(
        company: str | None = None,
        location: str | None = None,
        search: str | None = None,
        sort_by: str | None = "created_at",
        order: str | None = "desc",
        limit: int = 10,
        offset: int = 0
):
    cursor = conn.cursor()

    query = "SELECT id, title, company, location, description, created_at FROM jobs"
    params = []

    filters = []
    if company:
        filters.append("company=?")
        params.append(company)
    if location:
        filters.append("location=?")
        params.append(location)
    if search:
        filters.append("title LIKE ? OR description LIKE ?")
        params.extend([f"%{search}%", f"%{search}%"])

    if filters:
        query += " WHERE " + " AND ".join(filters)

    # sorting
    if sort_by not in ["created_at", "title", "company"]:
        sort_by = "created_at"
    if order.lower() not in ["asc", "desc"]:
        order = "desc"

    query += f" ORDER BY {sort_by} {order.upper()}"

    # pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


@router.put("/{job_id}", dependencies=[Depends(require_admin)], response_model=JobResponse)
def update_job(job_id: int, job: JobUpdate, current_user: dict = Depends(get_current_user),):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE jobs
        SET title=?, company=?, location=?, description=?
        WHERE id=?
        """,
        (
            job.title,
            job.company,
            job.location,
            job.description,
            job_id,
        ),
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found")

    cursor.execute(
        "SELECT id, title, company, location, description, created_at FROM jobs WHERE id=?",
        (job_id,),
    )

    return dict(cursor.fetchone())


@router.delete("/{job_id}", dependencies=[Depends(require_admin)], status_code=204)
def delete_job(job_id: int, current_user: dict = Depends(get_current_user),):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM jobs WHERE id=?",
        (job_id,),
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found")
