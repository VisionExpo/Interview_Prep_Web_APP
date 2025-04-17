from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.user import UserCreate, User, UserInDB
from ..utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    Token
)
from ..db.connection import db
from datetime import timedelta
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    session = db.get_session()
    
    # Check if user exists
    result = session.execute(
        "SELECT * FROM users WHERE email = %s", 
        (user.email,)
    )
    if result.one():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    user_in_db = UserInDB(
        **user.dict(),
        hashed_password=get_password_hash(user.password)
    )
    
    # Insert into database
    session.execute("""
        INSERT INTO users (id, email, username, full_name, hashed_password, 
                         created_at, is_active, skills, progress, preferences)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_in_db.id,
        user_in_db.email,
        user_in_db.username,
        user_in_db.full_name,
        user_in_db.hashed_password,
        user_in_db.created_at,
        user_in_db.is_active,
        user_in_db.skills,
        user_in_db.progress,
        user_in_db.preferences
    ))
    
    return User(**user_in_db.dict(exclude={'hashed_password'}))

@router.post("/token", response_model=Token)
async def login(username: str, password: str):
    session = db.get_session()
    user = session.execute(
        "SELECT * FROM users WHERE username = %s", 
        (username,)
    ).one()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=User)
async def update_user(
    user_update: UserCreate,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    
    # Update user in database
    session.execute("""
        UPDATE users 
        SET email = %s, username = %s, full_name = %s
        WHERE id = %s
    """, (
        user_update.email,
        user_update.username,
        user_update.full_name,
        current_user.id
    ))
    
    return User(**{**current_user.dict(), **user_update.dict(exclude={'password'})})

@router.put("/me/skills")
async def update_skills(
    skills: List[str],
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    session.execute(
        "UPDATE users SET skills = %s WHERE id = %s",
        (skills, current_user.id)
    )
    return {"message": "Skills updated successfully"}

@router.get("/me/progress")
async def get_progress(current_user: User = Depends(get_current_user)):
    session = db.get_session()
    result = session.execute(
        "SELECT progress FROM users WHERE id = %s",
        (current_user.id,)
    ).one()
    return result.progress if result else {}