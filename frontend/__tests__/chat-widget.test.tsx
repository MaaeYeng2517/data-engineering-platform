import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { ChatWidget } from '@/components/marketing/chat-widget'

const providersPayload = {
  providers: [
    {
      name: 'openai',
      label: 'OpenAI',
      configured: false,
      available: false,
      default_model: 'gpt-4o',
      models: ['gpt-4o'],
      requires_key: true,
    },
    {
      name: 'ollama',
      label: 'Ollama (local)',
      configured: true,
      available: true,
      default_model: 'qwen3:8b',
      models: ['qwen3:8b', 'gemma3:latest'],
      requires_key: false,
    },
  ],
  default_provider: 'ollama',
  default_model: 'qwen3:8b',
  degraded: false,
}

function streamResponse(frames: string[]) {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(frames.join('')))
      controller.close()
    },
  })
  return {
    ok: true,
    status: 200,
    body: stream,
    json: async () => ({}),
  } as unknown as Response
}

function emptyStream() {
  return streamResponse([])
}

let axiosSpy: jest.SpyInstance

function serveProviders(payload: unknown) {
  axiosSpy.mockResolvedValue({ data: payload })
}

let fetchMock: jest.Mock

function send(text: string) {
  const input = screen.getByLabelText('Message')
  fireEvent.change(input, { target: { value: text } })
  fireEvent.keyDown(input, { key: 'Enter' })
}

function sentBody() {
  const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
  return JSON.parse(String(init.body)) as Record<string, unknown>
}

beforeEach(() => {
  fetchMock = jest.fn()
  global.fetch = fetchMock as unknown as typeof fetch
  fetchMock.mockResolvedValue(emptyStream())
  // The widget reads providers through the axios client; keep that off the network.
  axiosSpy = jest
    .spyOn(require('axios').Axios.prototype, 'request')
    .mockResolvedValue({ data: providersPayload })
})

afterEach(() => {
  jest.restoreAllMocks()
})

describe('ChatWidget', () => {
  it('lists only providers the deployment can serve', async () => {
    render(<ChatWidget />)

    await waitFor(() => {
      expect(screen.getByText(/models available on this deployment/i)).toBeInTheDocument()
    })

    expect(screen.getByText('qwen3:8b')).toBeInTheDocument()
    // OpenAI has no credential, so it is reported rather than offered.
    expect(screen.getByText('no API key')).toBeInTheDocument()
  })

  it('streams an answer and labels the model that produced it', async () => {
    fetchMock.mockResolvedValue(
      streamResponse([
        'event: meta\ndata: {"event":"meta","provider":"ollama","model":"qwen3:8b","degraded":false}\n\n',
        'event: delta\ndata: {"event":"delta","text":"DataAir "}\n\n',
        'event: delta\ndata: {"event":"delta","text":"ingests sources."}\n\n',
        'event: done\ndata: {"event":"done","provider":"ollama","model":"qwen3:8b","latency_ms":128,"token_usage":{"total":9},"sources":[]}\n\n',
      ]),
    )

    render(<ChatWidget />)
    await screen.findByLabelText('Message')
    send('What does DataAir do?')

    await waitFor(() => {
      expect(screen.getByText('DataAir ingests sources.')).toBeInTheDocument()
    })
    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByText('128ms')).toBeInTheDocument()
  })

  it('flags an offline answer instead of hiding it', async () => {
    fetchMock.mockResolvedValue(
      streamResponse([
        'event: meta\ndata: {"event":"meta","provider":"offline","model":"deterministic","degraded":true}\n\n',
        'event: delta\ndata: {"event":"delta","text":"No provider is configured."}\n\n',
        'event: done\ndata: {"event":"done","provider":"offline","model":"deterministic","degraded":true,"latency_ms":2,"token_usage":{"total":4},"sources":[]}\n\n',
      ]),
    )

    render(<ChatWidget />)
    await screen.findByLabelText('Message')
    send('hello')

    await waitFor(() => {
      expect(screen.getByText('offline fallback')).toBeInTheDocument()
    })
  })

  it('shows the API message when the stream fails', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: 'Too many chat requests. Try again in 42s.' }),
    } as unknown as Response)

    render(<ChatWidget />)
    await screen.findByLabelText('Message')
    send('hi')

    await waitFor(() => {
      expect(
        screen.getAllByText('Too many chat requests. Try again in 42s.').length,
      ).toBeGreaterThan(0)
    })
  })

  it('sends the question from a suggestion chip and can clear the thread', async () => {
    fetchMock.mockResolvedValue(
      streamResponse([
        'event: delta\ndata: {"event":"delta","text":"Hybrid search combines scores."}\n\n',
        'event: done\ndata: {"event":"done","provider":"ollama","model":"qwen3:8b","latency_ms":40,"token_usage":{"total":5},"sources":[]}\n\n',
      ]),
    )

    render(<ChatWidget />)
    const chip = await screen.findByRole('button', {
      name: /how does hybrid search rank results/i,
    })
    fireEvent.click(chip)

    await waitFor(() => {
      expect(screen.getByText('Hybrid search combines scores.')).toBeInTheDocument()
    })

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(JSON.parse(String(init.body))).toEqual(
      expect.objectContaining({
        messages: [{ role: 'user', content: expect.stringMatching(/hybrid search/i) }],
      }),
    )

    fireEvent.click(screen.getByRole('button', { name: /clear conversation/i }))
    await waitFor(() => {
      expect(screen.queryByText('Hybrid search combines scores.')).not.toBeInTheDocument()
    })
  })

  it('keeps shift+enter out of the request', async () => {
    fetchMock.mockResolvedValue(streamResponse([]))
    render(<ChatWidget />)

    const input = await screen.findByLabelText('Message')
    fireEvent.change(input, { target: { value: 'first line' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })

    expect(fetchMock).not.toHaveBeenCalled()
    expect(input).toHaveValue('first line')
  })
})

