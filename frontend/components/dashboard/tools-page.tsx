'use client'

import { useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/shared/async'
import {
  platformTools,
  toolCategories,
  type PlatformTool,
  type ToolCategory,
} from '@/lib/platform-tools'

type ToolStatus = 'unknown' | 'up' | 'down'

const statusLabels: Record<ToolStatus, string> = {
  unknown: 'Not probed',
  up: 'Online',
  down: 'Unreachable',
}

function useToolStatuses(tools: PlatformTool[]) {
  const [statuses, setStatuses] = useState<Record<string, ToolStatus>>({})

  useEffect(() => {
    if (!tools.length) return
    let cancelled = false

    async function probe() {
      const entries = await Promise.all(
        tools.map(async (tool) => {
          if (!tool.healthUrl) return [tool.id, 'unknown' as ToolStatus] as const
          try {
            const response = await fetch(tool.healthUrl, {
              mode: 'no-cors',
              cache: 'no-store',
            })
            // opaque responses report status 0 but still prove the host answered
            return [tool.id, (response.ok || response.type === 'opaque'
              ? 'up'
              : 'down') as ToolStatus] as const
          } catch {
            return [tool.id, 'down' as ToolStatus] as const
          }
        })
      )
      if (!cancelled) setStatuses(Object.fromEntries(entries))
    }

    void probe()
    return () => {
      cancelled = true
    }
  }, [tools])

  return statuses
}

function StatusBadge({ status }: { status: ToolStatus }) {
  const variant =
    status === 'up' ? 'default' : status === 'down' ? 'destructive' : 'outline'
  return <Badge variant={variant}>{statusLabels[status]}</Badge>
}

export function ToolsPage() {
  const [category, setCategory] = useState<ToolCategory | 'all'>('all')
  const statuses = useToolStatuses(platformTools)

  const visible =
    category === 'all'
      ? platformTools
      : platformTools.filter((tool) => tool.category === category)

  const online = Object.values(statuses).filter((status) => status === 'up').length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tools"
        description="Every operator interface that runs alongside the platform, with live reachability."
        actions={
          <Select value={category} onValueChange={(value) => setCategory(value as ToolCategory | 'all')}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {toolCategories.map((value) => (
                <SelectItem key={value} value={value}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Tools listed</p>
            <p className="text-2xl font-bold">{platformTools.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Online now</p>
            <p className="text-2xl font-bold">{online}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Categories</p>
            <p className="text-2xl font-bold">{toolCategories.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visible.map((tool) => {
          const Icon = tool.icon
          return (
            <Card key={tool.id} className="flex flex-col">
              <CardContent className="flex flex-1 flex-col gap-3 pt-6">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <h2 className="font-semibold">{tool.name}</h2>
                  </div>
                  <StatusBadge status={statuses[tool.id] ?? 'unknown'} />
                </div>

                <p className="text-sm text-muted-foreground">{tool.description}</p>

                <div className="flex flex-wrap gap-1">
                  <Badge variant="secondary">{tool.category}</Badge>
                  {tool.ports.map((port) => (
                    <Badge key={port} variant="outline">
                      :{port}
                    </Badge>
                  ))}
                </div>

                {tool.notes && (
                  <p className="text-xs text-muted-foreground">{tool.notes}</p>
                )}

                <a
                  href={tool.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                >
                  Open {tool.name}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}