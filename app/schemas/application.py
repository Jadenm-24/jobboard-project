from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    applicant_name: str
    applicant_email: str


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    applicant_name: str
    applicant_email: str
    applied_at: datetime
