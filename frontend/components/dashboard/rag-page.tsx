'use client'

import { useState } from 'react'
import { Bot, Sparkles } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { extractErrorDetail, getList, post } from '@/lib/api/data'
import { PageHeader, useApi } from '@/components/shared/async'

interface KnowledgeBase {
  id?: string
  name?: string
}

interface SearchResult {
  chunk_id?: string
  document_id?: string
  title?: string
  content?: string
  score?: number
}

interface RagAnswer {
  answer?: string
  sources?: SearchResult[]
  citations?: Array<Record<string, unknown>>
  latency_ms?: number
  token_usage?: Record<string, number>
}

export function RagPage() {
  const [question, setQuestion] = useState('')
  const [kbIds, setKbIds] = useState<string[]>([])
  const [answer, setAnswer] = useState<RagAnswer | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const knowledgeBases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])

  function toggleKb(id: string) {
    setKbIds((current) =>
      current.includes(id) ? current.filter((k) => k !== id) : [...current, id]
    )
  }

  async function runQuery() {
    if (!question.trim()) {
      setError('Enter a question first')
      return
    }
    if (kbIds.length === 0) {
      setError('Select at least one knowledge base — the API requires kb_ids')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await post<RagAnswer>('/rag/', {
        query: question.trim(),
        kb_ids: kbIds,
      })
      setAnswer(result)
    } catch (err) {
      setError(extractErrorDetail(err))
      setAnswer(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="RAG Query"
        description="Ask natural-language questions grounded in your published knowledge."
      />

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-sm font-medium">Ask a question</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="question">Question</Label>
            <Textarea
              id="question"
              rows={4}
              placeholder="e.g. What is our data retention policy?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Knowledge bases (required)</legend>
            <div className="flex flex-wrap gap-2">
              {knowledgeBases.data?.items.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No knowledge bases yet. Create one to enable RAG queries.
                </p>
              )}
              {knowledgeBases.data?.items.map((kb, index) => {
                const id = kb.id ?? ''
                const active = kbIds.includes(id)
                return (
                  <Button
                    key={id || index}
                    type="button"
                    size="sm"
                    variant={active ? 'default' : 'outline'}
                    onClick={() => toggleKb(id)}
                  >
                    {kb.name ?? `KB ${index + 1}`}
                  </Button>
                )
              })}
            </div>
          </fieldset>

          <Button onClick={runQuery} disabled={loading}>
            <Sparkles className="mr-2 h-4 w-4" />
            {loading ? 'Generating…' : 'Generate answer'}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {answer && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Bot className="h-4 w-4" />
              Answer
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="whitespace-pre-wrap text-sm">
              {answer.answer ?? 'No answer returned.'}
            </p>

            <div className="flex flex-wrap gap-2">
              {typeof answer.latency_ms === 'number' && (
                <Badge variant="secondary">{Math.round(answer.latency_ms)}ms</Badge>
              )}
              {answer.token_usage &&
                Object.entries(answer.token_usage).map(([key, value]) => (
                  <Badge key={key} variant="outline">
                    {key}: {value}
                  </Badge>
                ))}
            </div>

            {answer.sources && answer.sources.length > 0 && (
              <div className="space-y-2 border-t pt-3">
                <p className="text-xs font-medium uppercase text-muted-foreground">Sources</p>
                <ul className="space-y-2">
                  {answer.sources.map((source, index) => (
                    <li key={source.chunk_id ?? index} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">
                          {source.title ?? `Source ${index + 1}`}
                        </span>
                        {typeof source.score === 'number' && (
                          <Badge variant="secondary">
                            {source.score.toFixed(3)}
                          </Badge>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {source.content ?? ''}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}