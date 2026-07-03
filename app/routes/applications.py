import sqlite3
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from app.database import conn
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.auth import require_admin

router = APIRouter(prefix="/jobs", tags=["applications"])


@router.post("/", response_model=ApplicationCreate, status_code=201)
def create_application(application: ApplicationCreate):
    cursor = conn.cursor()
    applied_at = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT id FROM jobs WHERE id=?", (application.job_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Job not found")

    cursor.execute(
        """
        INSERT INTO applications (job_id, applicant_name, applicant_email, applied_at
        VALUES (?, ?, ?, ?)
        """,
        (
            application.job_id,
            application.applicant_name,
            application.applicant_email,
            applied_at
        )
    )
    conn.commit()
    app_id = cursor.lastrowid

    return {
        "id": app_id,
        "job_id": application.job_id,
        "applicant_name": application.applicant_name,
        "applicant_email": application.applicant_email,
        "applied_at": applied_at
    }


@router.get("/{job_id}/apply", dependencies=[Depends(require_admin)], status_code=201)
def apply_to_job(job_id: int, application: ApplicationCreate):
    cursor = conn.cursor()

    applied_at = datetime.now(timezone.utc).isoformat()

    # Ensure job exists
    cursor.execute("SELECT id FROM jobs WHERE id=?", (job_id,))
    job = cursor.fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        cursor.execute(
            """
            INSERT INTO applications (job_id, applicant_name, applicant_email, applied_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                job_id,
                application.applicant_name,
                application.applicant_email,
                applied_at,
            )
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=404, detail="Application failed")

    return {
        "job_id": job_id,
        "applicant_name": application.applicant_name,
        "applicant_email": application.applicant_email,
        "applied_at": applied_at,
    }


@router.get("/{job_id}/applications", response_model=list[ApplicationResponse])
def get_applications_for_job(
        job_id: int,
        limit: int = 10,
        offset: int = 0
):
    cursor = conn.cursor()

    # Ensure the job exists
    cursor.execute("SELECT id FROM jobs WHERE id=?", (job_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Job not found")

    cursor.execute(
        """
         SELECT id, job_id, applicant_name, applicant_email, applied_at
         FROM applications
         WHERE jobs_id=?
        LIMIT ? OFFSET ?
        """,
        (job_id, limit, offset)
    )
    rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "job_id": row["job_id"],
            "applicant_name": row["applicant_name"],
            "applicant_email": row["applicant_email"],
            "applied_at": row["applied_at"],

        }
        for row in rows
    ]


@router.delete("/applications/{id}", status_code=204)
def delete_application(application_id: int):
    cursor = conn.cursor()

    # Ensures job exists
    cursor.execute("SELECT id FROM applications WHERE id=?", (application_id,))
    app_row = cursor.fetchone()
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")

    cursor.execute("DELETE FROM applications WHERE id=?", (application_id,))
    conn.commit()

    return


@router.put("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, application: ApplicationCreate):
    cursor = conn.cursor()

    # Ensures application exists
    cursor.execute("SELECT * FROM applications WHERE id=?", (application_id,))
    app_row = cursor.fetchone()
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update
    cursor.execute(
        """
        Update applications
        SET applicant_name=?, applicant_email=?
        WHERE id=?
        """,
        (application.applicant_name, application.applicant_email, application_id)
    )
    conn.commit()

    # Return updated application
    cursor.execute("SELECT * FROM applications WHERE id=?", (application_id,))
    updated_row = cursor.fetchone()

    return {
        "id": updated_row["id"],
        "job_id": updated_row["job_id"],
        "applicant_name": updated_row["applicant_name"],
        "applicant_email": updated_row["applicant_email"],
        "applied_at": updated_row["applied_at"]
    }
