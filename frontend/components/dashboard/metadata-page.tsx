'use client'

import Link from 'next/link'
import { FileText, Plus } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getList } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface MetadataSchema {
  id?: string
  name?: string
  description?: string
  /** Backend returns a free-form mapping, not an array. */
  taxonomy?: Record<string, unknown> | string[] | null
  is_active?: boolean
  kb_id?: string
}

/** Renders taxonomy as badges whether the API sends a map or a list. */
function taxonomyTags(taxonomy: MetadataSchema['taxonomy']): string[] {
  if (!taxonomy) return []
  if (Array.isArray(taxonomy)) return taxonomy.map(String)
  return Object.keys(taxonomy)
}

export function MetadataPage() {
  const schemas = useApi(() => getList<MetadataSchema>('/metadata/'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Datasets & Schemas"
        description="Register metadata schemas to describe and validate your datasets."
        actions={<ReloadButton onClick={schemas.reload} />}
      />

      <AsyncBoundary
        loading={schemas.loading}
        error={schemas.error}
        onRetry={schemas.reload}
        isEmpty={!schemas.data?.items.length}
        empty={
          <EmptyState
            title="No schemas registered"
            description="Define a schema to describe the shape of a dataset before ingesting it."
            action={
              <Button asChild>
                <Link href="/dashboard/knowledge">
                  <Plus className="mr-2 h-4 w-4" />
                  Create knowledge base first
                </Link>
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
                  <TableHead>Description</TableHead>
                  <TableHead>Taxonomy</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schemas.data?.items.map((schema, index) => (
                  <TableRow key={schema.id ?? index}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {schema.name ?? `Schema ${index + 1}`}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-muted-foreground">
                      {schema.description ?? '—'}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {taxonomyTags(schema.taxonomy).length === 0 ? (
                          <span className="text-muted-foreground">—</span>
                        ) : (
                          taxonomyTags(schema.taxonomy).map((tag) => (
                            <Badge key={tag} variant="outline">
                              {tag}
                            </Badge>
                          ))
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={schema.is_active === false ? 'secondary' : 'default'}>
                        {schema.is_active === false ? 'Inactive' : 'Active'}
                      </Badge>
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