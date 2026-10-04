'use client'

import { useState } from 'react'
import { Trash2 } from 'lucide-react'

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
import { getList, remove } from '@/lib/api/data'
import { CreateApiKeyDialog } from './create-api-key-dialog'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface ApiKeyRecord {
  id?: string
  name?: string
  key_prefix?: string
  scopes?: string[]
  is_active?: boolean
  last_used_at?: string
  expires_at?: string
  created_at?: string
}

interface UsageRecord {
  id?: string
  endpoint?: string
  method?: string
  status_code?: number
  latency_ms?: number
  created_at?: string
}

export function ApiKeysPage() {
  const keys = useApi(() => getList<ApiKeyRecord>('/api-keys'), [])
  const usage = useApi(() => getList<UsageRecord>('/api-keys/usage'), [])
  const [revoking, setRevoking] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function revoke(id: string) {
    setRevoking(id)
    setActionError(null)
    try {
      await remove(`/api-keys/${id}`)
      keys.reload()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setActionError(e.response?.data?.detail ?? 'Failed to revoke key')
    } finally {
      setRevoking(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="API Keys"
        description="Programmatic access to the platform. Keys are shown once at creation."
        actions={
          <>
            <ReloadButton
              onClick={() => {
                keys.reload()
                usage.reload()
              }}
            />
            <CreateApiKeyDialog onCreated={keys.reload} />
          </>
        }
      />

      {actionError && (
        <p className="text-sm text-destructive">{actionError}</p>
      )}

      <AsyncBoundary
        loading={keys.loading}
        error={keys.error}
        onRetry={keys.reload}
        isEmpty={!keys.data?.items.length}
        empty={
          <EmptyState
            title="No API keys"
            description="Create an API key to call the platform programmatically."
          />
        }
      >
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Prefix</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Last used</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.data?.items.map((key, index) => (
                  <TableRow key={key.id ?? index}>
                    <TableCell className="font-medium">
                      {key.name ?? `Key ${index + 1}`}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {key.key_prefix ?? '—'}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {(key.scopes ?? []).length === 0 ? (
                          <span className="text-muted-foreground">—</span>
                        ) : (
                          key.scopes?.map((scope) => (
                            <Badge key={scope} variant="outline">
                              {scope}
                            </Badge>
                          ))
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {key.last_used_at
                        ? new Date(key.last_used_at).toLocaleString()
                        : 'Never'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={key.is_active === false ? 'secondary' : 'default'}>
                        {key.is_active === false ? 'Revoked' : 'Active'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {key.id && (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={revoking === key.id}
                          onClick={() => revoke(key.id as string)}
                          aria-label={`Revoke ${key.name ?? 'API key'}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
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
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">
            Recent API usage ({usage.data?.items.length ?? 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AsyncBoundary
            loading={usage.loading}
            error={usage.error}
            onRetry={usage.reload}
            isEmpty={!usage.data?.items.length}
            empty={
              <p className="py-6 text-center text-sm text-muted-foreground">
                No API calls recorded yet.
              </p>
            }
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Method</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Latency</TableHead>
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
                        variant={
                          log.status_code && log.status_code >= 400 ? 'destructive' : 'secondary'
                        }
                      >
                        {log.status_code ?? '—'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {log.latency_ms != null ? `${log.latency_ms}ms` : '—'}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
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