import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API endpoints
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/users/token', { username, password }),
  register: (userData: any) =>
    api.post('/users/register', userData),
  getProfile: () =>
    api.get('/users/me'),
  updateProfile: (userData: any) =>
    api.put('/users/me', userData),
};

export const interviewAPI = {
  getQuestions: (params?: any) =>
    api.get('/interview/questions', { params }),
  submitAnswer: (answer: any) =>
    api.post('/interview/answers', answer),
  getProgress: () =>
    api.get('/interview/progress'),
  likeQuestion: (questionId: string) =>
    api.post(`/interview/questions/${questionId}/like`),
};

export const mediaAPI = {
  uploadFile: (formData: FormData) =>
    api.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  getFiles: (params?: any) =>
    api.get('/media/files', { params }),
  getFile: (fileId: string) =>
    api.get(`/media/files/${fileId}`),
  deleteFile: (fileId: string) =>
    api.delete(`/media/files/${fileId}`),
};

export const jobAPI = {
  getRecommendations: (params?: any) =>
    api.get('/jobs/recommendations', { params }),
  searchJobs: (params?: any) =>
    api.get('/jobs/search', { params }),
  applyToJob: (jobId: string) =>
    api.post('/jobs/applications', { job_id: jobId }),
  getApplications: () =>
    api.get('/jobs/applications'),
  updateApplicationStatus: (applicationId: string, status: string) =>
    api.put(`/jobs/applications/${applicationId}`, { status }),
};

export const voiceAPI = {
  submitRecording: (formData: FormData) =>
    api.post('/interview/voice-response', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  getRecordings: (questionId?: string) =>
    api.get('/interview/recordings', {
      params: questionId ? { question_id: questionId } : undefined,
    }),
};

export const progressAPI = {
  getStatistics: () =>
    api.get('/users/me/progress'),
  getStudyPlan: () =>
    api.get('/users/me/study-plan'),
  updateMastery: (questionId: string, score: number) =>
    api.post('/interview/progress', { question_id: questionId, score }),
};

export default api;