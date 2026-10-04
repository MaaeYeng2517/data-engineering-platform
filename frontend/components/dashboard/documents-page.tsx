'use client'

import { useState } from 'react'
import { BookOpen, FileText } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getList } from '@/lib/api/data'
import { UploadDocumentDialog } from './upload-document-dialog'
import { DocumentGuide } from './document-guide'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface DocumentRecord {
  id?: string
  kb_id?: string
  title?: string
  source_type?: string
  status?: string
  version?: string
  is_published?: boolean
  created_at?: string
}

interface KnowledgeBase {
  id?: string
  name?: string
}

export function DocumentsPage() {
  const [kbFilter, setKbFilter] = useState<string>('all')
  const knowledgeBases = useApi(() => getList<KnowledgeBase>('/knowledge-bases/'), [])
  const documents = useApi(
    () =>
      getList<DocumentRecord>(
        '/documents/',
        kbFilter === 'all' ? undefined : { params: { kb_id: kbFilter } }
      ),
    [kbFilter]
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="Documents"
        description="Files ingested into your knowledge bases, with version and publish state."
        actions={
          <>
            <ReloadButton onClick={documents.reload} />
            <UploadDocumentDialog onUploaded={documents.reload} />
          </>
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Filter by knowledge base</CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={kbFilter} onValueChange={setKbFilter}>
            <SelectTrigger className="w-full sm:w-72">
              <SelectValue placeholder="All knowledge bases" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All knowledge bases</SelectItem>
              {knowledgeBases.data?.items.map((kb, index) => (
                <SelectItem key={kb.id ?? index} value={kb.id ?? ''}>
                  {kb.name ?? `Knowledge base ${index + 1}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <AsyncBoundary
        loading={documents.loading}
        error={documents.error}
        onRetry={documents.reload}
        isEmpty={!documents.data?.items.length}
        empty={
          <EmptyState
            title="No documents"
            description="Upload a document to begin building your knowledge base."
          />
        }
      >
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Knowledge base</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.data?.items.map((doc, index) => (
                  <TableRow key={doc.id ?? index}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {doc.title ?? `Document ${index + 1}`}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5" />
                        {doc.kb_id ?? '—'}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {doc.source_type ?? '—'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {doc.version ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={doc.is_published ? 'default' : 'secondary'}>
                        {doc.is_published ? 'Published' : (doc.status ?? 'Draft')}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </AsyncBoundary>

      <DocumentGuide />
    </div>
  )
}