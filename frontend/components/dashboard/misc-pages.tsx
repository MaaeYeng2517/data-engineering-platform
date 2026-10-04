'use client'

import { useState } from 'react'
import {
  Activity,
  AlertCircle,
  Bell,
  CheckCircle2,
  Clock,
  ExternalLink,
  GitBranch,
  Info,
  MessageSquare,
  Search,
  Send,
  Settings as SettingsIcon,
  Table2,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { extractErrorDetail, getList, post } from '@/lib/api/data'
import { listCatalogTables, searchCatalog } from '@/lib/api/platform'
import type { CatalogTable } from '@/types/platform'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'
import { useAuth } from '@/providers/auth-provider'

/** Informational pages that describe a capability without a dedicated list endpoint. */
export function ActivityPage() {
  const usage = useApi(
    () => getList<{ id?: string; endpoint?: string; method?: string; status_code?: number; created_at?: string }>(
      '/api-keys/usage'
    ),
    []
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity"
        description="Recent API activity recorded against your workspace."
        actions={<ReloadButton onClick={usage.reload} />}
      />
      <AsyncBoundary
        loading={usage.loading}
        error={usage.error}
        onRetry={usage.reload}
        isEmpty={!usage.data?.items.length}
        empty={
          <EmptyState
            title="No activity yet"
            description="API calls made with your keys will appear here."
          />
        }
      >
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Method</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usage.data?.items.map((log, index) => (
                  <TableRow key={log.id ?? index}>
                    <TableCell className="font-mono text-xs font-medium">
                      {log.method ?? '—'}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {log.endpoint ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={log.status_code && log.status_code >= 400 ? 'destructive' : 'secondary'}
                      >
                        {log.status_code ?? '—'}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </AsyncBoundary>
    </div>
  )
}

export function LineagePage() {
  const [query, setQuery] = useState('')
  const tables = useApi(() => listCatalogTables(50), [])
  const searchResults = useApi(
    () => (query.trim() ? searchCatalog(query.trim()) : Promise.resolve([])),
    [query]
  )

  const shownTables: CatalogTable[] = query.trim()
    ? (searchResults.data ?? [])
    : (tables.data ?? [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Lineage"
        description="Catalog assets and lineage from OpenMetadata."
        actions={<ReloadButton onClick={tables.reload} />}
      />

      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search tables, dashboards, topics…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => searchResults.reload()}
              disabled={!query.trim()}
            >
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      <AsyncBoundary
        loading={query.trim() ? searchResults.loading : tables.loading}
        error={query.trim() ? searchResults.error : tables.error}
        onRetry={() => (query.trim() ? searchResults.reload() : tables.reload())}
        isEmpty={!shownTables.length}
        empty={
          <p className="py-8 text-center text-sm text-muted-foreground">
            {query.trim()
              ? 'No catalog assets match your search.'
              : 'No tables in the catalog yet. The OpenMetadata ingestion service publishes the warehouse and MinIO metadata.'}
          </p>
        }
      >
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Table2 className="h-4 w-4 text-muted-foreground" />
              {query.trim() ? 'Search results' : 'Catalog tables'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden md:table-cell">Description</TableHead>
                  <TableHead className="hidden w-10 md:table-cell" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {shownTables.map((asset, index) => (
                  <TableRow key={asset.fully_qualified_name ?? asset.name ?? index}>
                    <TableCell className="font-medium">
                      {asset.name ?? '—'}
                      {asset.fully_qualified_name && (
                        <p className="font-mono text-xs font-normal text-muted-foreground">
                          {asset.fully_qualified_name}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{asset.type ?? asset.table_type ?? 'table'}</Badge>
                    </TableCell>
                    <TableCell className="hidden max-w-xs truncate text-sm text-muted-foreground md:table-cell">
                      {asset.description || '—'}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {asset.url ? (
                        <Button size="sm" variant="ghost" asChild>
                          <a href={asset.url} target="_blank" rel="noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </AsyncBoundary>

      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <GitBranch className="h-6 w-6" />
          </div>
          <p className="font-medium">Column-level lineage</p>
          <p className="max-w-md text-sm text-muted-foreground">
            Lineage edges are captured by the OpenMetadata ingestion workflows
            (dbt manifest, warehouse and MinIO metadata) and rendered in the
            catalog UI above.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export function ApprovalsPage() {
  const [kbId, setKbId] = useState('')
  const [docId, setDocId] = useState('')
  const [reviewers, setReviewers] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)

  async function submit() {
    const reviewerIds = reviewers
      .split(',')
      .map((r) => r.trim())
      .filter(Boolean)
    if (!kbId.trim() || !docId.trim()) {
      setResult({ kind: 'error', text: 'Knowledge base and document IDs are required' })
      return
    }
    if (reviewerIds.length === 0) {
      setResult({ kind: 'error', text: 'Add at least one reviewer ID' })
      return
    }
    setSubmitting(true)
    setResult(null)
    try {
      // This endpoint declares plain scalars, so FastAPI expects query
      // parameters (repeat `reviewers` per entry), not a JSON body.
      await post('/governance/approvals', undefined, {
        params: {
          kb_id: kbId.trim(),
          document_id: docId.trim(),
          creator_id: user?.id ?? '',
          reviewers: reviewerIds,
        },
      })
      setResult({ kind: 'ok', text: 'Submitted for approval.' })
      setKbId('')
      setDocId('')
      setReviewers('')
    } catch (err) {
      setResult({ kind: 'error', text: extractErrorDetail(err) })
    } finally {
      setSubmitting(false)
    }
  }

  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Queue"
        description="Documents and changes awaiting reviewer sign-off before publication."
      />
      <Card>
        <CardContent className="pt-6">
          <div className="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
            <Info className="h-4 w-4" />
            Submitting as {user?.email ?? 'the current user'}.
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="appr-kb">Knowledge base ID</Label>
              <Input
                id="appr-kb"
                placeholder="Knowledge base UUID"
                value={kbId}
                onChange={(e) => setKbId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appr-doc">Document ID</Label>
              <Input
                id="appr-doc"
                placeholder="Document UUID"
                value={docId}
                onChange={(e) => setDocId(e.target.value)}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="appr-rev">Reviewer IDs (comma separated)</Label>
              <Input
                id="appr-rev"
                placeholder="uuid-1, uuid-2"
                value={reviewers}
                onChange={(e) => setReviewers(e.target.value)}
              />
            </div>
          </div>
          <Button className="mt-4" onClick={submit} disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit for approval'}
          </Button>
          {result && (
            <p
              className={`mt-3 flex items-center gap-2 text-sm ${
                result.kind === 'ok' ? 'text-primary' : 'text-destructive'
              }`}
            >
              {result.kind === 'ok' ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              {result.text}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function AuditPage() {
  const audit = useApi(() => getList<Record<string, unknown>>('/governance/audit'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Log"
        description="Immutable record of actions taken across your workspace."
        actions={<ReloadButton onClick={audit.reload} />}
      />
      <AsyncBoundary
        loading={audit.loading}
        error={audit.error}
        onRetry={audit.reload}
        isEmpty={!audit.data?.items.length}
        empty={
          <EmptyState
            title="No audit entries"
            description="Administrative and governance actions are recorded here as they occur."
          />
        }
      >
        <Card>
          <CardContent className="pt-6">
            <pre className="max-h-96 overflow-auto rounded-lg bg-muted p-4 text-xs">
              {JSON.stringify(audit.data?.items, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </AsyncBoundary>
    </div>
  )
}

export function ConfigurationPage() {
  const connectors = useApi(() => getList<{ name?: string; type?: string }>('/connectors/types'), [])
  const roles = useApi(() => getList<{ role?: string }>('/governance/roles'), [])

  const settings = [
    { label: 'API base URL', value: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1' },
    { label: 'Connector types', value: String(connectors.data?.items.length ?? 0) },
    { label: 'Governance roles', value: String(roles.data?.items.length ?? 0) },
    { label: 'CSRF protection', value: 'Enabled' },
    { label: 'Session strategy', value: 'HTTP-only cookies' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Configuration"
        description="Runtime configuration reported by the platform."
        actions={
          <ReloadButton
            onClick={() => {
              connectors.reload()
              roles.reload()
            }}
          />
        }
      />
      <Card>
        <CardContent className="pt-6">
          <dl className="space-y-0">
            {settings.map((setting, index) => (
              <div key={setting.label}>
                {index > 0 && <Separator className="my-3" />}
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <dt className="text-sm text-muted-foreground">{setting.label}</dt>
                  <dd className="font-mono text-sm">{setting.value}</dd>
                </div>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}

export function TeamPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Members"
        description="Members of your workspace and the roles they hold."
      />
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between gap-3 rounded-lg border p-4">
            <div>
              <p className="font-medium">{user?.full_name || 'You'}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
            </div>
            <Badge variant="secondary">{user?.role ?? 'member'}</Badge>
          </div>
          <p className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <SettingsIcon className="h-4 w-4" />
            Viewing the full member directory requires an admin account. Ask a workspace
            admin to grant access.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export function SupportPage() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [status, setStatus] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)
  const [sending, setSending] = useState(false)

  async function submit() {
    setSending(true)
    setStatus(null)
    try {
      await post('/contact', form)
      setStatus({ kind: 'ok', text: 'Thanks — your message has been received.' })
      setForm({ name: '', email: '', subject: '', message: '' })
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setStatus({ kind: 'error', text: e.response?.data?.detail ?? 'Failed to send message' })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Support"
        description="Send a message to the DataAir team and track your history."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              Contact us
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="sup-name">Name</Label>
                <Input
                  id="sup-name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sup-email">Email</Label>
                <Input
                  id="sup-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="sup-subject">Subject</Label>
              <Input
                id="sup-subject"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sup-message">Message</Label>
              <Textarea
                id="sup-message"
                rows={5}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
              />
            </div>
            <Button onClick={submit} disabled={sending}>
              <Send className="mr-2 h-4 w-4" />
              {sending ? 'Sending…' : 'Send message'}
            </Button>
            {status && (
              <p
                className={`flex items-center gap-2 text-sm ${
                  status.kind === 'ok' ? 'text-primary' : 'text-destructive'
                }`}
              >
                {status.kind === 'ok' ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                {status.text}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Clock className="h-4 w-4 text-muted-foreground" />
              Your messages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SupportHistory />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function SupportHistory() {
  const messages = useApi(
    () => getList<{ id?: string; subject?: string; status?: string; created_at?: string }>('/contact/mine'),
    []
  )

  return (
    <AsyncBoundary
      loading={messages.loading}
      error={messages.error}
      onRetry={messages.reload}
      isEmpty={!messages.data?.items.length}
      empty={
        <p className="py-6 text-center text-sm text-muted-foreground">
          No support requests yet.
        </p>
      }
    >
      <ul className="space-y-3">
        {messages.data?.items.map((message, index) => (
          <li key={message.id ?? index} className="rounded-lg border p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium">{message.subject ?? `Request ${index + 1}`}</p>
              <Badge variant="secondary">{message.status ?? 'new'}</Badge>
            </div>
            {message.created_at && (
              <p className="mt-1 text-xs text-muted-foreground">
                {new Date(message.created_at).toLocaleString()}
              </p>
            )}
          </li>
        ))}
      </ul>
    </AsyncBoundary>
  )
}