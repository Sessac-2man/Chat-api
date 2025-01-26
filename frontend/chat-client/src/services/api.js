import axios from "axios";
import store from "../store";

const API = axios.create({
  baseURL: "http://localhost:8002", // FastAPI 서버 주소
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청 인터셉터
API.interceptors.request.use(
  config => {
    const token = store.getters.getToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 응답 인터셉터
API.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      store.dispatch("logout");
    }
    return Promise.reject(error);
  }
);

export default API;
