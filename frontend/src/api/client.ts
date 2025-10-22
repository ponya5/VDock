import axios from 'axios'
import type { AxiosInstance, AxiosError } from 'axios'

class ApiClient {
  private client: AxiosInstance
  private authToken: string | null = null
  private notificationsStore: any = null

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000
    })

    // Request interceptor to add auth token and handle content type
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`
        }
        
        // Set Content-Type to application/json for non-FormData requests
        if (!(config.data instanceof FormData)) {
          config.headers['Content-Type'] = 'application/json'
        }
        // For FormData, axios will automatically set the correct Content-Type with boundary
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        this.handleError(error)
        return Promise.reject(error)
      }
    )
  }

  setNotificationsStore(store: any) {
    this.notificationsStore = store
  }

  private lastErrorTime = 0
  private errorThrottleMs = 1000

  private handleError(error: AxiosError) {
    if (!this.notificationsStore) return

    const response = error.response
    const config = error.config
    const currentTime = Date.now()
    
    // Network error
    if (!response) {
      // Throttle network errors to prevent spam on page load
      if (currentTime - this.lastErrorTime < this.errorThrottleMs) {
        console.warn('Network error throttled:', config?.url)
        return
      }
      this.lastErrorTime = currentTime
      
      this.notificationsStore.error(
        'Network Error',
        'Unable to connect to the server. Please check your internet connection.',
        'The server may be offline or you may have connectivity issues.',
        { duration: 8000 }
      )
      return
    }

    // Handle specific status codes
    switch (response.status) {
      case 401:
        // Token expired or invalid
        this.setAuthToken(null)
        localStorage.removeItem('vdock_token')
        this.notificationsStore.warning(
          'Session Expired',
          'Your session has expired. Please log in again.',
          { duration: 5000 }
        )
        setTimeout(() => {
          window.location.href = '/login'
        }, 1000)
        break

      case 403:
        this.notificationsStore.error(
          'Access Denied',
          'You don\'t have permission to perform this action.',
          `Request: ${config?.method?.toUpperCase()} ${config?.url}`,
          { duration: 6000 }
        )
        break

      case 404:
        // Don't show 404 errors for config/profiles on initial load (expected behavior)
        if (config?.url?.includes('/config') || config?.url?.includes('/profiles')) {
          console.warn('Resource not found (expected):', config?.url)
          return
        }
        this.notificationsStore.error(
          'Not Found',
          'The requested resource was not found.',
          `URL: ${config?.url}`,
          { duration: 5000 }
        )
        break

      case 408:
        this.notificationsStore.error(
          'Request Timeout',
          'The request took too long to complete.',
          'Try again or check your connection speed.',
          { duration: 6000 }
        )
        break

      case 413:
        this.notificationsStore.error(
          'File Too Large',
          'The uploaded file exceeds the maximum allowed size.',
          'Please choose a smaller file (max 50MB).',
          { duration: 6000 }
        )
        break

      case 429:
        // Throttle 429 errors to prevent spam
        if (currentTime - this.lastErrorTime < this.errorThrottleMs) {
          console.warn('429 error throttled:', config?.url)
          return
        }
        this.lastErrorTime = currentTime
        
        // Don't show notifications for metrics endpoints (they poll frequently)
        if (config?.url?.includes('/metrics')) {
          console.warn('429 error (suppressed for metrics):', config?.url)
          return
        }
        
        this.notificationsStore.warning(
          'Too Many Requests',
          'You\'re making too many requests. Please slow down.',
          { duration: 5000 }
        )
        break

      case 500:
        this.notificationsStore.error(
          'Server Error',
          'An internal server error occurred.',
          response.data?.error || 'Please try again later or contact support.',
          { duration: 8000 }
        )
        break

      case 502:
      case 503:
      case 504:
        this.notificationsStore.error(
          'Service Unavailable',
          'The server is temporarily unavailable.',
          'Please try again in a few moments.',
          { duration: 6000 }
        )
        break

      default:
        // Generic error message with details from response
        const errorMessage = response.data?.message || response.data?.error || 'An unexpected error occurred'
        const errorDetails = response.data?.details || `Status: ${response.status}`
        
        this.notificationsStore.error(
          'Request Failed',
          errorMessage,
          errorDetails,
          { duration: 6000 }
        )
    }
  }

  setAuthToken(token: string | null) {
    this.authToken = token
  }

  async get(url: string, params?: any) {
    return this.client.get(url, { params })
  }

  async post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config)
  }

  async put(url: string, data?: any) {
    return this.client.put(url, data)
  }

  async delete(url: string) {
    return this.client.delete(url)
  }

  async uploadFile(url: string, file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData()
    formData.append('file', file)

    return this.client.post(url, formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }
}

export default new ApiClient()

