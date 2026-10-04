'use client'

import { Fragment, useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  RadioTower,
  RefreshCw,
  XCircle,
} from 'lucide-react'

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
import { cn } from '@/lib/utils'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const REFRESH_MS = 15000

type ServiceStatus = 'healthy' | 'degraded' | 'down'

interface ServiceRow {
  id: string
  name: string
  tools: string
  port: string
  category: string
  category_label: string
  public_url: string | null
  status: ServiceStatus
  detail?: string
  latency_ms?: number | null
  targets?: { job: string; health: string; error: string }[]
}

interface SystemReport {
  generated_at: string
  summary: {
    total: number
    healthy: number
    degraded: number
    down: number
    availability_pct: number
    avg_latency_ms: number | null
  }
  services: ServiceRow[]
  telemetry?: {
    enabled: boolean
    endpoint: string | null
    service: string | null
  }
}

const statusMeta: Record<ServiceStatus, { label: string; icon: typeof Activity; className: string }> = {
  healthy: { label: 'สำเร็จ', icon: CheckCircle2, className: 'text-emerald-600' },
  degraded: { label: 'เตือน', icon: AlertTriangle, className: 'text-amber-600' },
  down: { label: 'ไม่สำเร็จ', icon: XCircle, className: 'text-destructive' },
}

function StatusCell({ status }: { status: ServiceStatus }) {
  const meta = statusMeta[status] ?? statusMeta.down
  const Icon = meta.icon
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-sm font-medium', meta.className)}>
      <Icon className="h-4 w-4" />
      {meta.label}
    </span>
  )
}

function MetricCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string
  value: string
  hint?: string
  icon: typeof Activity
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Icon className="h-4 w-4" />
          {label}
        </div>
        <p className="mt-1 text-2xl font-bold">{value}</p>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  )
}

