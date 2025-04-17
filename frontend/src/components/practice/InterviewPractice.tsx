import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import { School, QueryStats, Mic } from '@mui/icons-material';
import { interviewAPI, progressAPI } from '../../services/api';

interface Question {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  likes: number;
}

interface StudyPlan {
  focus_areas: Array<{
    category: string;
    current_score: number;
    recommended_practice_time: string;
  }>;
  recommended_questions: Question[];
  daily_goals: string[];
}

export const InterviewPractice: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [questionsRes, studyPlanRes] = await Promise.all([
          interviewAPI.getQuestions(),
          progressAPI.getStudyPlan(),
        ]);
        setQuestions(questionsRes.data);
        setStudyPlan(studyPlanRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        {/* Study Plan Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <School sx={{ mr: 1 }} /> Today's Study Plan
            </Typography>
            <Grid container spacing={2}>
              {studyPlan?.focus_areas.map((area, index) => (
                <Grid item xs={12} md={4} key={index}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Focus Area
                      </Typography>
                      <Typography variant="h6">{area.category}</Typography>
                      <Typography variant="body2">
                        Current Score: {Math.round(area.current_score * 100)}%
                      </Typography>
                      <Typography variant="body2">
                        Recommended Practice: {area.recommended_practice_time}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Practice Questions Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <QueryStats sx={{ mr: 1 }} /> Recommended Questions
            </Typography>
            <Grid container spacing={2}>
              {questions.map((question) => (
                <Grid item xs={12} md={6} key={question.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{question.title}</Typography>
                      <Box sx={{ mt: 1, mb: 1 }}>
                        <Chip 
                          label={question.category} 
                          color="primary" 
                          size="small" 
                          sx={{ mr: 1 }}
                        />
                        <Chip 
                          label={question.difficulty} 
                          color={
                            question.difficulty === 'Easy' ? 'success' :
                            question.difficulty === 'Medium' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary">
                        {question.likes} people found this helpful
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button size="small" color="primary">
                        Practice
                      </Button>
                      <Button 
                        size="small" 
                        startIcon={<Mic />}
                        color="secondary"
                      >
                        Voice Practice
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};