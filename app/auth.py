import os
import secrets
from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from app.database import conn
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_refresh_token():
    return secrets.token_hex(32)


def store_refresh_token(user_id: int, token: str, expires_at: datetime):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO refresh_tokens (user_id, token, expires_at, revoked, created_at)
        VALUES (?, ?, ?, 0, ?)
        """,
        (
            user_id,
            token,
            expires_at.isoformat(),
            datetime.now(timezone.utc).isoformat(),
        )
    )
    conn.commit()


# Decodes the JWT token & returns the current user as a dictionary
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, role FROM users WHERE email=",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_email(email: str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, hashed_password FROM users WHERE email=?",
        (email,)
    )
    row = cursor.fetchone()
    return row


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    return user


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (email, hashed_password, role) Values (?, ?, ?)",
            (user.email, hashed_password, "user")
        )
        conn.commit()
        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "email": user.email,
            "role": "user"
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"User already exists or invalid data: {e}"
        )
