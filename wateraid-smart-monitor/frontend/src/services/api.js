import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token expiry — auto-refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ---------- API modules ----------
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (data) => api.post('/auth/register/', data),
  me: () => api.get('/auth/me/'),
};

export const sectorAPI = {
  list: (params) => api.get('/sectors/', { params }),
  get: (id) => api.get(`/sectors/${id}/`),
  create: (data) => api.post('/sectors/', data),
  update: (id, data) => api.patch(`/sectors/${id}/`, data),
  delete: (id) => api.delete(`/sectors/${id}/`),
  summary: () => api.get('/sectors/summary/'),
};

export const sensorLogAPI = {
  list: (params) => api.get('/sensor-logs/', { params }),
  latest: () => api.get('/sensor-logs/latest/'),
  trend: (sectorId, hours = 24) =>
    api.get('/sensor-logs/trend/', { params: { sector_id: sectorId, hours } }),
};

export const taskAPI = {
  list: (params) => api.get('/tasks/', { params }),
  create: (data) => api.post('/tasks/', data),
  update: (id, data) => api.patch(`/tasks/${id}/`, data),
  resolve: (id, notes) =>
    api.post(`/tasks/${id}/resolve/`, { resolution_notes: notes }),
};

export const alertAPI = {
  list: (params) => api.get('/alerts/', { params }),
  active: () => api.get('/alerts/active/'),
  acknowledge: (id) => api.post(`/alerts/${id}/acknowledge/`),
  resolve: (id) => api.post(`/alerts/${id}/resolve/`),
};

export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats/'),
};

export const simulationAPI = {
  trigger: (sectorId, scenario) =>
    api.post('/simulate/', { sector_id: sectorId, scenario }),
};