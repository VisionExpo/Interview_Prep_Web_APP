from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
from ..db.connection import db
from collections import defaultdict

class ProgressService:
    def __init__(self):
        self.session = db.get_session()

    async def get_user_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics about user's interview preparation"""
        # Get all user answers
        answers = self.session.execute("""
            SELECT * FROM user_answers 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        # Get all question progress
        progress = self.session.execute("""
            SELECT * FROM question_progress 
            WHERE user_id = %s
        """, (user_id,))
        
        stats = {
            "total_questions_attempted": 0,
            "questions_completed": 0,
            "average_confidence_score": 0.0,
            "practice_sessions": 0,
            "total_practice_time": 0,
            "strength_areas": [],
            "weak_areas": [],
            "recent_activity": [],
            "weekly_progress": self._get_weekly_progress(answers),
            "category_performance": self._get_category_performance(answers),
        }
        
        confidence_scores = []
        
        for answer in answers:
            stats["total_questions_attempted"] += 1
            if answer.confidence_score:
                confidence_scores.append(answer.confidence_score)
            
        for prog in progress:
            if prog.status == 'completed':
                stats["questions_completed"] += 1
                
        if confidence_scores:
            stats["average_confidence_score"] = sum(confidence_scores) / len(confidence_scores)
            
        return stats

    def _get_weekly_progress(self, answers) -> List[Dict]:
        """Calculate weekly progress metrics"""
        weekly_data = defaultdict(lambda: {
            "questions_attempted": 0,
            "average_score": 0.0,
            "scores": []
        })
        
        for answer in answers:
            week_start = answer.created_at.date() - timedelta(days=answer.created_at.weekday())
            weekly_data[week_start]["questions_attempted"] += 1
            if answer.confidence_score:
                weekly_data[week_start]["scores"].append(answer.confidence_score)
                
        # Calculate averages
        for week_data in weekly_data.values():
            if week_data["scores"]:
                week_data["average_score"] = sum(week_data["scores"]) / len(week_data["scores"])
            del week_data["scores"]  # Remove raw scores from output
            
        return [{"week": week, **data} for week, data in weekly_data.items()]

    def _get_category_performance(self, answers) -> Dict[str, dict]:
        """Calculate performance metrics by question category"""
        categories = defaultdict(lambda: {
            "questions_attempted": 0,
            "average_score": 0.0,
            "scores": []
        })
        
        for answer in answers:
            question = self.session.execute(
                "SELECT category FROM interview_questions WHERE id = %s",
                (answer.question_id,)
            ).one()
            
            if question:
                categories[question.category]["questions_attempted"] += 1
                if answer.confidence_score:
                    categories[question.category]["scores"].append(answer.confidence_score)
                    
        # Calculate averages and remove raw scores
        for category_data in categories.values():
            if category_data["scores"]:
                category_data["average_score"] = sum(category_data["scores"]) / len(category_data["scores"])
            del category_data["scores"]
            
        return dict(categories)

    async def get_recommended_questions(self, user_id: UUID, limit: int = 5) -> List[dict]:
        """Get personalized question recommendations based on user's performance"""
        # Get user's weak areas
        stats = await self.get_user_statistics(user_id)
        category_performance = stats["category_performance"]
        
        # Sort categories by performance
        sorted_categories = sorted(
            category_performance.items(),
            key=lambda x: x[1]["average_score"]
        )
        
        recommended_questions = []
        
        for category, _ in sorted_categories:
            if len(recommended_questions) >= limit:
                break
                
            # Get questions from this category that the user hasn't attempted
            questions = self.session.execute("""
                SELECT q.* FROM interview_questions q
                LEFT JOIN question_progress p 
                ON p.question_id = q.id AND p.user_id = %s
                WHERE q.category = %s AND p.id IS NULL
                LIMIT %s
            """, (user_id, category, limit - len(recommended_questions)))
            
            recommended_questions.extend(questions)
            
        return recommended_questions

    async def update_mastery_level(
        self,
        user_id: UUID,
        question_id: UUID,
        confidence_score: float
    ):
        """Update mastery level for a question based on user's performance"""
        current_progress = self.session.execute("""
            SELECT * FROM question_progress 
            WHERE user_id = %s AND question_id = %s
        """, (user_id, question_id)).one()
        
        if current_progress:
            # Update existing progress
            new_mastery = (current_progress.mastery_level * current_progress.attempts + confidence_score) / (current_progress.attempts + 1)
            
            self.session.execute("""
                UPDATE question_progress 
                SET mastery_level = %s,
                    attempts = attempts + 1,
                    last_attempt_date = %s
                WHERE user_id = %s AND question_id = %s
            """, (new_mastery, datetime.now(), user_id, question_id))
        else:
            # Create new progress entry
            self.session.execute("""
                INSERT INTO question_progress 
                (user_id, question_id, status, attempts, mastery_level, last_attempt_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                question_id,
                'in_progress',
                1,
                confidence_score,
                datetime.now()
            ))

    async def get_study_plan(self, user_id: UUID) -> dict:
        """Generate a personalized study plan based on user's progress"""
        stats = await self.get_user_statistics(user_id)
        weak_categories = sorted(
            stats["category_performance"].items(),
            key=lambda x: x[1]["average_score"]
        )[:3]  # Focus on top 3 weak areas
        
        recommended_questions = await self.get_recommended_questions(user_id, limit=10)
        
        return {
            "focus_areas": [
                {
                    "category": category,
                    "current_score": data["average_score"],
                    "recommended_practice_time": "30 minutes" if data["average_score"] < 0.6 else "15 minutes"
                }
                for category, data in weak_categories
            ],
            "recommended_questions": recommended_questions,
            "daily_goals": [
                f"Practice {len(weak_categories)} questions from your weak areas",
                "Review previous answers and feedback",
                "Update your progress tracking"
            ],
            "estimated_improvement_time": self._calculate_improvement_time(stats)
        }
    
    def _calculate_improvement_time(self, stats: dict) -> str:
        """Estimate time needed for significant improvement based on current progress"""
        avg_score = stats["average_confidence_score"]
        if avg_score > 0.8:
            return "1-2 weeks"
        elif avg_score > 0.6:
            return "2-3 weeks"
        else:
            return "4-6 weeks"

progress_service = ProgressService()