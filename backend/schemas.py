from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """pydantic class for registration"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: int
    email: EmailStr