import type { AxiosRequestConfig } from 'axios'

import { api } from '@/lib/api/client'

export interface Paginated<T> {
  items: T[]
  total: number
}

/**
 * Keys the API uses to wrap collections. Endpoints return a bare array, an
 * object keyed by one of these, or a single object; all three must unwrap to
 * the same shape or pages silently render empty.
 */
const LIST_KEYS = [
  'items',
  'results',
  'data',
  'sources',
  'schemas',
  'documents',
  'types',
  'roles',
  'permissions',
  'logs',
  'datasets',
  'plans',
]

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Unwraps the various list shapes the API returns into a single form. */
function normalize<T>(data: unknown): Paginated<T> {
  if (Array.isArray(data)) {
    return { items: data as T[], total: data.length }
  }
  if (isPlainObject(data)) {
    for (const key of LIST_KEYS) {
      const value = data[key]
      if (Array.isArray(value)) {
        return { items: value as T[], total: Number(data.total ?? value.length) }
      }
    }
    // A single resource (entitlements, subscription). Wrap it so callers can
    // treat every endpoint uniformly instead of special-casing each one.
    return { items: [data as T], total: 1 }
  }
  return { items: [], total: 0 }
}

export async function getList<T>(
  path: string,
  config?: AxiosRequestConfig
): Promise<Paginated<T>> {
  const response = await api.get<T | Paginated<T>>(path, config)
  return normalize<T>(response.data)
}

/** Fetches a single resource, unwrapping both bare and `{item: ...}` forms. */
export async function getOne<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get<T>(path, config)
  const data = response.data
  if (isPlainObject(data)) {
    for (const key of LIST_KEYS) {
      const value = data[key]
      if (Array.isArray(value)) return value[0] as T
    }
  }
  return data as T
}

export async function post<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  config?: AxiosRequestConfig
): Promise<TResponse> {
  const response = await api.post<TResponse>(path, body, config)
  return response.data
}

export async function patch<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  config?: AxiosRequestConfig
): Promise<TResponse> {
  const response = await api.patch<TResponse>(path, body, config)
  return response.data
}

export async function put<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  config?: AxiosRequestConfig
): Promise<TResponse> {
  const response = await api.put<TResponse>(path, body, config)
  return response.data
}

export async function remove(path: string): Promise<void> {
  await api.delete(path)
}

/**
 * Some endpoints wrap errors as a list of validation objects rather than a
 * `detail` string. Surfaces something readable rather than [object Object].
 */
export function extractErrorDetail(error: unknown): string {
  const e = error as {
    response?: { data?: { detail?: unknown } }
    message?: string
  }
  const detail = e.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: unknown[] }
    const where = Array.isArray(first.loc) ? first.loc.join('.') : ''
    return where ? `${where}: ${first.msg ?? 'invalid'}` : (first.msg ?? 'invalid')
  }
  return e.message ?? 'Request failed'
}
