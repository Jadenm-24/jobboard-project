from fastapi import APIRouter, HTTPException, status, Depends
from app.database import conn
from app.auth import get_password_hash, get_current_user
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):

    cursor = conn.cursor()

    hashed_password = get_password_hash(user.password)

    try:
        cursor.execute(
            """
            INSERT INTO users (email, hashed_password, role)
            VALUES (?, ?, ?)
            """,
            (
                user.usernme,
                hashed_password,
                user.role or "user",
            ),
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"User already exists or invalid data: {e}"
        )

    user_id = cursor.lastrowid

    return {
        "id": user_id,
        "username": user.username,
        "role": user.role or "user"
    }


@router.get("/", response_model=list[UserResponse])
def list_users(current_user: dict = Depends(get_current_user)):

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users"
        )

    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    rows = cursor.fetall()

    return [
        {"id": row["id"], "username": row["username"], "role": row["role"]}
        for row in rows
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE ud=?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] != "admin" and current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    return {"id": row["id"], "username": row["username"], "role": row["role"]}
