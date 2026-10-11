'use client'

import { useState } from 'react'
import { FlaskConical, Play, Plus, Edit, Trash2, FileText, ChevronDown, ChevronUp } from 'lucide-react'

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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { getList, post, put, remove, extractErrorDetail } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { toast } from 'sonner'

interface EvaluationDataset {
  id?: string
  kb_id?: string
  name?: string
  description?: string
  questions?: Array<{ question: string; answer?: string }>
  question_count?: number
  created_at?: string
  updated_at?: string
}

interface EvaluationRun {
  id?: string
  dataset_id?: string
  kb_id?: string
  metrics?: Record<string, unknown>
  overall_score?: number
  status?: string
  results?: Array<{ question: string; answer?: string; score?: number }>
  created_at?: string
}

interface EvaluationResult {
  run_id?: string
  overall_score?: number
  status?: string
  metrics?: Record<string, unknown>
}

export function EvaluationPage() {
  const [kbId, setKbId] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [questions, setQuestions] = useState('')
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  // Dataset CRUD state
  const [newDatasetName, setNewDatasetName] = useState('')
  const [newDatasetDescription, setNewDatasetDescription] = useState('')
  const [newDatasetQuestions, setNewDatasetQuestions] = useState('')
  const [creatingDataset, setCreatingDataset] = useState(false)
  const [editingDatasetId, setEditingDatasetId] = useState<string | null>(null)
  const [editDatasetName, setEditDatasetName] = useState('')
  const [editDatasetDescription, setEditDatasetDescription] = useState('')
  const [editDatasetQuestions, setEditDatasetQuestions] = useState('')
  const [updatingDataset, setUpdatingDataset] = useState(false)

  const datasets = useApi(() => getList<EvaluationDataset>('/evaluation/datasets'), [])
  const runs = useApi(() => getList<EvaluationRun>('/evaluation/runs'), [])

  async function runEvaluation() {
    if (!kbId.trim()) {
      setError('Knowledge base ID is required')
      return
    }
    setRunning(true)
    setError(null)
    try {
      const parsed = questions
        .split('\n')
        .map((q) => q.trim())
        .filter(Boolean)
        .map((q) => ({ question: q }))
      const response = await post<EvaluationResult>('/evaluation/evaluate', {
        kb_id: kbId.trim(),
        ...(datasetId ? { dataset_id: datasetId } : {}),
        ...(parsed.length ? { questions: parsed } : {}),
      })
      setResult(response)
      toast.success('Evaluation completed')
      runs.reload()
    } catch (err) {
      setError(extractErrorDetail(err))
      setResult(null)
    } finally {
      setRunning(false)
    }
  }

  async function createDataset() {
    if (!newDatasetName.trim()) {
      setError('Dataset name is required')
      return
    }
    if (!kbId.trim()) {
      setError('Knowledge base ID is required')
      return
    }
    setCreatingDataset(true)
    setError(null)
    try {
      const parsedQuestions = newDatasetQuestions
        .split('\n')
        .map((q) => q.trim())
        .filter(Boolean)
        .map((q) => ({ question: q }))
      
      await post<EvaluationDataset>('/evaluation/datasets', {
        kb_id: kbId.trim(),
        name: newDatasetName.trim(),
        description: newDatasetDescription.trim(),
        questions: parsedQuestions,
      })
      toast.success(`Created dataset "${newDatasetName}"`)
      setNewDatasetName('')
      setNewDatasetDescription('')
      setNewDatasetQuestions('')
      datasets.reload()
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setCreatingDataset(false)
    }
  }

  function startEdit(dataset: EvaluationDataset) {
    setEditingDatasetId(dataset.id ?? '')
    setEditDatasetName(dataset.name ?? '')
    setEditDatasetDescription(dataset.description ?? '')
    setEditDatasetQuestions(
      dataset.questions?.map((q) => q.question).join('\n') ?? ''
    )
  }

  async function updateDataset() {
    if (!editingDatasetId || !editDatasetName.trim()) return
    setUpdatingDataset(true)
    setError(null)
    try {
      const parsedQuestions = editDatasetQuestions
        .split('\n')
        .map((q) => q.trim())
        .filter(Boolean)
        .map((q) => ({ question: q }))
      
      await put<EvaluationDataset>(`/evaluation/datasets/${editingDatasetId}`, {
        name: editDatasetName.trim(),
        description: editDatasetDescription.trim(),
        questions: parsedQuestions,
      })
      toast.success('Dataset updated')
      setEditingDatasetId(null)
      setEditDatasetName('')
      setEditDatasetDescription('')
      setEditDatasetQuestions('')
      datasets.reload()
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setUpdatingDataset(false)
    }
  }

  async function deleteDataset(id: string) {
    if (!confirm('Delete this evaluation dataset?')) return
    try {
      await remove(`/evaluation/datasets/${id}`)
      toast.success('Dataset deleted')
      datasets.reload()
    } catch (err) {
      setError(extractErrorDetail(err))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluation"
        description="Measure retrieval quality against question sets drawn from your data."
        actions={<ReloadButton onClick={() => { datasets.reload(); runs.reload(); }} />}
      />

      {/* Create Dataset Dialog */}
      <Dialog open={creatingDataset} onOpenChange={setCreatingDataset}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Evaluation Dataset</DialogTitle>
            <DialogDescription>
              Add a set of questions to measure retrieval quality against a knowledge base.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-ds-name">Knowledge base ID</Label>
              <Input
                id="new-ds-name"
                placeholder="Paste a knowledge base ID"
                value={kbId}
                onChange={(e) => setKbId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-ds-name2">Dataset name</Label>
              <Input
                id="new-ds-name2"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                placeholder="Product FAQ evaluation"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-ds-desc">Description (optional)</Label>
              <Textarea
                id="new-ds-desc"
                rows={2}
                value={newDatasetDescription}
                onChange={(e) => setNewDatasetDescription(e.target.value)}
                placeholder="What does this dataset measure?"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-ds-questions">Questions (one per line)</Label>
              <Textarea
                id="new-ds-questions"
                rows={5}
                placeholder={'What is our SLA?\nHow do we handle PII?'}
                value={newDatasetQuestions}
                onChange={(e) => setNewDatasetQuestions(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingDataset(false)}>
              Cancel
            </Button>
            <Button onClick={createDataset} disabled={creatingDataset}>
              {creatingDataset ? 'Creating…' : 'Create dataset'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dataset Dialog */}
      {editingDatasetId && (
        <Dialog open onOpenChange={(open) => !open && setEditingDatasetId(null)}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Dataset</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-ds-name">Dataset name</Label>
                <Input
                  id="edit-ds-name"
                  value={editDatasetName}
                  onChange={(e) => setEditDatasetName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-ds-desc">Description (optional)</Label>
                <Textarea
                  id="edit-ds-desc"
                  rows={2}
                  value={editDatasetDescription}
                  onChange={(e) => setEditDatasetDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-ds-questions">Questions (one per line)</Label>
                <Textarea
                  id="edit-ds-questions"
                  rows={5}
                  value={editDatasetQuestions}
                  onChange={(e) => setEditDatasetQuestions(e.target.value)}
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingDatasetId(null)}>
                Cancel
              </Button>
              <Button onClick={updateDataset} disabled={updatingDataset}>
                {updatingDataset ? 'Saving…' : 'Save changes'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Datasets List with CRUD */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-muted-foreground" />
              Datasets
            </CardTitle>
            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  New dataset
                </Button>
              </DialogTrigger>
            </Dialog>
          </CardHeader>
          <CardContent className="pt-0">
            <AsyncBoundary
              loading={datasets.loading}
              error={datasets.error}
              onRetry={datasets.reload}
              isEmpty={!datasets.data?.items.length}
              empty={
                <EmptyState
                  title="No evaluation datasets"
                  description="Create a dataset of questions to measure retrieval quality."
                  action={
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button>
                          <Plus className="mr-2 h-4 w-4" />
                          Create dataset
                        </Button>
                      </DialogTrigger>
                    </Dialog>
                  }
                />
              }
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead className="hidden md:table-cell">Description</TableHead>
                    <TableHead className="text-right">Questions</TableHead>
                    <TableHead className="hidden md:table-cell">Created</TableHead>
                    <TableHead className="text-right w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasets.data?.items.map((ds, index) => (
                    <TableRow key={ds.id ?? index}>
                      <TableCell className="font-medium">{ds.name ?? `Dataset ${index + 1}`}</TableCell>
                      <TableCell className="hidden max-w-[200px] truncate text-muted-foreground md:table-cell">
                        {ds.description ?? '—'}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {ds.question_count ?? ds.questions?.length ?? 0}
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">
                        {ds.created_at ? new Date(ds.created_at).toLocaleDateString() : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setDatasetId(ds.id ?? '')
                              toast.success(`Selected "${ds.name}" for evaluation`)
                            }}
                            title="Use for evaluation"
                          >
                            <FileText className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => startEdit(ds)}
                            title="Edit dataset"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteDataset(ds.id ?? '')}
                            className="text-destructive hover:text-destructive"
                            title="Delete dataset"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </AsyncBoundary>
          </CardContent>
        </Card>

        {/* Run Evaluation */}
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
              <div className="space-y-2 rounded-lg border p-4 bg-muted/30">
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

      {/* Evaluation Runs History */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm font-medium">Evaluation Runs</CardTitle>
          <ReloadButton onClick={runs.reload} />
        </CardHeader>
        <CardContent className="pt-0">
          <AsyncBoundary
            loading={runs.loading}
            error={runs.error}
            onRetry={runs.reload}
            isEmpty={!runs.data?.items.length}
            empty={<EmptyState title="No evaluation runs yet" description="Run an evaluation to see results here." />}
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>Dataset</TableHead>
                  <TableHead>Knowledge Base</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.data?.items.map((run, index) => (
                  <TableRow key={run.id ?? index}>
                    <TableCell className="font-mono text-xs">{run.id ?? `run-${index}`}</TableCell>
                    <TableCell className="text-muted-foreground">{run.dataset_id ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">{run.kb_id ?? '—'}</TableCell>
                    <TableCell className="text-right">
                      {typeof run.overall_score === 'number' ? (
                        <span className="font-semibold">{run.overall_score.toFixed(3)}</span>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={run.status === 'completed' ? 'default' : 'secondary'}>
                        {run.status ?? 'pending'}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {run.created_at ? new Date(run.created_at).toLocaleDateString() : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
        </CardContent>
      </Card>
    </div>
  )
}