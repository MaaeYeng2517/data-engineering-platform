'use client'

import { useMemo, useState } from 'react'
import { Database, Play, RefreshCw, Trash2, Wrench } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getList, post, patch, remove } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { toast } from 'sonner'

interface DataSource {
  id?: string
  kb_id?: string
  name?: string
  source_type?: string
  config?: Record<string, unknown>
  is_active?: boolean
  last_sync?: string | null
  sync_status?: string
  created_at?: string
  updated_at?: string
}

interface KnowledgeBase {
  id?: string
  name?: string
}

const SOURCE_TYPES = [
  { value: 'postgres', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 's3', label: 'S3 / MinIO' },
  { value: 'api', label: 'REST API' },
  { value: 'kafka', label: 'Kafka' },
  { value: 'mongodb', label: 'MongoDB' },
  { value: 'redis', label: 'Redis' },
  { value: 'elasticsearch', label: 'Elasticsearch' },
  { value: 'bigquery', label: 'BigQuery' },
  { value: 'snowflake', label: 'Snowflake' },
]

function statusBadge(status?: string) {
  switch (status) {
    case 'success':
      return <Badge variant="default">Success</Badge>
    case 'running':
      return <Badge variant="secondary">Running</Badge>
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>
    case 'idle':
      return <Badge variant="outline">Idle</Badge>
    default:
      return <Badge variant="outline">{status ?? '—'}</Badge>
  }
}

function SourceTypeBadge({ type }: { type?: string }) {
  const found = SOURCE_TYPES.find(t => t.value === type)
  return <Badge variant="outline">{found?.label ?? type ?? '—'}</Badge>
}

