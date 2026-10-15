import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Diagnostic logging without exposing secrets
apiClient.interceptors.request.use(
  (config) => {
    const fullUrl = (config.baseURL || '') + (config.url || '');
    console.debug(`[API Request] ${config.method?.toUpperCase()} ${fullUrl}`);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error?.message || error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const method = error.config?.method?.toUpperCase() || 'UNKNOWN';
    const fullUrl = (error.config?.baseURL || '') + (error.config?.url || '');
    const status = error.response?.status;
    console.error(`[API Error] ${method} ${fullUrl} -> Status: ${status ?? 'Network/CORS Error'}, Code: ${error.code || 'N/A'}`);
    return Promise.reject(error);
  }
);

export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Doctors
  getDoctors: async () => {
    const res = await apiClient.get('/doctors/');
    return res.data;
  },

  getDoctorSlots: async (doctorId, dateStr) => {
    const params = dateStr ? { target_date: dateStr } : {};
    const res = await apiClient.get(`/doctors/${doctorId}/slots`, { params });
    return res.data;
  },

  // Appointments
  getAppointments: async (params = {}) => {
    const res = await apiClient.get('/appointments/', { params });
    return res.data;
  },

  createAppointment: async (appointmentData) => {
    const res = await apiClient.post('/appointments/', appointmentData);
    return res.data;
  },

  cancelAppointment: async (appointmentId) => {
    const res = await apiClient.delete(`/appointments/${appointmentId}`);
    return res.data;
  },

  // WhatsApp Webhook Mock
  sendWhatsAppMessage: async (payload) => {
    const res = await apiClient.post('/whatsapp/', payload);
    return res.data;
  },
};

export default api;
