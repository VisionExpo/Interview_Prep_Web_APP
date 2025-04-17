import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Chip,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Mic,
  Stop,
  PlayArrow,
  ThumbUp,
  Timer,
  Save,
} from '@mui/icons-material';
import { interviewAPI, voiceAPI } from '../../services/api';

interface QuestionPracticeProps {
  questionId: string;
  onComplete: () => void;
}

interface Question {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  keywords: string[];
}

export const QuestionPractice: React.FC<QuestionPracticeProps> = ({
  questionId,
  onComplete,
}) => {
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [timer, setTimer] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        const response = await interviewAPI.getQuestions({ id: questionId });
        setQuestion(response.data);
      } catch (error) {
        console.error('Error fetching question:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchQuestion();
  }, [questionId]);

  useEffect(() => {
    if (isRecording) {
      timerIntervalRef.current = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerIntervalRef.current);
    }

    return () => clearInterval(timerIntervalRef.current);
  }, [isRecording]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setTimer(0);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      const formData = new FormData();
      if (audioUrl) {
        const audioBlob = await fetch(audioUrl).then(r => r.blob());
        formData.append('audio', audioBlob);
      }
      
      formData.append('answer_text', answer);
      formData.append('question_id', questionId);

      const response = await interviewAPI.submitAnswer(formData);
      setFeedback(response.data.feedback);
      setShowFeedback(true);
    } catch (error) {
      console.error('Error submitting answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    try {
      await interviewAPI.likeQuestion(questionId);
    } catch (error) {
      console.error('Error liking question:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        {/* Question Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            {question?.title}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
            <Chip label={question?.category} color="primary" />
            <Chip label={question?.difficulty} 
              color={
                question?.difficulty === 'Easy' ? 'success' :
                question?.difficulty === 'Medium' ? 'warning' : 'error'
              }
            />
            <IconButton onClick={handleLike} color="primary">
              <ThumbUp />
            </IconButton>
          </Stack>
          <Typography variant="body1">
            {question?.description}
          </Typography>
        </Box>

        {/* Recording Controls */}
        <Box sx={{ mb: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            {!isRecording ? (
              <Button
                startIcon={<Mic />}
                variant="contained"
                color="secondary"
                onClick={startRecording}
                disabled={loading}
              >
                Start Recording
              </Button>
            ) : (
              <Button
                startIcon={<Stop />}
                variant="contained"
                color="error"
                onClick={stopRecording}
              >
                Stop Recording
              </Button>
            )}
            {timer > 0 && (
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <Timer sx={{ mr: 1 }} />
                {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}
              </Typography>
            )}
          </Stack>
          {audioUrl && (
            <Box sx={{ mt: 2 }}>
              <audio controls src={audioUrl} />
            </Box>
          )}
        </Box>

        {/* Text Answer */}
        <TextField
          fullWidth
          multiline
          rows={6}
          variant="outlined"
          label="Your Answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          sx={{ mb: 3 }}
        />

        <Button
          fullWidth
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={loading || (!answer && !audioUrl)}
          startIcon={<Save />}
        >
          Submit Answer
        </Button>

        {/* Feedback Dialog */}
        <Dialog
          open={showFeedback}
          onClose={() => {
            setShowFeedback(false);
            onComplete();
          }}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Feedback on Your Answer</DialogTitle>
          <DialogContent>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
              {feedback}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setShowFeedback(false);
              onComplete();
            }}>
              Close
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Box>
  );
};