describe('ChatWidget model showcase', () => {
  it('pins the provider and model of the chip that was clicked', async () => {
    render(<ChatWidget />)
    fireEvent.click(await screen.findByRole('button', { name: 'gemma3:latest' }))

    expect(screen.getByRole('button', { name: 'gemma3:latest' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    send('which model answers this?')
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    expect(sentBody()).toEqual(
      expect.objectContaining({ provider: 'ollama', model: 'gemma3:latest' }),
    )
  })

  it('sends no provider or model while the Auto chip is active', async () => {
    render(<ChatWidget />)
    fireEvent.click(await screen.findByRole('button', { name: 'gemma3:latest' }))
    fireEvent.click(screen.getByRole('button', { name: 'Auto' }))

    expect(screen.getByRole('button', { name: 'Auto' })).toHaveAttribute('aria-pressed', 'true')

    send('let the gateway decide')
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    const body = sentBody()
    expect(body.provider).toBeUndefined()
    expect(body.model).toBeUndefined()
  })

  it('previews three models per provider and counts the rest', async () => {
    serveProviders({
      providers: [
        {
          name: 'ollama',
          label: 'Ollama (local)',
          configured: true,
          available: true,
          default_model: 'qwen3:8b',
          models: ['qwen3:8b', 'gemma3:latest', 'deepseek-r1:1.5b', 'llama2:latest'],
          requires_key: false,
        },
      ],
      default_provider: 'ollama',
      default_model: 'qwen3:8b',
      degraded: false,
    })

    render(<ChatWidget />)

    expect(await screen.findByText('deepseek-r1:1.5b')).toBeInTheDocument()
    expect(screen.queryByText('llama2:latest')).not.toBeInTheDocument()
    expect(screen.getByText('+1 more')).toBeInTheDocument()
  })

  it('distinguishes a missing key, a missing config and an unreachable provider', async () => {
    serveProviders({
      providers: [
        {
          name: 'openai',
          label: 'OpenAI',
          configured: false,
          available: false,
          default_model: 'gpt-4o',
          models: ['gpt-4o'],
          requires_key: true,
        },
        {
          name: 'ollama',
          label: 'Ollama (local)',
          configured: false,
          available: false,
          default_model: 'llama3.2',
          models: ['llama3.2'],
          requires_key: false,
        },
        {
          name: 'anthropic',
          label: 'Anthropic',
          configured: true,
          available: false,
          default_model: 'claude-haiku-4-5',
          models: ['claude-haiku-4-5'],
          requires_key: true,
        },
      ],
      default_provider: 'offline',
      default_model: 'deterministic',
      degraded: true,
    })

    render(<ChatWidget />)

    await waitFor(() => {
      expect(screen.getByText('no API key')).toBeInTheDocument()
    })
    expect(screen.getByText('not configured')).toBeInTheDocument()
    expect(screen.getByText('unreachable')).toBeInTheDocument()
    // An offline deployment still reports the model it will actually answer with.
    expect(screen.getByText(/no provider credentials configured/i)).toBeInTheDocument()
  })

  it('hides the strip but keeps answering when provider discovery fails', async () => {
    axiosSpy.mockRejectedValue(new Error('network down'))

    render(<ChatWidget />)

    await waitFor(() => {
      expect(screen.getByText(/model discovery is unreachable/i)).toBeInTheDocument()
    })
    expect(screen.queryByText('Models')).not.toBeInTheDocument()

    send('is the gateway up?')
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
  })
})
