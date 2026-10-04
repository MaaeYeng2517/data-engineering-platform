'use client'

import { useState } from 'react'
import {
  CalendarClock,
  ChevronDown,
  ExternalLink,
  FileCode2,
  Play,
  RefreshCw,
  Square,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AsyncBoundary,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { toast } from 'sonner'
import {
  listDagRuns,
  listDagRunTasks,
  listDags,
  setDagPaused,
  triggerDag,
} from '@/lib/api/platform'
import type { Dag, DagRun, TaskInstance } from '@/types/platform'

function stateVariant(state?: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (state) {
    case 'success':
      return 'default'
    case 'running':
    case 'queued':
    case 'up_for_retry':
      return 'secondary'
    case 'failed':
      return 'destructive'
    default:
      return 'outline'
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function DagDetail({ dag }: { dag: Dag }) {
  const [open, setOpen] = useState(false)
  const runs = useApi(() => listDagRuns(dag.dag_id), [dag.dag_id, open])
  const [expandedRun, setExpandedRun] = useState<string | null>(null)

  return (
    <div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen((value) => !value)}
      >
        <ChevronDown
          className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`}
        />
        {open ? 'Hide' : 'Show'} runs
      </Button>
      {open && (
        <div className="space-y-4 pt-2">
          <AsyncBoundary
            loading={runs.loading}
            error={runs.error}
            onRetry={runs.reload}
            isEmpty={!runs.data?.length}
            empty={<p className="py-4 text-center text-sm text-muted-foreground">No runs recorded.</p>}
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>Execution date</TableHead>
                  <TableHead>Tasks</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.data?.slice(0, 10).map((run: DagRun) => (
                  <RunRow
                    key={run.run_id}
                    dagId={dag.dag_id}
                    run={run}
                    expanded={expandedRun === run.run_id}
                    onToggle={() =>
                      setExpandedRun(expandedRun === run.run_id ? null : run.run_id)
                    }
                  />
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
        </div>
      )}
    </div>
  )
}

function RunRow({
  dagId,
  run,
  expanded,
  onToggle,
}: {
  dagId: string
  run: DagRun
  expanded: boolean
  onToggle: () => void
}) {
  const tasks = useApi(
    () => listDagRunTasks(dagId, run.run_id),
    [dagId, run.run_id, expanded]
  )

  return (
    <>
      <TableRow>
        <TableCell className="font-mono text-xs">{run.run_id}</TableCell>
        <TableCell>
          <Badge variant={stateVariant(run.state)}>{run.state ?? '—'}</Badge>
        </TableCell>
        <TableCell className="text-muted-foreground">
          {run.execution_date
            ? new Date(run.execution_date).toLocaleString()
            : '—'}
        </TableCell>
        <TableCell>
          <Button variant="ghost" size="sm" onClick={onToggle}>
            {expanded ? 'Hide' : 'Tasks'}
          </Button>
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow>
          <TableCell colSpan={4}>
            {tasks.loading ? (
              <p className="py-2 text-sm text-muted-foreground">Loading tasks…</p>
            ) : (
              <div className="flex flex-wrap gap-2 py-2">
                {(tasks.data ?? []).map((task: TaskInstance) => (
                  <Badge
                    key={task.task_id}
                    variant={stateVariant(task.state)}
                    className="font-mono text-xs"
                    title={`${task.operator ?? 'task'} · try ${task.try_number ?? 1}`}
                  >
                    {task.task_id}: {task.state ?? 'no-state'}
                  </Badge>
                ))}
              </div>
            )}
          </TableCell>
        </TableRow>
      )}
    </>
  )
}

export function PipelinesPage() {
  const dags = useApi(() => listDags(), [])
  const [busy, setBusy] = useState<string | null>(null)

  async function handleTrigger(dagId: string) {
    setBusy(dagId)
    try {
      await triggerDag(dagId)
      toast.success(`Triggered ${dagId}`)
      dags.reload()
    } catch (err) {
      toast.error(`Failed to trigger ${dagId}`)
    } finally {
      setBusy(null)
    }
  }

  async function handleTogglePause(dag: Dag) {
    try {
      await setDagPaused(dag.dag_id, !dag.is_paused)
      dags.reload()
    } catch {
      toast.error('Failed to update DAG')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pipelines"
        description="Airflow DAGs orchestrating ingestion, dbt builds, quality gates and catalog sync."
        actions={<ReloadButton onClick={dags.reload} />}
      />

      <AsyncBoundary
        loading={dags.loading}
        error={dags.error}
        onRetry={dags.reload}
        isEmpty={!dags.data?.length}
        empty={
          <p className="py-8 text-center text-sm text-muted-foreground">
            No DAGs registered in Airflow.
          </p>
        }
      >
        <div className="space-y-4">
          {dags.data?.map((dag: Dag) => (
            <Card key={dag.dag_id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <CardTitle className="flex flex-wrap items-center gap-2 font-mono text-base">
                      {dag.dag_id}
                      <Badge variant={dag.is_paused ? 'secondary' : 'default'}>
                        {dag.is_paused ? 'Paused' : 'Active'}
                      </Badge>
                    </CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {dag.description ?? 'No description'}
                    </p>
                  </div>
                  <div className="flex flex-shrink-0 gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleTrigger(dag.dag_id)}
                      disabled={busy === dag.dag_id}
                    >
                      {busy === dag.dag_id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      Trigger
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleTogglePause(dag)}
                    >
                      <Square className="h-4 w-4" />
                      {dag.is_paused ? 'Unpause' : 'Pause'}
                    </Button>
                    {dag.url && (
                      <Button size="sm" variant="ghost" asChild>
                        <a href={dag.url} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <CalendarClock className="h-3.5 w-3.5" />
                    {dag.schedule ?? '—'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <FileCode2 className="h-3.5 w-3.5" />
                    {dag.file_path?.split('/').pop() ?? '—'}
                  </span>
                  {dag.tags?.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <DagDetail dag={dag} />
              </CardContent>
            </Card>
          ))}
        </div>
      </AsyncBoundary>
    </div>
  )
}
