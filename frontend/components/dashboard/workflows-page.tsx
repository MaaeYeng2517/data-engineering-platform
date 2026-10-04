'use client'

import { GitBranch } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getList } from '@/lib/api/data'
import {
  AsyncBoundary,
  EmptyState,
  PageHeader,
  ReloadButton,
  useApi,
} from '@/components/shared/async'

interface WorkflowRecord {
  id?: string
  kb_id?: string
  name?: string
  description?: string
  version?: string
  is_active?: boolean
  nodes?: unknown[]
  edges?: unknown[]
}

export function WorkflowsPage() {
  const workflows = useApi(() => getList<WorkflowRecord>('/workflows/'), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflows"
        description="Repeatable data pipelines you can execute on demand."
        actions={<ReloadButton onClick={workflows.reload} />}
      />

      <AsyncBoundary
        loading={workflows.loading}
        error={workflows.error}
        onRetry={workflows.reload}
        isEmpty={!workflows.data?.items.length}
        empty={
          <EmptyState
            title="No workflows"
            description="Define a workflow to chain transformations and automate recurring data work."
          />
        }
      >
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows.data?.items.map((workflow, index) => (
            <Card key={workflow.id ?? index}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <GitBranch className="h-4 w-4 text-muted-foreground" />
                    {workflow.name ?? `Workflow ${index + 1}`}
                  </CardTitle>
                  <Badge variant={workflow.is_active === false ? 'secondary' : 'default'}>
                    {workflow.is_active === false ? 'Inactive' : 'Active'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="text-muted-foreground">
                  {workflow.description ?? 'No description provided.'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {workflow.nodes?.length ?? 0} nodes &middot; {workflow.edges?.length ?? 0} edges
                  {workflow.version ? ` · v${workflow.version}` : ''}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </AsyncBoundary>
    </div>
  )
}