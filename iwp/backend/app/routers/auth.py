"""
Simple authentication router for admin panel access.

For production, replace this with proper user management and password hashing.
This is a minimal implementation to prevent unauthorized access.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


# PRODUCTION: Move these to environment variables or database
# For now, simple hardcoded credentials
ADMIN_USERS = {
    "admin": "tradekings2026",  # Change this password in production!
    "supervisor": "supervisor123",
}


@router.post("/login")
def login(payload: LoginRequest):
    """Simple login endpoint - validates username/password."""
    if payload.username not in ADMIN_USERS:
        raise HTTPException(401, "Invalid username or password")
    
    if ADMIN_USERS[payload.username] != payload.password:
        raise HTTPException(401, "Invalid username or password")
    
    return {
        "status": "ok",
        "username": payload.username,
        "message": "Login successful"
    }
