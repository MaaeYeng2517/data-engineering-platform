'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Bot,
  CornerDownLeft,
  Cpu,
  Loader2,
  Send,
  Sparkles,
  Square,
  Trash2,
  TriangleAlert,
  User,
} from 'lucide-react'

import {
  ChatProviderInfo,
  ChatRole,
  ChatTurn,
  fetchChatProviders,
  streamChatMessage,
} from '@/lib/api/chat'
import { extractErrorDetail } from '@/lib/api/data'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const AUTO_VALUE = 'auto'
const HISTORY_LIMIT = 20
const MODELS_PREVIEW_LIMIT = 3

interface RenderedMessage extends ChatTurn {
  id: string
  provider?: string
  model?: string
  degraded?: boolean
  latencyMs?: number
  pending?: boolean
  failed?: boolean
}

const suggestions = [
  'What can DataAir do for a data team?',
  'How does hybrid search rank results?',
  'Which LLM providers can this deployment use?',
  'How do I ground an answer in my own documents?',
  'Build a data analysis pipeline for sales data',
  'Create an AI agent to analyze customer feedback',
  'Generate SQL for cohort analysis',
  'Write a Python script to clean CSV data',
  'Design a data warehouse schema for e-commerce',
  'Explain how to set up ETL for this platform',
  'Create a dashboard specification for sales metrics',
  'Write code to detect anomalies in time series data',
  'Plan a RAG system for technical documentation',
  'Generate dbt models for a fact table',
  'Build an AI coding agent workflow',
]

let messageCounter = 0

function nextId(role: ChatRole): string {
  messageCounter += 1
  return `${role}-${messageCounter}`
}

function modelValue(provider: ChatProviderInfo, model: string) {
  return `${provider.name}::${model}`
}

function modelOptions(providers: ChatProviderInfo[]) {
  const options: { value: string; label: string }[] = [
    { value: AUTO_VALUE, label: 'Automatic — best available provider' },
  ]
  for (const provider of providers) {
    if (!provider.available) continue
    for (const model of provider.models) {
      options.push({
        value: modelValue(provider, model),
        label: `${provider.label} · ${model}`,
      })
    }
  }
  return options
}

