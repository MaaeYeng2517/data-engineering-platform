/**
 * Server-side session helpers.
 *
 * The browser is authenticated by the FastAPI backend through cookies
 * (`dataair_access_token`). A Next.js route handler has to forward those
 * cookies to the backend to learn who the caller is — the session is never
 * re-implemented here.
 */
const API_BASE_URL =
  process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface SessionUser {
  id: string
  tenant_id: string
  email: string
  full_name: string | null
  role: string
}

/**
 * Resolve the signed-in user from the request cookies, or null when the
 * caller has no valid session.
 */
export async function getSessionUser(cookieHeader: string | null): Promise<SessionUser | null> {
  if (!cookieHeader) return null

  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { cookie: cookieHeader },
      cache: 'no-store',
    })
    if (!response.ok) return null
    const user = (await response.json()) as SessionUser
    return user?.id ? user : null
  } catch {
    return null
  }
}
