'use client'

import { useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { extractErrorDetail, getList, post } from '@/lib/api/data'
import { PageHeader, useApi } from '@/components/shared/async'

interface SearchResult {
  chunk_id?: string
  document_id?: string
  title?: string
  content?: string
  score?: number
  metadata?: Record<string, unknown>
  sources?: string[]
}

interface KnowledgeBase {
  id?: string
  name?: string
}

const MODES = [
  { value: 'hybrid', label: 'Hybrid', hint: 'Semantic plus keyword' },
  { value: 'vector', label: 'Vector', hint: 'Embedding similarity' },
  { value: 'keyword', label: 'Keyword', hint: 'Exact term matching' },
  { value: 'graph', label: 'Graph', hint: 'Relationship traversal' },
] as const

/** Modes served by POST /search/ that take query params; graph takes a body. */
const QUERY_PARAM_MODES = new Set(['vector', 'keyword'])

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [kbIds, setKbIds] = useState<string[]>([])
  const [mode, setMode] = useState<string>('hybrid')
  const [limit, setLimit] = useState('10')
  const [threshold, setThreshold] = useState('')
  const [results, setResults] = useState<SearchResult[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const knowledgeBases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])

  function toggleKb(id: string) {
    setKbIds((current) =>
      current.includes(id) ? current.filter((k) => k !== id) : [...current, id]
    )
  }

  async function runSearch() {
    if (!query.trim()) {
      setError('Enter a query first')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const limitValue = Number(limit) || 10
      let payload: { results?: SearchResult[] } | SearchResult[]

      if (QUERY_PARAM_MODES.has(mode) || mode === 'graph') {
        // These endpoints take query parameters, not a JSON body.
        const response = await post<{ results?: SearchResult[] }>(
          `/search/${mode}?query=${encodeURIComponent(query.trim())}&limit=${limitValue}`,
          undefined,
          { params: { query: query.trim(), limit: limitValue } }
        )
        payload = response
      } else {
        const response = await post<{ results?: SearchResult[] }>('/search/', {
          query: query.trim(),
          kb_ids: kbIds,
          limit: limitValue,
          search_type: mode,
          ...(threshold ? { score_threshold: Number(threshold) } : {}),
        })
        payload = response
      }

      const list = Array.isArray(payload) ? payload : (payload.results ?? [])
      setResults(list)
    } catch (err) {
      setError(extractErrorDetail(err))
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Search"
        description="Query indexed content using hybrid, vector, keyword or graph retrieval."
      />

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-sm font-medium">Search parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Query</Label>
            <Textarea
              id="query"
              rows={3}
              placeholder="What do you want to know?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="mode">Retrieval mode</Label>
              <Select value={mode} onValueChange={setMode}>
                <SelectTrigger id="mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MODES.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label} — {m.hint}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="limit">Limit</Label>
              <Input
                id="limit"
                type="number"
                min={1}
                max={100}
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="threshold">Score threshold (optional)</Label>
              <Input
                id="threshold"
                type="number"
                step="0.05"
                min={0}
                max={1}
                placeholder="0.0 – 1.0"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
            </div>
          </div>

          {mode === 'hybrid' && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">
                Knowledge bases (required — leave none selected to fail fast)
              </legend>
              <div className="flex flex-wrap gap-2">
                {knowledgeBases.data?.items.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No knowledge bases available. Create one before searching.
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
          )}

          <Button onClick={runSearch} disabled={loading}>
            <SearchIcon className="mr-2 h-4 w-4" />
            {loading ? 'Searching…' : 'Run search'}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive/50">
          <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {results && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Results ({results.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {results.length === 0 && (
              <p className="text-sm text-muted-foreground">No results found.</p>
            )}
            {results.map((result, index) => (
              <div key={result.chunk_id ?? result.document_id ?? index} className="rounded-lg border p-4">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">
                    {result.title ?? `Result ${index + 1}`}
                  </span>
                  {typeof result.score === 'number' && (
                    <Badge variant="secondary">score {result.score.toFixed(3)}</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {result.content ?? 'No content returned.'}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}