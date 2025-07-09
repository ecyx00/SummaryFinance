import axios from 'axios';

// Temel API yapılandırması
const api = axios.create({
  baseURL: '/api', // Proxy ile http://localhost:8080/api'ye yönlendirilecek
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 saniye timeout
});

// Response interceptor - hata yönetimi
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API error:', error);
    return Promise.reject(error);
  }
);

// API fonksiyonları
export const fetchSummaries = () => api.get('/summaries');
export const fetchSummaryById = (id) => api.get(`/summary/${id}`);
export const submitFeedback = (feedback) => api.post('/feedback', feedback);

export default api;
