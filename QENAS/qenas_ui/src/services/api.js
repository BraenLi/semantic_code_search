/**
 * API 客户端服务
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API 错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// 策略 API
export const strategiesApi = {
  list: () => apiClient.get('/strategies'),
  get: (id) => apiClient.get(`/strategies/${id}`),
  create: (data) => apiClient.post('/strategies', data),
  start: (id) => apiClient.post(`/strategies/${id}/start`),
  stop: (id) => apiClient.post(`/strategies/${id}/stop`),
  delete: (id) => apiClient.delete(`/strategies/${id}`),
  getStatus: (id) => apiClient.get(`/strategies/${id}/status`),
}

// 回测 API
export const backtestApi = {
  run: (data) => apiClient.post('/backtest/qenas', data),
  list: () => apiClient.get('/backtest'),
  get: (jobId) => apiClient.get(`/backtest/${jobId}`),
  getResult: (jobId) => apiClient.get(`/backtest/${jobId}/result`),
  cancel: (jobId) => apiClient.post(`/backtest/${jobId}/cancel`),
  delete: (jobId) => apiClient.delete(`/backtest/${jobId}`),
}

// 可视化 API
export const visualizationApi = {
  getEntanglement: (params) => apiClient.get('/visualization/entanglement', { params }),
  getEntanglementHistory: (params) => apiClient.get('/visualization/entanglement/history', { params }),
  getEvents: (params) => apiClient.get('/visualization/events', { params }),
  getPerformance: (params) => apiClient.get('/visualization/performance', { params }),
  getEcosystem: (params) => apiClient.get('/visualization/ecosystem', { params }),
  getDashboard: (params) => apiClient.get('/visualization/dashboard', { params }),
}

export default apiClient
