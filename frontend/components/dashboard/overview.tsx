'use client'

import Link from 'next/link'
import {
  Activity,
  BookOpen,
  CircleDollarSign,
  Database,
  FileText,
  GitBranch,
  KeyRound,
  Search,
  ShieldCheck,
  Workflow,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getList } from '@/lib/api/data'
import { getPlatformHealth, getPlatformLinks } from '@/lib/api/platform'
import type { PlatformHealth, PlatformLinks } from '@/types/platform'
import {
  AsyncBoundary,
  PageHeader,
  ReloadButton,
} from '@/components/shared/async'
import { useApi } from '@/components/shared/async'
import { useAuth } from '@/providers/auth-provider'

interface Source {
  id?: string
  name?: string
  type?: string
  status?: string
  is_active?: boolean
}

interface Subscription {
  id?: string
  status?: string
  plan?: { code?: string; name?: string; api_calls_per_month?: number }
}

interface MetadataSchema {
  id?: string
  name?: string
}

interface UsageRecord {
  id?: string
  endpoint?: string
  method?: string
  status_code?: number
}

const quickLinks = [
  { title: 'Data Sources', href: '/dashboard/sources', icon: Database, description: 'Connect and sync data' },
  { title: 'Knowledge Bases', href: '/dashboard/knowledge', icon: BookOpen, description: 'Curate collections' },
  { title: 'Search', href: '/dashboard/search', icon: Search, description: 'Query your data' },
  { title: 'Workflows', href: '/dashboard/workflows', icon: Workflow, description: 'Orchestrate pipelines' },
  { title: 'Governance', href: '/dashboard/governance', icon: ShieldCheck, description: 'Policies and approvals' },
  { title: 'API Keys', href: '/dashboard/api-keys', icon: KeyRound, description: 'Programmatic access' },
  { title: 'Lineage', href: '/dashboard/lineage', icon: GitBranch, description: 'Trace data flow' },
  { title: 'Billing', href: '/dashboard/billing', icon: CircleDollarSign, description: 'Plan and usage' },
]

function StatCard({
  title,
  value,
  hint,
  icon: Icon,
}: {
  title: string
  value: string | number
  hint?: string
  icon: typeof Database
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  )
}

export function DashboardOverview() {
  const { user } = useAuth()
  const sources = useApi(() => getList<Source>('/connectors/sources'), [])
  const subscription = useApi(() => getList<Subscription>('/billing/subscription'), [])
  const schemas = useApi(() => getList<MetadataSchema>('/metadata/'), [])
  const usage = useApi(() => getList<UsageRecord>('/api-keys/usage'), [])
  const platform = useApi(() => getPlatformHealth(), [])
  const links = useApi(() => getPlatformLinks(), [])

  const activeSources = sources.data?.items.filter((s) => s.is_active !== false).length ?? 0
  const sub = subscription.data?.items[0]
  const limit = sub?.plan?.api_calls_per_month ?? 0

  // Real call count from the usage log, not a fabricated numerator.
  const usedCalls = usage.data?.total ?? 0
  const usagePercent = limit > 0 ? Math.min(100, Math.round((usedCalls / limit) * 100)) : 0

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back${user?.full_name ? `, ${user.full_name}` : ''}`}
        description="Overview of your workspace, data sources and plan."
        actions={
        <ReloadButton
          onClick={() => {
            sources.reload()
            subscription.reload()
            schemas.reload()
            usage.reload()
            platform.reload()
            links.reload()
          }}
        />
        }
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Data Sources"
          value={sources.loading ? '—' : activeSources}
          hint={activeSources === 0 ? 'No sources configured yet' : 'Connected sources'}
          icon={Database}
        />
        <StatCard
          title="Datasets"
          value={schemas.loading ? '—' : (schemas.data?.total ?? 0)}
          hint="Registered metadata schemas"
          icon={FileText}
        />
        <StatCard
          title="Current Plan"
          value={subscription.loading ? '—' : (sub?.plan?.name ?? 'None')}
          hint={sub?.status ?? 'No active subscription'}
          icon={CircleDollarSign}
        />
        <StatCard
          title="API Calls"
          value={usage.loading ? '—' : usedCalls.toLocaleString()}
          hint={limit > 0 ? `of ${limit.toLocaleString()} this month` : 'Select a plan'}
          icon={Activity}
        />
      </div>

      {limit > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Monthly API usage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Progress value={usagePercent} />
            <p className="text-xs text-muted-foreground">
              {usedCalls.toLocaleString()} of {limit.toLocaleString()} calls used (
              {usagePercent}%).
            </p>
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="mb-3 text-lg font-semibold">Platform systems</h2>
        <Card>
          <CardContent className="pt-6">
            {platform.loading ? (
              <p className="py-4 text-center text-sm text-muted-foreground">Loading…</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(platform.data?.systems ?? {}).map(([name, info]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between gap-3 rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          info.status === 'healthy'
                            ? 'bg-green-500'
                            : info.status === 'degraded'
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                        }`}
                      />
                      <span className="text-sm font-medium capitalize">{name}</span>
                    </div>
                    <Badge
                      variant={
                        info.status === 'healthy'
                          ? 'default'
                          : info.status === 'degraded'
                            ? 'secondary'
                            : 'destructive'
                      }
                    >
                      {String(info.status)}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
            {platform.data && (
              <p className="mt-3 text-xs text-muted-foreground">
                {platform.data.summary.healthy} of {platform.data.summary.total} systems
                reachable ·{' '}
                {links.data?.airflow ? (
                  <a href={links.data.airflow} target="_blank" rel="noreferrer" className="underline">
                    Airflow
                  </a>
                ) : (
                  'Airflow'
                )}
                {' · '}
                {links.data?.openmetadata ? (
                  <a href={links.data.openmetadata} target="_blank" rel="noreferrer" className="underline">
                    OpenMetadata
                  </a>
                ) : (
                  'OpenMetadata'
                )}
                {' · '}
                {links.data?.grafana ? (
                  <a href={links.data.grafana} target="_blank" rel="noreferrer" className="underline">
                    Grafana
                  </a>
                ) : (
                  'Grafana'
                )}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Quick access</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickLinks.map((link) => (
            <Link key={link.href} href={link.href}>
              <Card className="h-full transition-colors hover:border-primary/50 hover:bg-accent/40">
                <CardContent className="flex items-start gap-3 p-4">
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <link.icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{link.title}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {link.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Recent sources</CardTitle>
        </CardHeader>
        <CardContent>
          <AsyncBoundary
            loading={sources.loading}
            error={sources.error}
            onRetry={sources.reload}
            isEmpty={!sources.data?.items.length}
            empty={
              <div className="flex flex-col items-center gap-3 py-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No data sources connected yet.
                </p>
                <Button size="sm" asChild>
                  <Link href="/dashboard/sources">Connect your first source</Link>
                </Button>
              </div>
            }
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.data?.items.map((source, index) => (
                  <TableRow key={source.id ?? index}>
                    <TableCell className="font-medium">
                      {source.name ?? `Source ${index + 1}`}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {source.type ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={source.is_active === false ? 'secondary' : 'default'}>
                        {source.status ?? (source.is_active === false ? 'Inactive' : 'Active')}
                      </Badge>
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