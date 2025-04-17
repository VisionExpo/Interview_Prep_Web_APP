import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  InputAdornment,
  MenuItem,
} from '@mui/material';
import {
  Search,
  LocationOn,
  Work,
  BookmarkBorder,
  Bookmark,
  Share,
} from '@mui/icons-material';
import { jobAPI } from '../../services/api';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  salary_range?: string;
  posting_url: string;
  skills_required: string[];
  experience_level: string;
}

interface Application {
  id: string;
  job_id: string;
  status: string;
  applied_date: string;
}

export const JobSearch: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showJobDetails, setShowJobDetails] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [jobsRes, applicationsRes] = await Promise.all([
          jobAPI.getRecommendations(),
          jobAPI.getApplications(),
        ]);
        setJobs(jobsRes.data);
        setApplications(applicationsRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await jobAPI.searchJobs({
        keywords: searchQuery ? searchQuery.split(',').map(k => k.trim()) : undefined,
        location,
        experience_level: experienceLevel,
      });
      setJobs(response.data);
    } catch (error) {
      console.error('Error searching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (jobId: string) => {
    try {
      await jobAPI.applyToJob(jobId);
      const response = await jobAPI.getApplications();
      setApplications(response.data);
    } catch (error) {
      console.error('Error applying to job:', error);
    }
  };

  const isApplied = (jobId: string) => {
    return applications.some(app => app.job_id === jobId);
  };

  const experienceLevels = ['Entry Level', 'Mid Level', 'Senior Level', 'Lead', 'Manager'];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Search Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search Jobs"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LocationOn />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              select
              label="Experience Level"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
            >
              {experienceLevels.map((level) => (
                <MenuItem key={level} value={level}>
                  {level}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              sx={{ height: '100%' }}
            >
              Search
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Jobs List */}
      <Grid container spacing={2}>
        {loading ? (
          <Box display="flex" justifyContent="center" width="100%" mt={4}>
            <CircularProgress />
          </Box>
        ) : (
          jobs.map((job) => (
            <Grid item xs={12} md={6} key={job.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {job.title}
                  </Typography>
                  <Typography color="textSecondary" gutterBottom>
                    {job.company} • {job.location}
                  </Typography>
                  {job.salary_range && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {job.salary_range}
                    </Typography>
                  )}
                  <Box sx={{ mt: 1, mb: 1 }}>
                    {job.skills_required.map((skill, index) => (
                      <Chip
                        key={index}
                        label={skill}
                        size="small"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    color="primary"
                    onClick={() => {
                      setSelectedJob(job);
                      setShowJobDetails(true);
                    }}
                  >
                    View Details
                  </Button>
                  <Button
                    size="small"
                    color="secondary"
                    disabled={isApplied(job.id)}
                    onClick={() => handleApply(job.id)}
                  >
                    {isApplied(job.id) ? 'Applied' : 'Apply'}
                  </Button>
                  <IconButton size="small">
                    <Share />
                  </IconButton>
                  <IconButton size="small">
                    {isApplied(job.id) ? <Bookmark /> : <BookmarkBorder />}
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Job Details Dialog */}
      <Dialog
        open={showJobDetails}
        onClose={() => setShowJobDetails(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedJob && (
          <>
            <DialogTitle>
              {selectedJob.title}
            </DialogTitle>
            <DialogContent>
              <Typography variant="subtitle1" gutterBottom>
                {selectedJob.company} • {selectedJob.location}
              </Typography>
              {selectedJob.salary_range && (
                <Typography variant="subtitle2" gutterBottom>
                  Salary Range: {selectedJob.salary_range}
                </Typography>
              )}
              <Typography variant="body1" paragraph>
                {selectedJob.description}
              </Typography>
              <Typography variant="h6" gutterBottom>
                Requirements
              </Typography>
              <ul>
                {selectedJob.requirements.map((req, index) => (
                  <Typography component="li" key={index}>
                    {req}
                  </Typography>
                ))}
              </ul>
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Required Skills
                </Typography>
                {selectedJob.skills_required.map((skill, index) => (
                  <Chip
                    key={index}
                    label={skill}
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowJobDetails(false)}>
                Close
              </Button>
              <Button
                variant="contained"
                color="primary"
                disabled={isApplied(selectedJob.id)}
                onClick={() => {
                  handleApply(selectedJob.id);
                  setShowJobDetails(false);
                }}
              >
                {isApplied(selectedJob.id) ? 'Applied' : 'Apply Now'}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};