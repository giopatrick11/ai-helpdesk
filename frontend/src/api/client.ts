import axios from "axios";

const apiBaseURL = import.meta.env.VITE_API_BASE_URL;

if (!apiBaseURL) {
  throw new Error("VITE_API_BASE_URL is not configured");
}

const api = axios.create({
  baseURL: apiBaseURL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      window.location.pathname !== "/login"
    ) {
      localStorage.removeItem("access_token");
      window.location.assign("/login");
    }

    return Promise.reject(error);
  },
);

export default api;
