import { API_BASE_URL } from '@/lib/api/client'
import { getOne, post } from '@/lib/api/data'

export type ChatRole = 'user' | 'assistant'

export interface ChatTurn {
  role: ChatRole
  content: string
}

export interface ChatProviderInfo {
  name: string
  label: string
  configured: boolean
  available: boolean
  default_model: string
  models: string[]
  requires_key: boolean
}

export interface ChatProviders {
  providers: ChatProviderInfo[]
  default_provider: string
  default_model: string
  degraded: boolean
}

export interface ChatSource {
  id: string
  title?: string | null
  snippet: string
  score: number
}

export interface ChatAnswer {
  answer: string
  provider: string
  model: string
  finish_reason: string
  latency_ms: number
  token_usage: Record<string, number>
  sources: ChatSource[]
  degraded: boolean
}

export interface ChatRequestBody {
  messages: ChatTurn[]
  provider?: string
  model?: string
  temperature?: number
  max_tokens?: number
  kb_ids?: string[]
}

export interface ChatStreamHandlers {
  onMeta?: (info: { provider: string; model: string; degraded: boolean }) => void
  onDelta?: (text: string) => void
  onDone?: (info: {
    provider: string
    model: string
    degraded: boolean
    latency_ms: number
    token_usage: Record<string, number>
    sources: ChatSource[]
  }) => void
}

/**
 * Shown instead of the browser's raw "Failed to fetch".
 *
 * A rejected `fetch` means the API could not be reached at all — wrong base
 * URL, backend down, or a blocked cross-origin request — none of which the
 * visitor can act on, so the transport-level wording is replaced.
 */
export const CHAT_UNAVAILABLE_MESSAGE =
  'Sorry, the chat service is not available right now. Please try again in a moment.'

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError'
}

export async function fetchChatProviders(): Promise<ChatProviders> {
  return getOne<ChatProviders>('/chat/providers')
}

export async function sendChatMessage(body: ChatRequestBody): Promise<ChatAnswer> {
  return post<ChatAnswer>('/chat', body)
}

/**
 * Streams an answer over server-sent events.
 *
 * The endpoint is public and stateless, so `fetch` is used directly: axios has
 * no browser streaming support and the CSRF client would buffer the response.
 */
export async function streamChatMessage(
  body: ChatRequestBody,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
      signal,
    })
  } catch (err) {
    // An abort is the caller's own "Stop" action, so it must stay an abort.
    if (isAbortError(err)) throw err
    throw new Error(CHAT_UNAVAILABLE_MESSAGE)
  }

  if (!response.ok) {
    let detail = `Chat request failed (${response.status})`
    try {
      const payload = await response.json()
      if (typeof payload?.detail === 'string') detail = payload.detail
    } catch {
      // Keep the status-based message when the body is not JSON.
    }
    throw new Error(detail)
  }
  if (!response.body) {
    throw new Error('Streaming is not supported by this browser')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatch = (block: string) => {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }
    if (dataLines.length === 0) return

    let payload: Record<string, unknown>
    try {
      payload = JSON.parse(dataLines.join('\n'))
    } catch {
      return
    }

    if (event === 'meta') {
      handlers.onMeta?.({
        provider: String(payload.provider ?? ''),
        model: String(payload.model ?? ''),
        degraded: Boolean(payload.degraded),
      })
    } else if (event === 'delta') {
      handlers.onDelta?.(String(payload.text ?? ''))
    } else if (event === 'done') {
      handlers.onDone?.({
        provider: String(payload.provider ?? ''),
        model: String(payload.model ?? ''),
        degraded: Boolean(payload.degraded),
        latency_ms: Number(payload.latency_ms ?? 0),
        token_usage: (payload.token_usage ?? {}) as Record<string, number>,
        sources: (payload.sources ?? []) as ChatSource[],
      })
    } else if (event === 'error') {
      throw new Error(String(payload.detail ?? 'The chat stream failed'))
    }
  }

  try {
    for (;;) {
      let chunk: ReadableStreamReadResult<Uint8Array>
      try {
        chunk = await reader.read()
      } catch (err) {
        // The connection dropped mid-answer; the partial text stays on screen
        // and the caller reports the service as unavailable.
        if (isAbortError(err)) throw err
        throw new Error(CHAT_UNAVAILABLE_MESSAGE)
      }
      const { done, value } = chunk
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        dispatch(buffer.slice(0, boundary))
        buffer = buffer.slice(boundary + 2)
        boundary = buffer.indexOf('\n\n')
      }
    }
    buffer += decoder.decode()
    if (buffer.trim()) dispatch(buffer)
  } finally {
    reader.releaseLock()
  }
}
