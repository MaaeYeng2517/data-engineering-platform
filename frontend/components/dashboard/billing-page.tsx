'use client'

import { CircleDollarSign } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
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

interface Plan {
  id?: string
  code?: string
  name?: string
  description?: string
  price_cents?: number
  currency?: string
  interval?: string
  api_calls_per_month?: number
  features?: string[]
  is_active?: boolean
}

interface Entitlement {
  plan?: string
  status?: string
  api_calls_limit?: number
  features?: string[]
  current_period_end?: string
}

/**
 * Share of the billing month consumed. Falls back to 0 when the plan has no
 * recorded start, and is derived from the previous reset rather than hardcoded.
 */
function periodElapsedPercent(periodEnd?: string): number {
  if (!periodEnd) return 0
  const end = new Date(periodEnd).getTime()
  if (Number.isNaN(end)) return 0
  const now = Date.now()
  if (end <= now) return 100

  const endDate = new Date(end)
  // Period runs to the same day-of-month one month earlier.
  const start = new Date(endDate)
  start.setMonth(start.getMonth() - 1)
  const span = end - start.getTime()
  if (span <= 0) return 0
  return Math.min(100, Math.max(0, Math.round(((now - start.getTime()) / span) * 100)))
}

export function BillingPage() {
  const plans = useApi(() => getList<Plan>('/billing/plans'), [])
  const entitlements = useApi(() => getList<Entitlement>('/billing/entitlements'), [])

  const current = entitlements.data?.items[0]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing"
        description="Your plan, entitlements and available membership tiers."
        actions={
          <ReloadButton
            onClick={() => {
              plans.reload()
              entitlements.reload()
            }}
          />
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <CircleDollarSign className="h-4 w-4 text-muted-foreground" />
            Current plan
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <AsyncBoundary
            loading={entitlements.loading}
            error={entitlements.error}
            onRetry={entitlements.reload}
          >
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <p className="text-xs uppercase text-muted-foreground">Plan</p>
                <p className="text-lg font-semibold">{current?.plan ?? 'None'}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Status</p>
                <Badge variant={current?.status === 'active' ? 'default' : 'secondary'}>
                  {current?.status ?? 'inactive'}
                </Badge>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">API calls / month</p>
                <p className="text-lg font-semibold">
                  {(current?.api_calls_limit ?? 0).toLocaleString()}
                </p>
              </div>
            </div>

            {current?.current_period_end && (
              <>
                <Separator />
                <div className="space-y-1.5">
                  <p className="text-xs text-muted-foreground">
                    Current period ends{' '}
                    {new Date(current.current_period_end).toLocaleDateString()}
                  </p>
                  <Progress value={periodElapsedPercent(current.current_period_end)} />
                  <p className="text-xs text-muted-foreground">
                    {periodElapsedPercent(current.current_period_end)}% of the billing period
                    elapsed.
                  </p>
                </div>
              </>
            )}

            {current?.features && current.features.length > 0 && (
              <>
                <Separator />
                <ul className="space-y-1.5 text-sm">
                  {current.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </AsyncBoundary>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Available plans</h2>
        <AsyncBoundary
          loading={plans.loading}
          error={plans.error}
          onRetry={plans.reload}
          isEmpty={!plans.data?.items.length}
          empty={
            <EmptyState
              title="No plans available"
              description="No membership plans have been seeded for this workspace."
            />
          }
        >
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {plans.data?.items.map((plan, index) => (
              <Card key={plan.id ?? index}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-base">{plan.name ?? plan.code}</CardTitle>
                    {plan.code === current?.plan && <Badge>Current</Badge>}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <span className="text-2xl font-bold">
                      {((plan.price_cents ?? 0) / 100).toFixed(0)}
                    </span>
                    <span className="ml-1 text-xs uppercase text-muted-foreground">
                      {plan.currency ?? 'thb'} / {plan.interval ?? 'month'}
                    </span>
                  </div>
                  {plan.description && (
                    <p className="text-sm text-muted-foreground">{plan.description}</p>
                  )}
                  {plan.features && plan.features.length > 0 && (
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {plan.features.map((feature) => (
                        <li key={feature}>• {feature}</li>
                      ))}
                    </ul>
                  )}
                  <Button className="w-full" variant="outline" disabled>
                    Upgrade (Stripe not configured)
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </AsyncBoundary>
      </div>
    </div>
  )
}