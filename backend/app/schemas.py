from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class CandidateCreate(BaseModel):
    name: str
    email: str
    role_applied: str
    skills: List[str] = []

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role_applied: Optional[str] = None
    status: Optional[str] = None
    skills: Optional[List[str]] = None
    internal_notes: Optional[str] = None

class ScoreCreate(BaseModel):
    category: str
    score: int = Field(ge=1, le=5)
    note: Optional[str] = ""

class ScoreResponse(BaseModel):
    id: int
    candidate_id: int
    category: str
    score: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    note: str
    created_at: str

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    role_applied: str
    status: str
    skills: List[str]
    internal_notes: Optional[str] = None
    created_at: str

class CandidateDetailResponse(CandidateResponse):
    scores: List[ScoreResponse] = []
    ai_summary: Optional[str] = None

class SummaryResponse(BaseModel):
    summary: str

class PaginatedResponse(BaseModel):
    items: List[CandidateResponse]
    total: int
    page: int
    page_size: int
    next_offset: Optional[int] = None
