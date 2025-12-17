from pydantic import BaseModel, EmailStr, Field
from datetime import date


### SCHEMAS FOR USERS

class UserRegister(BaseModel):
    """pydantic class for registration"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr


### SCHEMAS FOR NOTES

class NoteCreate(BaseModel):
    note_text: str
    note_date: date


class NoteUpdate(BaseModel):
    note_text: str


class NoteOut(BaseModel):
    note_id: int
    note_text: str
    note_date: date


class StatusOut(BaseModel):
    status: bool


# SCHEMAS FOR TOKENS

class LoginSchema(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRotation(BaseModel):
    refresh_token: str