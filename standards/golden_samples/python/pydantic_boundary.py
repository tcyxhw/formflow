"""
模块用途: 边界 schema 正例
"""

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str
    age: int = Field(ge=0, le=150)


class CreateUserResponse(BaseModel):
    id: str
    username: str
    email: str
