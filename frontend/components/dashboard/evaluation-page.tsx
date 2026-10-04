'use client'

import { useState } from 'react'
import { FlaskConical, Play } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { getList, post, extractErrorDetail } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface EvaluationResult {
  run_id?: string
  overall_score?: number
  status?: string
  metrics?: Record<string, unknown>
}

export function EvaluationPage() {
  const datasets = useApi(() => getList<string>('/evaluation/datasets'), [])
  const [kbId, setKbId] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [questions, setQuestions] = useState('')
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  async function runEvaluation() {
    if (!kbId.trim()) {
      setError('Knowledge base ID is required')
      return
    }
    setRunning(true)
    setError(null)
    try {
      // The API expects questions as objects ({question: string}), not bare strings.
      const parsed = questions
        .split('\n')
        .map((q) => q.trim())
        .filter(Boolean)
        .map((q) => ({ question: q }))
      const response = await post<EvaluationResult>('/evaluation/', {
        kb_id: kbId.trim(),
        ...(datasetId ? { dataset_id: datasetId } : {}),
        ...(parsed.length ? { questions: parsed } : {}),
      })
      setResult(response)
    } catch (err) {
      setError(extractErrorDetail(err))
      setResult(null)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluation"
        description="Measure retrieval quality against question sets drawn from your data."
        actions={<ReloadButton onClick={datasets.reload} />}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <h2 className="mb-3 flex items-center gap-2 font-semibold">
              <FlaskConical className="h-4 w-4 text-muted-foreground" />
              Datasets
            </h2>
            <AsyncBoundary
              loading={datasets.loading}
              error={datasets.error}
              onRetry={datasets.reload}
              isEmpty={!datasets.data?.items.length}
              empty={
                <EmptyState
                  title="No evaluation datasets"
                  description="Create a dataset of questions to measure retrieval quality."
                />
              }
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Dataset</TableHead>
                    <TableHead>Select</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasets.data?.items.map((name, index) => (
                    <TableRow key={name || index}>
                      <TableCell className="font-mono text-xs">{name}</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setDatasetId(name)}
                        >
                          Use
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </AsyncBoundary>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium">Run an evaluation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="eval-kb">Knowledge base ID</Label>
              <Input
                id="eval-kb"
                placeholder="Paste a knowledge base ID"
                value={kbId}
                onChange={(e) => setKbId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="eval-dataset">Dataset (optional)</Label>
              <Input
                id="eval-dataset"
                placeholder="Select from the datasets list"
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="eval-questions">Questions (one per line)</Label>
              <Textarea
                id="eval-questions"
                rows={5}
                placeholder={'What is our SLA?\nHow do we handle PII?'}
                value={questions}
                onChange={(e) => setQuestions(e.target.value)}
              />
            </div>
            <Button onClick={runEvaluation} disabled={running}>
              <Play className="mr-2 h-4 w-4" />
              {running ? 'Running…' : 'Run evaluation'}
            </Button>
            {error && <p className="text-sm text-destructive">{error}</p>}
            {result && (
              <div className="space-y-2 rounded-lg border p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">Run {result.run_id ?? '—'}</span>
                  <Badge variant="secondary">{result.status ?? 'completed'}</Badge>
                </div>
                {typeof result.overall_score === 'number' && (
                  <p className="text-sm">
                    Overall score:{' '}
                    <span className="font-semibold">{result.overall_score.toFixed(3)}</span>
                  </p>
                )}
                {result.metrics && (
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {Object.entries(result.metrics).map(([key, value]) => (
                      <li key={key}>
                        {key}: {String(value)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}