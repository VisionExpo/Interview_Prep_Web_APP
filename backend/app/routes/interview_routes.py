from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..models.question import InterviewQuestion, UserAnswer, QuestionProgress
from ..models.user import User
from ..utils.auth import get_current_user
from ..db.connection import db
from uuid import UUID

router = APIRouter(prefix="/interview", tags=["interview"])

@router.post("/questions", response_model=InterviewQuestion)
async def create_question(
    question: InterviewQuestion,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    session.execute("""
        INSERT INTO interview_questions 
        (id, category, difficulty, title, description, sample_answer, 
         keywords, created_at, tags, company_tags, likes, views)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        question.id,
        question.category,
        question.difficulty,
        question.title,
        question.description,
        question.sample_answer,
        question.keywords,
        question.created_at,
        question.tags,
        question.company_tags,
        question.likes,
        question.views
    ))
    return question

@router.get("/questions", response_model=List[InterviewQuestion])
async def get_questions(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    tag: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    query = "SELECT * FROM interview_questions"
    conditions = []
    params = []
    
    if category:
        conditions.append("category = %s")
        params.append(category)
    if difficulty:
        conditions.append("difficulty = %s")
        params.append(difficulty)
    if tag:
        conditions.append("%s = ANY(tags)")
        params.append(tag)
    if company:
        conditions.append("%s = ANY(company_tags)")
        params.append(company)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {limit}"
    
    result = session.execute(query, params)
    return [InterviewQuestion(**row) for row in result]

@router.post("/answers", response_model=UserAnswer)
async def submit_answer(
    answer: UserAnswer,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    
    # Verify question exists
    question = session.execute(
        "SELECT * FROM interview_questions WHERE id = %s",
        (answer.question_id,)
    ).one()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Store the answer
    session.execute("""
        INSERT INTO user_answers 
        (id, user_id, question_id, answer_text, voice_recording_url,
         feedback, confidence_score, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        answer.id,
        current_user.id,
        answer.question_id,
        answer.answer_text,
        answer.voice_recording_url,
        answer.feedback,
        answer.confidence_score,
        answer.created_at
    ))
    
    # Update progress
    progress = session.execute("""
        SELECT * FROM question_progress 
        WHERE user_id = %s AND question_id = %s
    """, (current_user.id, answer.question_id)).one()
    
    if progress:
        session.execute("""
            UPDATE question_progress 
            SET attempts = attempts + 1,
                last_attempt_date = %s
            WHERE user_id = %s AND question_id = %s
        """, (answer.created_at, current_user.id, answer.question_id))
    else:
        session.execute("""
            INSERT INTO question_progress 
            (user_id, question_id, status, attempts, last_attempt_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            current_user.id,
            answer.question_id,
            'in_progress',
            1,
            answer.created_at
        ))
    
    return answer

@router.get("/progress", response_model=List[QuestionProgress])
async def get_user_progress(
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    result = session.execute(
        "SELECT * FROM question_progress WHERE user_id = %s",
        (current_user.id,)
    )
    return [QuestionProgress(**row) for row in result]

@router.post("/questions/{question_id}/like")
async def like_question(
    question_id: UUID,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    session.execute(
        "UPDATE interview_questions SET likes = likes + 1 WHERE id = %s",
        (question_id,)
    )
    return {"message": "Question liked successfully"}