function ModelShowcase({
  providers,
  loading,
  target,
  onSelect,
}: {
  providers: ChatProviderInfo[]
  loading: boolean
  target: string
  onSelect: (value: string) => void
}) {
  if (loading) {
    return (
      <div className="flex flex-wrap items-center gap-2 border-b px-4 py-2.5">
        <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <Cpu className="h-3.5 w-3.5" />
          Models
        </span>
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-5 w-16" />
      </div>
    )
  }

  if (providers.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b px-4 py-2.5">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Cpu className="h-3.5 w-3.5" />
        Models
      </span>

      <button
        type="button"
        onClick={() => onSelect(AUTO_VALUE)}
        aria-pressed={target === AUTO_VALUE}
        className={cn(
          'rounded-full border px-2 py-0.5 text-[11px] transition-colors',
          target === AUTO_VALUE
            ? 'border-primary bg-primary/10 font-medium text-primary'
            : 'text-muted-foreground hover:border-primary hover:text-foreground',
        )}
      >
        Auto
      </button>

      {providers.map((provider) => {
        const visible = provider.models.slice(0, MODELS_PREVIEW_LIMIT)
        const hidden = provider.models.length - visible.length
        return (
          <div key={provider.name} className="flex flex-wrap items-center gap-1.5">
            <span
              className={cn(
                'text-[11px] font-semibold uppercase tracking-wide',
                provider.available ? 'text-muted-foreground' : 'text-muted-foreground/50',
              )}
            >
              {provider.label}
            </span>
            {provider.available ? (
              <>
                {visible.map((model) => {
                  const value = modelValue(provider, model)
                  const active = target === value
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onSelect(value)}
                      aria-pressed={active}
                      className={cn(
                        'rounded-full border px-2 py-0.5 font-mono text-[11px] transition-colors',
                        active
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:border-primary hover:text-foreground',
                      )}
                    >
                      {model}
                    </button>
                  )
                })}
                {hidden > 0 && (
                  <span className="text-[11px] text-muted-foreground">+{hidden} more</span>
                )}
              </>
            ) : (
              <span className="text-[11px] text-muted-foreground/70">
                {!provider.configured && provider.requires_key
                  ? 'no API key'
                  : !provider.configured
                    ? 'not configured'
                    : 'unreachable'}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

export function ChatWidget({ kbIds = [] }: { kbIds?: string[] }) {
  const [providers, setProviders] = useState<ChatProviderInfo[]>([])
  const [providersLoading, setProvidersLoading] = useState(true)
  const [providersUnreachable, setProvidersUnreachable] = useState(false)
  const [target, setTarget] = useState<string>(AUTO_VALUE)
  const [messages, setMessages] = useState<RenderedMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    let active = true
    fetchChatProviders()
      .then((data) => {
        if (active && Array.isArray(data?.providers)) setProviders(data.providers)
      })
      .catch(() => {
        // Leave the picker on "Automatic"; the backend still resolves a provider.
        if (active) setProvidersUnreachable(true)
      })
      .finally(() => {
        if (active) setProvidersLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const node = scrollRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [messages])

  useEffect(() => () => abortRef.current?.abort(), [])

  const options = useMemo(() => modelOptions(providers), [providers])
  const selected = useMemo(() => {
    if (target === AUTO_VALUE) return {}
    const [provider, model] = target.split('::')
    return { provider, model }
  }, [target])

  const patchLastAssistant = useCallback((patch: Partial<RenderedMessage>) => {
    setMessages((current) => {
      const last = current[current.length - 1]
      if (!last || last.role !== 'assistant') return current
      return [...current.slice(0, -1), { ...last, ...patch }]
    })
  }, [])

  const appendDelta = useCallback((text: string) => {
    setMessages((current) => {
      const last = current[current.length - 1]
      if (!last || last.role !== 'assistant') return current
      return [...current.slice(0, -1), { ...last, content: last.content + text }]
    })
  }, [])

  const send = useCallback(
    async (question: string) => {
      const text = question.trim()
      if (!text || busy) return

      const history: ChatTurn[] = messages
        .filter((message) => !message.failed && message.content.trim())
        .map(({ role, content }) => ({ role, content }))
        .slice(-HISTORY_LIMIT)
      const assistantId = nextId('assistant')

      setError(null)
      setInput('')
      setBusy(true)
      setMessages((current) => [
        ...current,
        { id: nextId('user'), role: 'user', content: text },
        { id: assistantId, role: 'assistant', content: '', pending: true },
      ])

      const controller = new AbortController()
      abortRef.current = controller
      let received = ''

      try {
        await streamChatMessage(
          {
            messages: [...history, { role: 'user', content: text }],
            ...selected,
            ...(kbIds.length > 0 ? { kb_ids: kbIds } : {}),
          },
          {
            onMeta: (info) => patchLastAssistant({ provider: info.provider, model: info.model }),
            onDelta: (chunk) => {
              received += chunk
              appendDelta(chunk)
            },
            onDone: (info) =>
              patchLastAssistant({
                provider: info.provider,
                model: info.model,
                degraded: info.degraded,
                latencyMs: info.latency_ms,
                pending: false,
              }),
          },
          controller.signal,
        )

        if (received.trim()) {
          patchLastAssistant({ pending: false })
        } else {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId
                ? {
                    ...message,
                    content: 'The provider returned an empty answer.',
                    failed: true,
                    pending: false,
                  }
                : message,
            ),
          )
        }
      } catch (err) {
        if (controller.signal.aborted) {
          patchLastAssistant({ pending: false })
        } else {
          const detail = extractErrorDetail(err)
          setError(detail)
          setMessages((current) => {
            const last = current[current.length - 1]
            if (last?.id === assistantId && !last.content.trim()) {
              return [
                ...current.slice(0, -1),
                { ...last, content: detail, failed: true, pending: false },
              ]
            }
            return current.map((message) =>
              message.id === assistantId ? { ...message, pending: false } : message,
            )
          })
        }
      } finally {
        abortRef.current = null
        setBusy(false)
      }
    },
    [appendDelta, busy, kbIds, messages, patchLastAssistant, selected],
  )

  function stop() {
    abortRef.current?.abort()
  }

  function reset() {
    abortRef.current?.abort()
    setMessages([])
    setError(null)
  }

  const availableCount = options.length - 1

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-card shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold">AI Agent Chat</p>
            <p className="text-xs text-muted-foreground">
              {providersLoading
                ? 'Checking which providers this deployment can reach…'
                : providersUnreachable
                  ? 'Model discovery is unreachable — the gateway picks the provider per answer.'
                  : availableCount > 0
                    ? `${availableCount} model${availableCount === 1 ? '' : 's'} available on this deployment.`
                    : 'No provider credentials configured — answers run in offline mode.'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select value={target} onValueChange={setTarget}>
            <SelectTrigger className="h-9 w-[260px] text-xs" aria-label="Model">
              <SelectValue placeholder="Choose a model" />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value} className="text-xs">
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={reset}
            disabled={messages.length === 0}
            aria-label="Clear conversation"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ModelShowcase
        providers={providers}
        loading={providersLoading}
        target={target}
        onSelect={setTarget}
      />

      <div ref={scrollRef} className="h-[420px] space-y-4 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium">AI Agent Ready</p>
              <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
                Build, analyze, and code with AI. Ask for data analysis, SQL, Python scripts, ETL workflows, or AI agent designs.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 pt-1">
              {suggestions.map((suggestion) => (
                <Button
                  key={suggestion}
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-auto py-1.5 text-xs"
                  onClick={() => void send(suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
            >
              <div
                className={
                  message.role === 'user'
                    ? 'max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground'
                    : 'max-w-[90%] space-y-2 rounded-2xl rounded-bl-sm bg-muted px-4 py-2.5 text-sm'
                }
              >
                <div className="flex items-center gap-1.5 text-xs font-medium opacity-70">
                  {message.role === 'user' ? (
                    <User className="h-3 w-3" />
                  ) : (
                    <Bot className="h-3 w-3" />
                  )}
                  <span>{message.role === 'user' ? 'You' : 'Assistant'}</span>
                </div>

                 {message.role === 'assistant' ? (
                   <ReactMarkdown
                     remarkPlugins={[remarkGfm]}
                     components={{
                       p: ({ node, ...props }) => <p className="mb-2 break-words" {...props} />,
                       ul: ({ node, ...props }) => <ul className="mb-2 ml-5 list-disc" {...props} />,
                       ol: ({ node, ...props }) => <ol className="mb-2 ml-5 list-decimal" {...props} />,
                       code: ({ node, ...props }) => (
                         <code className="rounded bg-muted px-1.5 py-0.5 text-sm" {...props} />
                       ),
                       pre: ({ node, ...props }) => (
                         <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-sm" {...props} />
                       ),
                       blockquote: ({ node, ...props }) => (
                         <blockquote className="border-l-2 border-muted pl-4 italic" {...props} />
                       ),
                     }}
                   >
                     {message.content}
                   </ReactMarkdown>
                 ) : (
                   <p className="whitespace-pre-wrap break-words">{message.content}</p>
                 )}
                {message.pending && !message.content ? (
                  <Loader2 className="ml-1 inline h-3.5 w-3.5 animate-spin" />
                ) : null}

                {message.role === 'assistant' && (message.model || message.latencyMs) && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    {message.model && (
                      <Badge variant="secondary" className="text-[10px]">
                        {message.model}
                      </Badge>
                    )}
                    {typeof message.latencyMs === 'number' && (
                      <Badge variant="outline" className="text-[10px]">
                        {Math.round(message.latencyMs)}ms
                      </Badge>
                    )}
                    {message.degraded && (
                      <Badge variant="outline" className="gap-1 text-[10px]">
                        <TriangleAlert className="h-3 w-3" />
                        offline fallback
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="space-y-3 border-t p-4">
        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-xs text-destructive">
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span className="flex-1">{error}</span>
            <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}

        <Textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void send(input)
            }
          }}
          placeholder="Ask AI agent: data analysis, SQL, Python, ETL, workflow, coding..."
          rows={2}
          disabled={busy}
          aria-label="Message"
        />

        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <CornerDownLeft className="h-3 w-3" />
            Enter sends · Shift + Enter adds a new line
          </p>
          <div className="flex items-center gap-2">
            {busy ? (
              <Button type="button" variant="outline" size="sm" onClick={stop}>
                <Square className="mr-2 h-3.5 w-3.5" />
                Stop
              </Button>
            ) : null}
            <Button type="button" size="sm" onClick={() => void send(input)} disabled={busy}>
              <Send className="mr-2 h-3.5 w-3.5" />
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function ChatSection() {
  return (
    <section id="chat" className="scroll-mt-16 border-b bg-muted/30 py-20">
      <div className="container">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <Badge variant="secondary" className="gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Live assistant
          </Badge>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Ask the platform anything
          </h2>
          <p className="mt-3 text-muted-foreground">
            This assistant runs on the same LLM gateway as the workspace: OpenAI, Anthropic, Gemini
            or a local Ollama runtime, whichever this deployment has configured. The model list
            below is read live from the gateway, so you can pick the exact model that answers your
            question.
          </p>
        </div>

        <div className="mx-auto max-w-3xl">
          <ChatWidget />
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Need answers grounded in your own documents?{' '}
            <Link href="/register" className="underline underline-offset-4">
              Create a workspace
            </Link>{' '}
            and query a published knowledge base from{' '}
            <Link href="/dashboard/rag" className="underline underline-offset-4">
              RAG
            </Link>
            .
          </p>
        </div>
      </div>
    </section>
  )
}
