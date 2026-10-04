'use client'

import { useState } from 'react'
import { BookOpen } from 'lucide-react'

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
import { CreateKnowledgeBaseDialog } from './create-kb-dialog'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface KnowledgeBase {
  id?: string
  name?: string
  description?: string
  status?: string
  version?: string
  is_published?: boolean
  created_at?: string
}

export function KnowledgeBasesPage() {
  const bases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Bases"
        description="Curated document collections that power search and retrieval."
        actions={
          <>
            <ReloadButton onClick={bases.reload} />
            <CreateKnowledgeBaseDialog onCreated={bases.reload} />
          </>
        }
      />

      <AsyncBoundary
        loading={bases.loading}
        error={bases.error}
        onRetry={bases.reload}
        isEmpty={!bases.data?.items.length}
        empty={
          <EmptyState
            title="No knowledge bases yet"
            description="Create a knowledge base to group documents, schemas and workflows for retrieval."
            action={<CreateKnowledgeBaseDialog onCreated={bases.reload} />}
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
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bases.data?.items.map((kb, index) => (
                  <TableRow key={kb.id ?? index}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-muted-foreground" />
                        {kb.name ?? `Knowledge base ${index + 1}`}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-sm truncate text-muted-foreground">
                      {kb.description ?? '—'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {kb.version ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={kb.is_published ? 'default' : 'secondary'}>
                        {kb.is_published ? 'Published' : (kb.status ?? 'Draft')}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {kb.created_at
                        ? new Date(kb.created_at).toLocaleDateString()
                        : '—'}
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