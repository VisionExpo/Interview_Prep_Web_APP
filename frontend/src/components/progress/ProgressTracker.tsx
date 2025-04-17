import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  LinearProgress,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  AccessTime,
  Grade,
  Info,
} from '@mui/icons-material';
import { progressAPI } from '../../services/api';

interface Statistics {
  total_questions_attempted: number;
  questions_completed: number;
  average_confidence_score: number;
  weekly_progress: Array<{
    week: string;
    questions_attempted: number;
    average_score: number;
  }>;
  category_performance: {
    [key: string]: {
      questions_attempted: number;
      average_score: number;
    };
  };
  strength_areas: string[];
  weak_areas: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const ProgressTracker: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Statistics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        const response = await progressAPI.getStatistics();
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching statistics:', error);
        setError('Failed to load progress data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatistics();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Typography color="error" variant="h6">
          {error}
        </Typography>
      </Box>
    );
  }

  const categoryData = stats ? Object.entries(stats.category_performance).map(
    ([category, data], index) => ({
      category,
      score: data.average_score * 100,
      questions: data.questions_attempted,
      color: COLORS[index % COLORS.length],
    })
  ) : [];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Questions Attempted
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_questions_attempted}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <TrendingUp color="primary" />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {stats?.questions_completed} completed
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Average Score
                  </Typography>
                  <Typography variant="h4">
                    {Math.round(stats?.average_confidence_score * 100)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={stats?.average_confidence_score * 100 || 0}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Strengths
                  </Typography>
                  {stats?.strength_areas.map((area, index) => (
                    <Typography key={index} variant="body2">
                      • {area}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Weekly Progress Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Weekly Progress
              <Tooltip title="Shows your progress over the past weeks">
                <IconButton size="small">
                  <Info />
                </IconButton>
              </Tooltip>
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer>
                <BarChart data={stats?.weekly_progress}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="questions_attempted" fill="#8884d8" name="Questions" />
                  <Bar dataKey="average_score" fill="#82ca9d" name="Score" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Category Performance */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Category Performance
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="questions"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Areas for Improvement */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Areas for Improvement
            </Typography>
            {stats?.weak_areas.map((area, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Typography variant="body1" gutterBottom>
                  {area}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={100 - (index + 1) * 20}
                  color="warning"
                />
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};