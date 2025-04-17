import speech_recognition as sr
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import os
import io
from typing import Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from ..db.connection import db

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.session = db.get_session()
        # Initialize Google Cloud Speech client
        self.client = speech_v1.SpeechClient()
        
    async def transcribe_audio(self, audio_file_path: str) -> Tuple[str, float]:
        """
        Transcribe audio file and return the text and confidence score
        """
        with io.open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
            
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
            enable_automatic_punctuation=True,
            enable_speaker_diarization=True,
            diarization_speaker_count=1
        )
        
        response = self.client.recognize(config=config, audio=audio)
        
        if not response.results:
            return "", 0.0
            
        transcript = response.results[0].alternatives[0].transcript
        confidence = response.results[0].alternatives[0].confidence
        
        return transcript, confidence
        
    async def save_voice_recording(
        self,
        user_id: UUID,
        question_id: UUID,
        audio_file_path: str,
        transcript: Optional[str] = None
    ) -> UUID:
        """
        Save voice recording metadata to database
        """
        recording_id = uuid4()
        
        self.session.execute("""
            INSERT INTO voice_recordings 
            (id, user_id, question_id, file_path, transcript, 
             created_at, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            recording_id,
            user_id,
            question_id,
            audio_file_path,
            transcript,
            datetime.now(),
            self._get_audio_duration(audio_file_path)
        ))
        
        return recording_id
        
    def _get_audio_duration(self, audio_file_path: str) -> float:
        """
        Get the duration of an audio file in seconds
        """
        with sr.AudioFile(audio_file_path) as source:
            audio = self.recognizer.record(source)
            return len(audio.frame_data) / audio.sample_rate
            
    async def analyze_interview_response(
        self,
        transcript: str,
        question_id: UUID
    ) -> dict:
        """
        Analyze the interview response for keywords and confidence
        """
        session = db.get_session()
        
        # Get question details
        question = session.execute(
            "SELECT * FROM interview_questions WHERE id = %s",
            (question_id,)
        ).one()
        
        if not question:
            return {
                "score": 0,
                "feedback": "Question not found",
                "keywords_mentioned": [],
                "missing_keywords": []
            }
            
        # Check for required keywords
        keywords_mentioned = []
        missing_keywords = []
        
        for keyword in question.keywords:
            if keyword.lower() in transcript.lower():
                keywords_mentioned.append(keyword)
            else:
                missing_keywords.append(keyword)
                
        # Calculate basic score based on keywords
        keyword_score = len(keywords_mentioned) / len(question.keywords) if question.keywords else 0
        
        # Generate feedback
        feedback = self._generate_feedback(
            keyword_score,
            keywords_mentioned,
            missing_keywords
        )
        
        return {
            "score": keyword_score,
            "feedback": feedback,
            "keywords_mentioned": keywords_mentioned,
            "missing_keywords": missing_keywords
        }
        
    def _generate_feedback(
        self,
        score: float,
        keywords_mentioned: list,
        missing_keywords: list
    ) -> str:
        """
        Generate feedback based on the interview response analysis
        """
        feedback = []
        
        if score >= 0.8:
            feedback.append("Excellent response! You covered most of the key points.")
        elif score >= 0.6:
            feedback.append("Good response, but there's room for improvement.")
        else:
            feedback.append("You might want to review this topic and try again.")
            
        if keywords_mentioned:
            feedback.append(f"You effectively mentioned: {', '.join(keywords_mentioned)}")
            
        if missing_keywords:
            feedback.append(
                f"Consider including these points in your answer: {', '.join(missing_keywords)}"
            )
            
        return " ".join(feedback)
        
    async def get_user_recordings(
        self,
        user_id: UUID,
        question_id: Optional[UUID] = None
    ) -> list:
        """
        Get user's voice recordings, optionally filtered by question
        """
        query = "SELECT * FROM voice_recordings WHERE user_id = %s"
        params = [user_id]
        
        if question_id:
            query += " AND question_id = %s"
            params.append(question_id)
            
        query += " ORDER BY created_at DESC"
        
        result = self.session.execute(query, params)
        return list(result)

voice_service = VoiceService()