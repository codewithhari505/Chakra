import axios from 'axios';

const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[API Error]', err?.response?.status, err?.message);
    return Promise.reject(err);
  }
);

export default api;
