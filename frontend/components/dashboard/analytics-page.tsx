'use client'

import { BarChart3, CheckCircle2, Database, RefreshCw, XCircle } from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { PageHeader, ReloadButton, useApi } from '@/components/shared/async'
import {
  getCategoryBreakdown,
  getEltRuns,
  getQualityResults,
  getSalesDaily,
  getSalesSummary,
  getTopProducts,
} from '@/lib/api/platform'
import type {
  CategoryBreakdown,
  EltRun,
  QualityResult,
  SalesDay,
  SalesSummary,
  TopProduct,
} from '@/types/platform'

function StatCard({
  title,
  value,
  hint,
  icon: Icon,
}: {
  title: string
  value: string
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

export function AnalyticsPage() {
  const sales = useApi(() => getSalesDaily(120), [])
  const summary = useApi(() => getSalesSummary(), [])
  const products = useApi(() => getTopProducts(8), [])
  const categories = useApi(() => getCategoryBreakdown(), [])
  const quality = useApi(() => getQualityResults(10), [])
  const eltRuns = useApi(() => getEltRuns(10), [])

  const reloadAll = () => {
    sales.reload()
    summary.reload()
    products.reload()
    categories.reload()
    quality.reload()
    eltRuns.reload()
  }

  const days: SalesDay[] = [...(sales.data ?? [])].reverse()
  const chartData = days.map((d) => ({
    date: d.sales_date.slice(5),
    revenue: Number(d.total_amount),
    orders: d.order_count,
  }))
  const sum: SalesSummary = summary.data ?? {}
  const revenue = Number(sum.total_revenue ?? 0)
  const topProducts: TopProduct[] = products.data ?? []
  const maxRevenue = topProducts[0]?.revenue ?? 1
  const categoryData: CategoryBreakdown[] = categories.data ?? []
  const maxCategory = categoryData[0]?.revenue ?? 1
  const qualityResults: QualityResult[] = quality.data ?? []
  const runs: EltRun[] = eltRuns.data ?? []
  const failedExpectations = qualityResults.filter((r) => !r.success).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        description="Warehouse metrics from the dbt-built marts layer, plus pipeline runs and data quality gates."
        actions={<ReloadButton onClick={reloadAll} />}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total revenue"
          value={sales.loading ? '—' : `$${revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          hint={sum.first_day && sum.last_day ? `${sum.first_day} → ${sum.last_day}` : 'completed orders'}
          icon={BarChart3}
        />
        <StatCard
          title="Orders"
          value={sales.loading ? '—' : (sum.total_orders ?? 0).toLocaleString()}
          hint={`${sum.days ?? 0} days aggregated`}
          icon={Database}
        />
        <StatCard
          title="Units sold"
          value={sales.loading ? '—' : (sum.total_units ?? 0).toLocaleString()}
          hint={`avg $${Number(sum.avg_daily_revenue ?? 0).toFixed(0)} / day`}
          icon={BarChart3}
        />
        <StatCard
          title="Quality gates"
          value={quality.loading ? '—' : `${qualityResults.length - failedExpectations}/${qualityResults.length} passed`}
          hint={failedExpectations ? `${failedExpectations} failing runs` : 'all suites green'}
          icon={CheckCircle2}
        />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            Daily revenue (marts.sales_daily)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sales.loading ? (
            <p className="py-16 text-center text-sm text-muted-foreground">Loading…</p>
          ) : chartData.length === 0 ? (
            <p className="py-16 text-center text-sm text-muted-foreground">
              No sales data yet — run the ingest and warehouse_build pipelines.
            </p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted-foreground/20" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}`}
                    width={48}
                  />
                  <Tooltip
                    formatter={(value: number | string) => [
                      `$${Number(value).toLocaleString()}`,
                      'Revenue',
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.15}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Top products by revenue</CardTitle>
          </CardHeader>
          <CardContent>
            {topProducts.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No product data.</p>
            ) : (
              <div className="space-y-3">
                {topProducts.map((product) => (
                  <div key={product.product_id} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <span className="truncate">
                        {product.product_name}{' '}
                        <span className="text-muted-foreground">· {product.category}</span>
                      </span>
                      <Badge variant="secondary">
                        ${Number(product.revenue).toLocaleString()}
                      </Badge>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${(Number(product.revenue) / maxRevenue) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Revenue by category</CardTitle>
          </CardHeader>
          <CardContent>
            {categoryData.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No category data.</p>
            ) : (
              <div className="space-y-3">
                {categoryData.map((category) => (
                  <div key={category.category} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <span>{category.category}</span>
                      <Badge variant="secondary">
                        ${Number(category.revenue).toLocaleString()}
                      </Badge>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${(Number(category.revenue) / maxCategory) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
              Recent data quality runs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {qualityResults.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No quality runs recorded yet.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Suite</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead className="hidden md:table-cell">When</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {qualityResults.map((result) => (
                    <TableRow key={result.run_id}>
                      <TableCell className="font-medium">{result.suite_name}</TableCell>
                      <TableCell>
                        <Badge variant={result.success ? 'default' : 'destructive'}>
                          {result.success ? (
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                          ) : (
                            <XCircle className="mr-1 h-3 w-3" />
                          )}
                          {result.success ? 'Passed' : 'Failed'}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">
                        {result.created_at ? new Date(result.created_at).toLocaleString() : '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Recent pipeline runs</CardTitle>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No ELT runs recorded yet.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Layer</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">Rows</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={`${run.run_id}-${run.model_name}`}>
                      <TableCell className="font-medium">{run.model_name}</TableCell>
                      <TableCell className="text-muted-foreground">{run.layer}</TableCell>
                      <TableCell>
                        <Badge variant={run.status === 'success' ? 'default' : 'destructive'}>
                          {run.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">
                        {run.rows_affected != null ? run.rows_affected.toLocaleString() : '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
