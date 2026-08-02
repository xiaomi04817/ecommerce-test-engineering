import axios from 'axios'
import { getToken, removeToken, removeUser } from './auth'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor: attach Authorization Bearer token
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor: handle errors
api.interceptors.response.use(
  (response) => {
    const data = response.data
    // API returns { code, message, data }
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.message || '请求失败'

      if (status === 401) {
        removeToken()
        removeUser()
        ElMessage.error('登录已过期，请重新登录')
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      } else if (status === 403) {
        ElMessage.error(message || '没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error(message || '请求的资源不存在')
      } else if (status === 400) {
        ElMessage.error(message || '请求参数错误')
      } else {
        ElMessage.error(message || '服务器错误')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default api
