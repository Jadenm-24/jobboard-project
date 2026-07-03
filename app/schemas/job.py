from pydantic import BaseModel
from datetime import datetime


class JobCreated(BaseModel):
    title: str
    company: str
    location: str
    description: str


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    created_at: datetime