export function SystemStatusPage() {
  const [report, setReport] = useState<SystemReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const load = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true)
    try {
      const response = await fetch(`${API_BASE_URL}/system/status`, { cache: 'no-store' })
      if (!response.ok) throw new Error(`backend responded ${response.status}`)
      setReport((await response.json()) as SystemReport)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'ไม่สามารถเชื่อมต่อ backend ได้')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!autoRefresh) return
    const timer = setInterval(() => void load(true), REFRESH_MS)
    return () => clearInterval(timer)
  }, [autoRefresh, load])

  const grouped = useMemo(() => {
    if (!report) return []
    const buckets = new Map<string, ServiceRow[]>()
    for (const service of report.services) {
      const list = buckets.get(service.category_label) ?? []
      list.push(service)
      buckets.set(service.category_label, list)
    }
    return Array.from(buckets.entries())
  }, [report])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        กำลังตรวจสอบระบบ…
      </div>
    )
  }

  const summary = report?.summary
  const failed = (summary?.degraded ?? 0) + (summary?.down ?? 0)

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="mx-auto w-full max-w-7xl px-6 py-10">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">System Status</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              ติดตามการทำงานของทุก service ใน DataAir platform
              {report?.generated_at ? ` · ตรวจล่าสุด ${report.generated_at}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={autoRefresh ? 'secondary' : 'outline'}
              onClick={() => setAutoRefresh((value) => !value)}
            >
              {autoRefresh ? 'Auto-refresh 15s' : 'Auto-refresh ปิด'}
            </Button>
            <Button onClick={() => void load()} disabled={refreshing}>
              <RefreshCw className={cn('mr-2 h-4 w-4', refreshing && 'animate-spin')} />
              ตรวจสอบใหม่
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm">
            <p className="font-medium">อ่านข้อมูลไม่สำเร็จ: {error}</p>
            <p className="mt-1 text-muted-foreground">
              ตรวจสอบว่า backend ทำงานอยู่ที่ {API_BASE_URL}
            </p>
          </div>
        )}

        {summary && (
          <>
            {report?.telemetry && (
              <Card className="mb-6">
                <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
                  <div className="flex items-center gap-3">
                    <RadioTower
                      className={cn(
                        'h-5 w-5',
                        report.telemetry.enabled ? 'text-emerald-600' : 'text-muted-foreground'
                      )}
                    />
                    <div>
                      <p className="text-sm font-medium">
                        Traces ไปยัง Grafana Cloud
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {report.telemetry.enabled
                          ? `${report.telemetry.service} → ${report.telemetry.endpoint}`
                          : 'ปิดอยู่ — ยังไม่ได้ตั้งค่า OTEL_EXPORTER_OTLP_ENDPOINT'}
                      </p>
                    </div>
                  </div>
                  <Badge variant={report.telemetry.enabled ? 'default' : 'outline'}>
                    {report.telemetry.enabled ? 'ส่งอยู่' : 'ไม่ส่ง'}
                  </Badge>
                </CardContent>
              </Card>
            )}

            <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Services ทั้งหมด"
                value={String(summary.total)}
                hint="ตรวจจากภายใน backend container"
                icon={Activity}
              />
              <MetricCard
                label="ทำงานปกติ"
                value={String(summary.healthy)}
                hint={`degraded ${summary.degraded} · down ${summary.down}`}
                icon={CheckCircle2}
              />
              <MetricCard
                label="ต้องแก้ไข"
                value={String(failed)}
                hint={failed === 0 ? 'ไม่พบปัญหา' : 'ดูรายละเอียดด้านล่าง'}
                icon={failed === 0 ? CheckCircle2 : AlertTriangle}
              />
              <MetricCard
                label="Availability"
                value={`${summary.availability_pct}%`}
                hint={
                  summary.avg_latency_ms
                    ? `เฉลี่ย ${summary.avg_latency_ms} ms`
                    : 'ไม่มี latency'
                }
                icon={Activity}
              />
            </div>

            <div className="space-y-6">
              {grouped.map(([label, services]) => (
                <Card key={label}>
                  <div className="border-b px-6 py-4">
                    <h2 className="font-semibold">{label}</h2>
                    <p className="text-xs text-muted-foreground">
                      {services.length} service(s)
                    </p>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Service</TableHead>
                        <TableHead>Tools</TableHead>
                        <TableHead>Port</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>รายละเอียด</TableHead>
                        <TableHead>Latency</TableHead>
                        <TableHead>เปิด</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {services.map((service) => (
                        <Fragment key={service.id}>
                          <TableRow>
                            <TableCell className="font-mono text-xs">{service.name}</TableCell>
                            <TableCell className="text-muted-foreground">{service.tools}</TableCell>
                            <TableCell className="font-mono text-xs">{service.port}</TableCell>
                            <TableCell>
                              <StatusCell status={service.status} />
                            </TableCell>
                            <TableCell className="max-w-md text-sm text-muted-foreground">
                              {service.detail ?? '—'}
                            </TableCell>
                            <TableCell className="font-mono text-xs">
                              {service.latency_ms != null ? `${service.latency_ms} ms` : '—'}
                            </TableCell>
                            <TableCell>
                              {service.public_url ? (
                                <a
                                  href={service.public_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                                >
                                  เปิด
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              ) : (
                                <span className="text-xs text-muted-foreground">internal</span>
                              )}
                            </TableCell>
                          </TableRow>
                          {service.targets?.map((target) => (
                            <TableRow key={`${service.id}-${target.job}`} className="bg-muted/40">
                              <TableCell className="pl-10 font-mono text-xs text-muted-foreground">
                                ↳ {target.job}
                              </TableCell>
                              <TableCell colSpan={4} className="text-xs text-muted-foreground">
                                {target.health === 'up'
                                  ? 'scrape สำเร็จ'
                                  : target.error || 'scrape ไม่สำเร็จ'}
                              </TableCell>
                              <TableCell colSpan={2} />
                            </TableRow>
                          ))}
                        </Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              ))}
            </div>

            <p className="mt-8 text-center text-xs text-muted-foreground">
              ไม่ต้องเข้าสู่ระบบ · อัปเดตอัตโนมัติทุก 15 วินาที
            </p>
          </>
        )}
      </div>
    </div>
  )
}