from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    
class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: UUID = uuid4()
    hashed_password: str
    created_at: datetime = datetime.now()
    is_active: bool = True
    skills: List[str] = []
    progress: dict = {}
    preferences: dict = {}

class User(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    skills: List[str]
    progress: dict
    preferences: dict

    class Config:
        from_attributes = True