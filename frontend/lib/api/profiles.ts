import { getList, getOne, patch, post, remove } from './data'

export interface ServiceProfile {
  id: string
  tenant_id?: string
  owner_id?: string
  name: string
  slug: string
  description?: string | null
  environment: string
  cloud_provider: string
  region?: string | null
  zone?: string | null
  variables: Record<string, unknown>
  tags: string[]
  is_default: boolean
  is_active: boolean
  service_count: number
  config_count: number
  created_at?: string
  updated_at?: string
}

export interface ProfileService {
  id: string
  profile_id: string
  name: string
  service_type: string
  provider?: string | null
  description?: string | null
  api_base_url?: string | null
  host?: string | null
  port?: number | null
  region?: string | null
  zone?: string | null
  auth_type: string
  username?: string | null
  env_vars: Record<string, unknown>
  headers: Record<string, unknown>
  timeout_seconds: number
  max_retries: number
  health_check_url?: string | null
  health_check_enabled: boolean
  health_status: string
  last_checked_at?: string | null
  is_active: boolean
  /** The API never returns the token itself, only whether one is set. */
  has_token: boolean
  has_credentials: boolean
  token_masked?: string | null
  created_at?: string
  updated_at?: string
}

export interface ProfileConfigItem {
  id: string
  profile_id: string
  key: string
  description?: string | null
  value_type: string
  is_secret: boolean
  tags: string[]
  value?: string | null
  value_masked?: string | null
  created_at?: string
  updated_at?: string
}

export interface ProfileDetail extends ServiceProfile {
  services: ProfileService[]
  config_items: ProfileConfigItem[]
}

export interface ProfileOptions {
  environments: string[]
  cloud_providers: string[]
  service_types: string[]
  health_statuses: string[]
}

export interface ProfileInput {
  name: string
  description?: string | null
  environment: string
  cloud_provider: string
  region?: string | null
  zone?: string | null
  variables?: Record<string, unknown>
  tags?: string[]
  is_active?: boolean
}

export interface ProfileServiceInput {
  name: string
  service_type: string
  provider?: string | null
  description?: string | null
  api_base_url?: string | null
  host?: string | null
  port?: number | null
  region?: string | null
  zone?: string | null
  auth_type: string
  token?: string | null
  username?: string | null
  env_vars?: Record<string, unknown>
  headers?: Record<string, unknown>
  timeout_seconds?: number
  max_retries?: number
  health_check_url?: string | null
  health_check_enabled?: boolean
  is_active?: boolean
}

export interface ProfileConfigInput {
  key: string
  value?: string | null
  description?: string | null
  value_type?: string
  is_secret?: boolean
  tags?: string[]
}

const BASE = '/profiles'

/**
 * Secrets are write-only. `token` is accepted on create and on update (where it
 * rotates the stored value) and `clear_token` removes one, but no read path ever
 * hands the plaintext back.
 */
export const profilesApi = {
  list: (params?: { environment?: string; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.environment) query.set('environment', params.environment)
    if (params?.search) query.set('search', params.search)
    const suffix = query.toString() ? `?${query}` : ''
    return getList<ServiceProfile>(`${BASE}${suffix}`)
  },

  options: () => getOne<ProfileOptions>(`${BASE}/options`),

  get: (id: string) => getOne<ProfileDetail>(`${BASE}/${id}`),

  create: (body: ProfileInput) => post<ProfileDetail, ProfileInput>(BASE, body),

  update: (id: string, body: Partial<ProfileInput>) =>
    patch<ProfileDetail, Partial<ProfileInput>>(`${BASE}/${id}`, body),

  remove: (id: string) => remove(`${BASE}/${id}`),

  duplicate: (id: string) => post<ProfileDetail>(`${BASE}/${id}/duplicate`),

  createService: (id: string, body: ProfileServiceInput) =>
    post<ProfileService, ProfileServiceInput>(`${BASE}/${id}/services`, body),

  updateService: (id: string, serviceId: string, body: Partial<ProfileServiceInput>) =>
    patch<ProfileService, Partial<ProfileServiceInput>>(`${BASE}/${id}/services/${serviceId}`, body),

  removeService: (id: string, serviceId: string) => remove(`${BASE}/${id}/services/${serviceId}`),

  checkService: (id: string, serviceId: string) =>
    post<ProfileService>(`${BASE}/${id}/services/${serviceId}/health-check`),

  createConfig: (id: string, body: ProfileConfigInput) =>
    post<ProfileConfigItem, ProfileConfigInput>(`${BASE}/${id}/config`, body),

  updateConfig: (id: string, itemId: string, body: Partial<ProfileConfigInput>) =>
    patch<ProfileConfigItem, Partial<ProfileConfigInput>>(`${BASE}/${id}/config/${itemId}`, body),

  removeConfig: (id: string, itemId: string) => remove(`${BASE}/${id}/config/${itemId}`),
}

export const ENVIRONMENT_LABELS: Record<string, string> = {
  development: 'Development',
  staging: 'Staging',
  production: 'Production',
  testing: 'Testing',
}

export const CLOUD_LABELS: Record<string, string> = {
  aws: 'AWS',
  gcp: 'Google Cloud',
  azure: 'Azure',
  on_premise: 'On-premise',
  hybrid: 'Hybrid',
  other: 'Other',
}

export const SERVICE_TYPE_LABELS: Record<string, string> = {
  llm: 'LLM',
  embedding: 'Embedding',
  vector_db: 'Vector DB',
  search: 'Search',
  object_storage: 'Object storage',
  database: 'Database',
  cache: 'Cache',
  queue: 'Queue',
  monitoring: 'Monitoring',
  cdn: 'CDN',
  other: 'Other',
}

export const AUTH_TYPE_LABELS: Record<string, string> = {
  none: 'None',
  api_key: 'API key',
  bearer: 'Bearer token',
  basic: 'Basic auth',
  oauth2: 'OAuth 2.0',
  mtls: 'mTLS',
  custom: 'Custom header',
}
