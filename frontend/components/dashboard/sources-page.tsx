'use client'

import Link from 'next/link'
import { Database, HardDrive, Plus } from 'lucide-react'

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
import { getList } from '@/lib/api/data'
import { listStorageObjects } from '@/lib/api/platform'
import type { StorageObject } from '@/types/platform'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface Source {
  id?: string
  name?: string
  type?: string
  status?: string
  is_active?: boolean
  description?: string
}

export function SourcesPage() {
  const sources = useApi(() => getList<Source>('/connectors/sources'), [])
  const storage = useApi(() => listStorageObjects(undefined, '', 20), [])

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const objects: StorageObject[] = storage.data?.objects ?? []

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Sources"
        description="Connect databases, warehouses and object stores, then trigger syncs."
        actions={
          <>
            <ReloadButton onClick={sources.reload} />
            <Button asChild>
              <Link href="/dashboard/connectors">
                <Plus className="mr-2 h-4 w-4" />
                Add source
              </Link>
            </Button>
          </>
        }
      />

      <AsyncBoundary
        loading={sources.loading}
        error={sources.error}
        onRetry={sources.reload}
        isEmpty={!sources.data?.items.length}
        empty={
          <EmptyState
            title="No data sources yet"
            description="Connect your first source to start ingesting data into DataAir."
            action={
              <Button asChild>
                <Link href="/dashboard/connectors">Browse connectors</Link>
              </Button>
            }
          />
        }
      >
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.data?.items.map((source, index) => (
                  <TableRow key={source.id ?? index}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        {source.name ?? `Source ${index + 1}`}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {source.type ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={source.is_active === false ? 'secondary' : 'default'}>
                        {source.status ?? (source.is_active === false ? 'Inactive' : 'Active')}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden max-w-xs truncate text-muted-foreground md:table-cell">
                      {source.description ?? '—'}
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
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <HardDrive className="h-4 w-4 text-muted-foreground" />
            Object storage (MinIO)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AsyncBoundary
            loading={storage.loading}
            error={storage.error}
            onRetry={storage.reload}
            isEmpty={!objects.length}
            empty={
              <p className="py-6 text-center text-sm text-muted-foreground">
                No objects in the landing bucket yet.
              </p>
            }
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Key</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead className="hidden md:table-cell">Last modified</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {objects.map((object) => (
                  <TableRow key={object.key}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        {object.key}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatBytes(object.size)}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {object.last_modified
                        ? new Date(object.last_modified).toLocaleString()
                        : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AsyncBoundary>
          <p className="mt-3 text-xs text-muted-foreground">
            {storage.data?.bucket
              ? `Bucket: ${storage.data.bucket} · ${storage.data.count} objects`
              : ''}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}