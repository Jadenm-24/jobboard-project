from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
