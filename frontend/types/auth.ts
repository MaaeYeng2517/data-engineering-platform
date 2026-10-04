export type UserRole = 'guest' | 'member' | 'admin'

export interface User {
  id: string
  email: string
  full_name?: string
is_active: boolean
  is_superuser?: boolean
  role?: string
  organization_id?: string
  created_at?: string
  updated_at?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  user: User
  tokens?: AuthTokens
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}