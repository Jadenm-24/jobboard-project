from app.database import conn, delete_expired_refresh_tokens
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.auth import authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, SECRET_KEY, ALGORITHM, create_access_token, oauth2_scheme
from datetime import datetime, timezone
from jose import JWTError, jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={
            "sub": user["email"],
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token()

    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=7)
    ).isoformat()

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO refresh_tokens (user_id, token,  expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user["id"],
            refresh_token,
            expires_at,
            datetime.now(timezone.utc).isoformat(),
        )
    )
    conn.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get user id
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Revoke all refresh tokens
        cursor.execute(
            "UPDATE refresh_tokens SET revoked=1 WHERE user_id=?",
            (user["id"],)
        )
        conn.commit()

        return {"message": "Logged out successfully"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/refresh")
def refresh_access_token(refresh_token: str):
    cursor = conn.cursor()

    cursor = conn.cursor(
        """
        SELECT user_id, expires_at
        FROM refresh_tokens
        WHERE token=?
        """,
        (refresh_token,)
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Get user info
    cursor.execute(
        "SELECT email, role FROM users WHERE id=?",
        (row["user_id"],)
    )
    user = cursor.fetchone()

    access_token = create_access_token(
        data={"sub": user["email"],
              "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(refresh_token: str):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM refresh_tokens WHERE token=?",
        (refresh_token,)
    )
    conn.commit()
    return {"detail": "Logged out"}


@router.post("/refresh")
def refresh_token(token: str = Depends(oauth2_scheme)):

    delete_expired_refresh_tokens()

    cursor = conn.cursor()

    # Looks up refresh token in DB
    cursor.execute(
        """
        SELECT rt.token, rt.expires_at, rt.revoke, u.id, u.email, u.role
        FROM refresh_tokens rt
        JOIN users u ON rt.user_id = u.id
        WHERE rt.token = ?
        """,
        (refresh_token,)
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if row["revoked"]:
        raise HTTPException(status_code=401, detail="Token revoked")

    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Creating new access token
    access_token = create_access_token(
        data={
            "sub": row["email"],
            "role": row["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
