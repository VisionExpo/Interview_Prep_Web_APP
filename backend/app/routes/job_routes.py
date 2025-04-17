from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..models.user import User
from ..utils.auth import get_current_user
from ..services.job_service import job_service, JobPosting
from uuid import UUID

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/recommendations", response_model=List[JobPosting])
async def get_job_recommendations(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized job recommendations based on user's skills and preferences
    """
    return await job_service.get_recommended_jobs(current_user.id, limit)

@router.post("/applications")
async def apply_to_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a job application
    """
    await job_service.save_job_application(
        user_id=current_user.id,
        job_id=job_id,
        status='applied'
    )
    return {"message": "Application submitted successfully"}

@router.get("/applications")
async def get_user_applications(
    current_user: User = Depends(get_current_user)
):
    """
    Get all job applications for the current user
    """
    return await job_service.get_user_applications(current_user.id)

@router.put("/applications/{application_id}")
async def update_application_status(
    application_id: UUID,
    status: str,
    current_user: User = Depends(get_current_user)
):
    """
    Update the status of a job application
    """
    await job_service.update_application_status(application_id, status)
    return {"message": "Application status updated successfully"}

@router.get("/search")
async def search_jobs(
    keywords: Optional[List[str]] = Query(None),
    location: Optional[str] = None,
    experience_level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Search for jobs with specific criteria
    """
    if not keywords:
        # If no keywords provided, use user's skills
        user_data = job_service.session.execute(
            "SELECT skills FROM users WHERE id = %s",
            (current_user.id,)
        ).one()
        keywords = user_data.skills if user_data else []
    
    # Fetch jobs from multiple sources
    linkedin_jobs = await job_service.fetch_linkedin_jobs(keywords, location or '')
    indeed_jobs = await job_service.fetch_indeed_jobs(keywords, location or '')
    
    all_jobs = linkedin_jobs + indeed_jobs
    
    # Filter by experience level if provided
    if experience_level:
        all_jobs = [
            job for job in all_jobs 
            if job.experience_level.lower() == experience_level.lower()
        ]
    
    return all_jobs