import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const CSRF_COOKIE_NAME = 'dataair_csrf_token'
const CSRF_HEADER = 'x-csrf-token'

export { API_BASE_URL }

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

const AUTH_PATH_PREFIX = '/auth'

/**
 * Only bounce to the login screen for requests that need a session.
 *
 * The session probe (`/auth/me`) runs on every page including the marketing
 * home page, and an anonymous visitor gets a 401 there by design. Redirecting
 * on that response traps public pages behind the login form.
 */
function shouldRedirectToLogin(config?: { url?: string }): boolean {
  if (typeof window === 'undefined') return false
  const url = config?.url ?? ''
  if (url.startsWith(AUTH_PATH_PREFIX)) return false
  const path = window.location.pathname
  if (path.startsWith('/login') || path.startsWith('/register')) return false
  return true
}

function withReturnPath(pathname: string): string {
  if (!pathname || pathname === '/') return '/login'
  return `/login?next=${encodeURIComponent(pathname)}`
}

class ApiClient {
  private client: AxiosInstance
  private csrfToken: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Send cookies
    })

    this.setupInterceptors()
  }

  private async ensureCsrfToken(): Promise<string | null> {
    const fromCookie = readCookie(CSRF_COOKIE_NAME)
    if (fromCookie) {
      this.csrfToken = fromCookie
      return fromCookie
    }
    if (this.csrfToken) return this.csrfToken

    try {
      const response = await axios.get<{ csrf_token: string }>(`${API_BASE_URL}/auth/csrf-token`, {
        withCredentials: true,
      })
      this.csrfToken = response.data.csrf_token
      return this.csrfToken
    } catch {
      return null
    }
  }

  private setupInterceptors() {
    // Request interceptor - attach CSRF token for unsafe methods
    this.client.interceptors.request.use(
      async (config) => {
        const method = (config.method || 'get').toLowerCase()
        if (['post', 'put', 'patch', 'delete'].includes(method)) {
          const token = await this.ensureCsrfToken()
          if (token) {
            config.headers = config.headers || {}
            config.headers[CSRF_HEADER] = token
          }
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && shouldRedirectToLogin(error.config)) {
          window.location.href = withReturnPath(window.location.pathname)
        }
        return Promise.reject(error)
      },
    )
  }

  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config)
  }

  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config)
  }

  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config)
  }

  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config)
  }

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config)
  }
}

export const api = new ApiClient()