export function SourcesPage() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({
    kb_id: '',
    name: '',
    source_type: 'postgres',
    config: {},
  })
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<Partial<DataSource>>({})
  const [busyId, setBusyId] = useState<string | null>(null)

  const sources = useApi(() => getList<DataSource>('/connectors/sources'), [])
  const knowledgeBases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])

  const filtered = useMemo(() => {
    let items = sources.data?.items ?? []
    if (search.trim()) {
      const q = search.toLowerCase()
      items = items.filter((s) =>
        [s.name, s.source_type, s.kb_id].filter(Boolean).some((f) => String(f).toLowerCase().includes(q))
      )
    }
    if (typeFilter) {
      items = items.filter((s) => s.source_type === typeFilter)
    }
    return items
  }, [sources.data, search, typeFilter])

  const kbOptions = useMemo(() =>
    (knowledgeBases.data?.items ?? []).map((kb) => ({ value: kb.id!, label: kb.name! }))
  , [knowledgeBases.data])

  async function handleCreate() {
    if (!createForm.kb_id || !createForm.name || !createForm.source_type) {
      toast.error('Knowledge base, name and type are required')
      return
    }
    setBusyId('create')
    try {
      await post('/connectors/sources', createForm)
      toast.success('Source created')
      setShowCreate(false)
      setCreateForm({ kb_id: '', name: '', source_type: 'postgres', config: {} })
      sources.reload()
    } catch (err) {
      toast.error('Failed to create source')
    } finally {
      setBusyId(null)
    }
  }

  async function handleEdit(source: DataSource) {
    setEditingId(source.id!)
    setEditForm({ name: source.name, config: source.config, is_active: source.is_active })
  }

  async function handleSaveEdit(source: DataSource) {
    setBusyId(source.id!)
    try {
      await patch(`/connectors/sources/${source.id}`, editForm)
      toast.success('Source updated')
      setEditingId(null)
      setEditForm({})
      sources.reload()
    } catch (err) {
      toast.error('Failed to update source')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this source?')) return
    setBusyId(id)
    try {
      await remove(`/connectors/sources/${id}`)
      toast.success('Source deleted')
      sources.reload()
    } catch (err) {
      toast.error('Failed to delete source')
    } finally {
      setBusyId(null)
    }
  }

  async function handleSync(source: DataSource) {
    setBusyId(source.id!)
    try {
      await post(`/connectors/sources/${source.id}/sync`)
      toast.success('Sync started')
      sources.reload()
    } catch (err) {
      toast.error('Sync failed')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Sources"
        description="Configure connectors to ingest data from external systems into knowledge bases."
        actions={
          <>
            <ReloadButton onClick={sources.reload} />
            <Button onClick={() => setShowCreate(true)}>
              <Database className="mr-2 h-4 w-4" />
              Add Source
            </Button>
          </>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-2">
          <Label htmlFor="source-search">Search sources</Label>
          <Input
            id="source-search"
            placeholder="Filter by name, type, KB…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="source-type-filter">Type</Label>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger id="source-type-filter">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All types</SelectItem>
              {SOURCE_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {showCreate && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Create Data Source</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="create-kb">Knowledge Base *</Label>
                <Select value={createForm.kb_id} onValueChange={(v) => setCreateForm({ ...createForm, kb_id: v })}>
                  <SelectTrigger id="create-kb">
                    <SelectValue placeholder="Select KB" />
                  </SelectTrigger>
                  <SelectContent>
                    {kbOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-type">Source Type *</Label>
                <Select value={createForm.source_type} onValueChange={(v) => setCreateForm({ ...createForm, source_type: v })}>
                  <SelectTrigger id="create-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SOURCE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="create-name">Name *</Label>
                <Input
                  id="create-name"
                  placeholder="e.g. production-db, s3-raw-logs"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                />
              </div>
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="create-config">Config (JSON)</Label>
                <textarea
                  id="create-config"
                  className="font-mono text-sm p-2 border rounded-md"
                  rows={4}
                  placeholder='{"host": "localhost", "port": 5432, "database": "mydb", "username": "user", "password": "***"}'
                  value={JSON.stringify(createForm.config, null, 2)}
                  onChange={(e) => {
                    try {
                      setCreateForm({ ...createForm, config: JSON.parse(e.target.value) })
                    } catch {}
                  }}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={busyId === 'create'}>
                {busyId === 'create' ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : 'Create'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <AsyncBoundary
        loading={sources.loading}
        error={sources.error}
        onRetry={sources.reload}
        isEmpty={!filtered.length}
        empty={
          <EmptyState
            title="No data sources"
            description={
              search || typeFilter
                ? 'No sources match your filters.'
                : 'Create a source to start ingesting data from external systems.'
            }
            action={!search && !typeFilter ? (
              <Button onClick={() => setShowCreate(true)}>
                <Database className="mr-2 h-4 w-4" />
                Add Source
              </Button>
            ) : null}
          />
        }
      >
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((source, index) => (
            <Card key={source.id ?? index}>
              {editingId === source.id ? (
                <CardContent className="space-y-4 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Edit {source.name}</h3>
                    <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}>Cancel</Button>
                  </div>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor={`edit-name-${source.id}`}>Name</Label>
                      <Input
                        id={`edit-name-${source.id}`}
                        value={editForm.name ?? ''}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`edit-active-${source.id}`}>Active</Label>
                      <Select
                        value={String(editForm.is_active ?? source.is_active ?? true)}
                        onValueChange={(v) => setEditForm({ ...editForm, is_active: v === 'true' })}
                      >
                        <SelectTrigger id={`edit-active-${source.id}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="true">Yes</SelectItem>
                          <SelectItem value="false">No</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`edit-config-${source.id}`}>Config (JSON)</Label>
                      <textarea
                        id={`edit-config-${source.id}`}
                        className="font-mono text-sm p-2 border rounded-md"
                        rows={3}
                        value={JSON.stringify(editForm.config ?? source.config ?? {}, null, 2)}
                        onChange={(e) => {
                          try {
                            setEditForm({ ...editForm, config: JSON.parse(e.target.value) })
                          } catch {}
                        }}
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button onClick={() => handleSaveEdit(source)} disabled={busyId === source.id}>
                      {busyId === source.id ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : 'Save'}
                    </Button>
                  </div>
                </CardContent>
              ) : (
                <>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        {source.name ?? `Source ${index + 1}`}
                      </CardTitle>
                      <SourceTypeBadge type={source.source_type} />
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span className="font-mono text-xs">{source.kb_id?.slice(0, 8)}…</span>
                      <span>{statusBadge(source.sync_status)}</span>
                    </div>
                    {source.last_sync && (
                      <p className="text-xs text-muted-foreground">
                        Last sync: {new Date(source.last_sync).toLocaleString()}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSync(source)}
                        disabled={busyId === source.id}
                        title="Trigger sync"
                      >
                        {busyId === source.id ? (
                          <RefreshCw className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        Sync
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEdit(source)}
                        title="Edit"
                      >
                        <Wrench className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        onClick={() => handleDelete(source.id!)}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </>
              )}
            </Card>
          ))}
        </div>
      </AsyncBoundary>
    </div>
  )
}