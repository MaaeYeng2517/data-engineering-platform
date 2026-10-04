'use client'

import { useMemo, useState } from 'react'
import { Plus, RefreshCw, Trash2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
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
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface ConnectorType {
  id?: string
  name?: string
  type?: string
  description?: string
  category?: string
}

/**
 * Reads the connector catalogue. The API wraps it as {types: [...]}, which the
 * shared normalizer does not unwrap, so map it explicitly.
 */
export function ConnectorsPage() {
  const [search, setSearch] = useState('')
  const types = useApi(() => getList<ConnectorType>('/connectors/types'), [])

  const filtered = useMemo(() => {
    const items = types.data?.items ?? []
    if (!search.trim()) return items
    const q = search.toLowerCase()
    return items.filter((item) =>
      [item.name, item.type, item.description, item.category]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(q))
    )
  }, [types.data, search])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Connectors"
        description="Supported source types available to ingest data into DataAir."
        actions={<ReloadButton onClick={types.reload} />}
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 space-y-2">
          <Label htmlFor="connector-search">Search connectors</Label>
          <Input
            id="connector-search"
            placeholder="Filter by name, type or category…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <AsyncBoundary
        loading={types.loading}
        error={types.error}
        onRetry={types.reload}
        isEmpty={!filtered.length}
        empty={
          <EmptyState
            title="No connectors found"
            description={
              search
                ? 'No connectors match your search.'
                : 'No connector types are registered in this deployment.'
            }
          />
        }
      >
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((connector, index) => (
            <Card key={connector.id ?? connector.type ?? index}>
              <CardContent className="space-y-2 p-5">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium">
                    {connector.name ?? connector.type ?? 'Connector'}
                  </h3>
                  {connector.category && (
                    <Badge variant="secondary">{connector.category}</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {connector.description ?? 'No description provided.'}
                </p>
                {connector.type && (
                  <p className="text-xs text-muted-foreground">
                    Type: <span className="font-mono">{connector.type}</span>
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </AsyncBoundary>
    </div>
  )
}