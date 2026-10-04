import { CHAT_UNAVAILABLE_MESSAGE, fetchChatProviders, streamChatMessage } from '@/lib/api/chat'

interface StreamHandlers {
  meta: unknown[]
  deltas: string[]
  done?: Record<string, unknown>
}

function sseResponse(frames: string[], status = 200): Response {
  const body = frames.join('')
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body))
      controller.close()
    },
  })
  return {
    ok: status >= 200 && status < 300,
    status,
    body: stream,
    json: async () => JSON.parse(body || '{}'),
  } as unknown as Response
}

function collect() {
  const state: StreamHandlers = { meta: [], deltas: [] }
  return {
    state,
    handlers: {
      onMeta: (info: unknown) => state.meta.push(info),
      onDelta: (text: string) => state.deltas.push(text),
      onDone: (info: Record<string, unknown>) => {
        state.done = info
      },
    },
  }
}

const originalFetch = global.fetch

afterEach(() => {
  global.fetch = originalFetch
  jest.restoreAllMocks()
})

describe('streamChatMessage', () => {
  it('parses meta, delta and done frames into callbacks', async () => {
    global.fetch = jest.fn(async () =>
      sseResponse([
        'event: meta\ndata: {"event":"meta","provider":"openai","model":"gpt-4o","degraded":false}\n\n',
        'event: delta\ndata: {"event":"delta","text":"Hel"}\n\n',
        'event: delta\ndata: {"event":"delta","text":"lo"}\n\n',
        'event: done\ndata: {"event":"done","provider":"openai","model":"gpt-4o","latency_ms":42.5,"token_usage":{"total":7},"sources":[]}\n\n',
      ]),
    ) as unknown as typeof fetch

    const { state, handlers } = collect()
    await streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers)

    expect(state.meta).toEqual([{ provider: 'openai', model: 'gpt-4o', degraded: false }])
    expect(state.deltas.join('')).toBe('Hello')
    expect(state.done).toMatchObject({ provider: 'openai', latency_ms: 42.5 })
  })

  it('reassembles frames split across chunk boundaries', async () => {
    const payload =
      'event: delta\ndata: {"event":"delta","text":"split"}\n\nevent: done\ndata: {"event":"done","latency_ms":1}\n\n'
    const bytes = new TextEncoder().encode(payload)
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        // One byte at a time: the parser must buffer partial frames.
        for (const byte of bytes) controller.enqueue(new Uint8Array([byte]))
        controller.close()
      },
    })

    global.fetch = jest.fn(
      async () => ({ ok: true, status: 200, body: stream }) as unknown as Response,
    ) as unknown as typeof fetch

    const { state, handlers } = collect()
    await streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers)

    expect(state.deltas.join('')).toBe('split')
    expect(state.done).toMatchObject({ latency_ms: 1 })
  })

  it('keeps non-ASCII text intact', async () => {
    global.fetch = jest.fn(async () =>
      sseResponse(['event: delta\ndata: {"event":"delta","text":"สวัสดี"}\n\n']),
    ) as unknown as typeof fetch

    const { state, handlers } = collect()
    await streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers)

    expect(state.deltas.join('')).toBe('สวัสดี')
  })

  it('throws the detail from an error frame', async () => {
    global.fetch = jest.fn(async () =>
      sseResponse(['event: error\ndata: {"detail":"No LLM provider is configured"}\n\n']),
    ) as unknown as typeof fetch

    const { handlers } = collect()
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.toThrow('No LLM provider is configured')
  })

  it('surfaces the API detail when the request fails', async () => {
    global.fetch = jest.fn(
      async () =>
        ({
          ok: false,
          status: 429,
          json: async () => ({ detail: 'Too many chat requests. Try again in 42s.' }),
        }) as unknown as Response,
    ) as unknown as typeof fetch

    const { handlers } = collect()
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.toThrow('Too many chat requests. Try again in 42s.')
  })

  it('posts the selected provider and model', async () => {
    const fetchMock = jest.fn(async () => sseResponse([]))
    global.fetch = fetchMock as unknown as typeof fetch

    await streamChatMessage(
      {
        messages: [{ role: 'user', content: 'hi' }],
        provider: 'ollama',
        model: 'qwen3:8b',
        kb_ids: ['kb-1'],
      },
      {},
    )

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toContain('/chat/stream')
    expect(JSON.parse(String(init.body))).toEqual({
      messages: [{ role: 'user', content: 'hi' }],
      provider: 'ollama',
      model: 'qwen3:8b',
      kb_ids: ['kb-1'],
    })
  })

  it('replaces the raw "Failed to fetch" when the API is unreachable', async () => {
    global.fetch = jest.fn(async () => {
      throw new TypeError('Failed to fetch')
    }) as unknown as typeof fetch

    const { handlers } = collect()
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.toThrow(CHAT_UNAVAILABLE_MESSAGE)
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.not.toThrow('Failed to fetch')
  })

  it('propagates an abort instead of reporting the service as down', async () => {
    const abort = new Error('The operation was aborted')
    abort.name = 'AbortError'
    global.fetch = jest.fn(async () => {
      throw abort
    }) as unknown as typeof fetch

    const { handlers } = collect()
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.toThrow('The operation was aborted')
  })

  it('reports the service as unavailable when the stream drops mid-answer', async () => {
    let sent = false
    const stream = new ReadableStream<Uint8Array>({
      pull(controller) {
        if (!sent) {
          sent = true
          controller.enqueue(
            new TextEncoder().encode(
              'event: delta\ndata: {"event":"delta","text":"partial"}\n\n',
            ),
          )
          return
        }
        controller.error(new TypeError('network error'))
      },
    })

    global.fetch = jest.fn(
      async () => ({ ok: true, status: 200, body: stream }) as unknown as Response,
    ) as unknown as typeof fetch

    const { state, handlers } = collect()
    await expect(
      streamChatMessage({ messages: [{ role: 'user', content: 'hi' }] }, handlers),
    ).rejects.toThrow(CHAT_UNAVAILABLE_MESSAGE)
    expect(state.deltas.join('')).toBe('partial')
  })
})

describe('fetchChatProviders', () => {
  it('unwraps the providers payload', async () => {
    const axios = jest.requireActual('axios')
    const spy = jest.spyOn(axios.Axios.prototype, 'request').mockResolvedValue({
      data: {
        providers: [{ name: 'ollama', label: 'Ollama', available: true, models: ['qwen3:8b'] }],
        default_provider: 'ollama',
        default_model: 'qwen3:8b',
        degraded: false,
      },
    })

    const result = await fetchChatProviders()

    expect(result.default_provider).toBe('ollama')
    expect(result.providers[0].models).toEqual(['qwen3:8b'])
    spy.mockRestore()
  })
})
