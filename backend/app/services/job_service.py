from typing import List, Optional
import requests
from pydantic import BaseModel
from datetime import datetime
import os
from ..db.connection import db
from uuid import UUID, uuid4

class JobPosting(BaseModel):
    id: UUID = uuid4()
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    salary_range: Optional[str]
    posting_url: str
    source: str
    posted_date: datetime
    skills_required: List[str]
    experience_level: str

class JobService:
    def __init__(self):
        self.session = db.get_session()
        self.linkedin_api_key = os.getenv('LINKEDIN_API_KEY')
        self.indeed_api_key = os.getenv('INDEED_API_KEY')
        self.glassdoor_api_key = os.getenv('GLASSDOOR_API_KEY')

    async def fetch_linkedin_jobs(self, keywords: List[str], location: str) -> List[JobPosting]:
        # Implementation for LinkedIn Jobs API
        headers = {'Authorization': f'Bearer {self.linkedin_api_key}'}
        response = requests.get(
            'https://api.linkedin.com/v2/jobs',
            headers=headers,
            params={
                'keywords': ','.join(keywords),
                'location': location
            }
        )
        jobs = []
        if response.status_code == 200:
            for job in response.json().get('elements', []):
                jobs.append(JobPosting(
                    title=job['title'],
                    company=job['company']['name'],
                    location=job['location'],
                    description=job['description'],
                    requirements=job.get('requirements', []),
                    posting_url=job['applicationUrl'],
                    source='linkedin',
                    posted_date=datetime.fromtimestamp(job['postedAt']/1000),
                    skills_required=job.get('skills', []),
                    experience_level=job.get('experienceLevel', '')
                ))
        return jobs

    async def fetch_indeed_jobs(self, keywords: List[str], location: str) -> List[JobPosting]:
        # Implementation for Indeed Jobs API
        headers = {'Authorization': f'Bearer {self.indeed_api_key}'}
        response = requests.get(
            'https://api.indeed.com/v2/jobs',
            headers=headers,
            params={
                'q': ' '.join(keywords),
                'l': location
            }
        )
        jobs = []
        if response.status_code == 200:
            for job in response.json().get('results', []):
                jobs.append(JobPosting(
                    title=job['title'],
                    company=job['company'],
                    location=job['location'],
                    description=job['description'],
                    posting_url=job['url'],
                    source='indeed',
                    posted_date=datetime.fromisoformat(job['date']),
                    skills_required=self._extract_skills(job['description']),
                    experience_level=self._extract_experience_level(job['description'])
                ))
        return jobs

    async def get_recommended_jobs(self, user_id: UUID, limit: int = 10) -> List[JobPosting]:
        # Get user's skills and preferences
        user_data = self.session.execute(
            "SELECT skills, preferences FROM users WHERE id = %s",
            (user_id,)
        ).one()
        
        if not user_data:
            return []
        
        user_skills = user_data.skills
        preferences = user_data.preferences
        location = preferences.get('preferred_location', '')
        
        # Fetch jobs from multiple sources
        linkedin_jobs = await self.fetch_linkedin_jobs(user_skills, location)
        indeed_jobs = await self.fetch_indeed_jobs(user_skills, location)
        
        # Combine and sort jobs by relevance
        all_jobs = linkedin_jobs + indeed_jobs
        return self._sort_jobs_by_relevance(all_jobs, user_skills)[:limit]

    def _sort_jobs_by_relevance(self, jobs: List[JobPosting], user_skills: List[str]) -> List[JobPosting]:
        def calculate_relevance(job):
            skill_match = sum(1 for skill in user_skills if any(
                skill.lower() in req.lower() for req in job.skills_required
            ))
            return skill_match
        
        return sorted(jobs, key=calculate_relevance, reverse=True)

    def _extract_skills(self, description: str) -> List[str]:
        # Basic skill extraction logic
        common_skills = ['python', 'java', 'javascript', 'react', 'node.js', 'sql',
                        'aws', 'docker', 'kubernetes', 'machine learning']
        return [skill for skill in common_skills if skill.lower() in description.lower()]

    def _extract_experience_level(self, description: str) -> str:
        # Basic experience level extraction logic
        if 'senior' in description.lower():
            return 'senior'
        elif 'junior' in description.lower():
            return 'junior'
        return 'mid-level'

    async def save_job_application(self, user_id: UUID, job_id: UUID, status: str):
        self.session.execute("""
            INSERT INTO job_applications 
            (id, user_id, job_id, status, applied_date, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            uuid4(),
            user_id,
            job_id,
            status,
            datetime.now(),
            datetime.now()
        ))

    async def update_application_status(self, application_id: UUID, new_status: str):
        self.session.execute("""
            UPDATE job_applications 
            SET status = %s, last_updated = %s
            WHERE id = %s
        """, (new_status, datetime.now(), application_id))

    async def get_user_applications(self, user_id: UUID) -> List[dict]:
        result = self.session.execute("""
            SELECT * FROM job_applications 
            WHERE user_id = %s 
            ORDER BY applied_date DESC
        """, (user_id,))
        return list(result)

job_service = JobService()