from uuid import UUID, uuid4
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InterviewQuestion(BaseModel):
    id: UUID = uuid4()
    category: str
    difficulty: str
    title: str
    description: str
    sample_answer: str
    keywords: List[str] = []
    created_at: datetime = datetime.now()
    tags: List[str] = []
    company_tags: List[str] = []
    likes: int = 0
    views: int = 0

class UserAnswer(BaseModel):
    id: UUID = uuid4()
    user_id: UUID
    question_id: UUID
    answer_text: str
    voice_recording_url: Optional[str]
    feedback: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime]
    
class QuestionProgress(BaseModel):
    user_id: UUID
    question_id: UUID
    status: str  # 'not_started', 'in_progress', 'completed'
    attempts: int = 0
    last_attempt_date: Optional[datetime]
    mastery_level: float = 0.0  # 0 to 1.0
    notes: Optional[str]