from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageDelete(BaseModel):
    message_id: int