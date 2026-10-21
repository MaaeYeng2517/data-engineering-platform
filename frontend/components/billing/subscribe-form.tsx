'use client'

import { useEffect, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { extractErrorDetail } from '@/lib/api/data'
import {
  FALLBACK_PLANS,
  MembershipPlan,
  fetchPlans,
  subscribe,
} from '@/lib/api/billing'
import { toast } from 'sonner'

function formatPrice(plan: MembershipPlan): string {
  if (plan.price_cents === 0) return 'ฟรี'
  const amount = plan.price_cents / 100
  const symbol = plan.currency.toUpperCase() === 'THB' ? '฿' : `${plan.currency.toUpperCase()} `
  return `${symbol}${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

function featureLabel(feature: string): string {
  const labels: Record<string, string> = {
    basic_search: 'ค้นหาข้อมูลพื้นฐาน',
    advanced_search: 'ค้นหาขั้นสูง (hybrid + rerank)',
    basic_rag: 'RAG พื้นฐาน',
    rag: 'RAG พร้อม citations',
    api_access: 'เข้าถึงผ่าน API',
    workflows: 'workflow อัตโนมัติ',
    usage_analytics: 'สถิติการใช้งาน',
    everything_in_pro: 'ทุกอย่างในแผน Pro',
    custom_integrations: 'integration เฉพาะองค์กร',
    sso: 'SSO / SAML',
    audit_logs: 'audit log',
    dedicated_support: 'ฝ่ายสนับสนุนเฉพาะทาง',
  }
  return labels[feature] ?? feature
}

export function SubscribeForm() {
  const [plans, setPlans] = useState<MembershipPlan[]>(FALLBACK_PLANS)
  const [selected, setSelected] = useState<string>('pro')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [plansLoading, setPlansLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchPlans()
      .then((loaded) => {
        if (cancelled) return
        setPlans(loaded)
        const paid = loaded.find((p) => p.price_cents > 0)
        if (paid) setSelected(paid.code)
      })
      .finally(() => {
        if (!cancelled) setPlansLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const activePlan = plans.find((p) => p.code === selected) ?? plans[0]
  const requiresPayment = (activePlan?.price_cents ?? 0) > 0

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!activePlan) return
    setLoading(true)
    try {
      const result = await subscribe({
        email: email.trim(),
        password,
        ...(fullName.trim() ? { full_name: fullName.trim() } : {}),
        plan_code: activePlan.code,
        success_url: `${window.location.origin}/subscribe/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/subscribe?cancelled=1`,
      })

      if (result.status === 'activated') {
        toast.success('สร้าง workspace สำเร็จ — เริ่มใช้งานได้เลย')
        window.location.href = '/dashboard'
        return
      }

      if (result.checkout_url) {
        window.location.href = result.checkout_url
        return
      }

      toast.error(result.message || 'เริ่มการชำระเงินไม่สำเร็จ')
    } catch (error) {
      toast.error(extractErrorDetail(error))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold">เลือกแผนที่ต้องการ</h2>
          <p className="text-sm text-muted-foreground">
            ชำระเงินก่อนเริ่มใช้งาน — workspace จะถูกสร้างหลังยืนยันการชำระเงินสำเร็จ
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {plans.map((plan) => {
            const isActive = plan.code === selected
            return (
              <button
                key={plan.code}
                type="button"
                onClick={() => setSelected(plan.code)}
                aria-pressed={isActive}
                className={`rounded-xl border p-4 text-left transition-colors ${
                  isActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{plan.name}</span>
                  {isActive && <Check className="h-4 w-4 text-primary" />}
                </div>
                <div className="mt-2 text-2xl font-semibold">
                  {formatPrice(plan)}
                  {plan.price_cents > 0 && (
                    <span className="text-sm font-normal text-muted-foreground">
                      {' '}
                      / {plan.interval === 'year' ? 'ปี' : 'เดือน'}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {plan.api_calls_per_month.toLocaleString()} calls/เดือน
                </p>
              </button>
            )
          })}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border p-5">
          <div className="space-y-2">
            <Label htmlFor="plan">แผนที่เลือก</Label>
            <Input id="plan" value={activePlan?.name ?? ''} disabled readOnly />
          </div>
          <div className="space-y-2">
            <Label htmlFor="sub-name">ชื่อเต็ม</Label>
            <Input
              id="sub-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ada Lovelace"
              autoComplete="name"
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="sub-email">อีเมล</Label>
            <Input
              id="sub-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="sub-password">รหัสผ่าน</Label>
            <Input
              id="sub-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground">อย่างน้อย 8 ตัวอักษร</p>
          </div>

          <Button type="submit" className="w-full" disabled={loading || plansLoading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {requiresPayment
              ? `ชำระเงิน ${formatPrice(activePlan)} และเริ่มใช้งาน`
              : 'สมัครใช้งานฟรี'}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            {requiresPayment
              ? 'จะถูกพาไปหน้าชำระเงินของ Stripe — workspace จะถูกเปิดใช้งานหลังชำระเงินสำเร็จ'
              : 'บัญชีจะถูกเปิดใช้งานทันที ไม่ต้องใช้บัตรเครดิต'}
          </p>
        </form>
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle className="text-lg">{activePlan?.name ?? 'แผน'}</CardTitle>
          <CardDescription>{activePlan?.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-3xl font-semibold">
            {formatPrice(activePlan)}
            {activePlan && activePlan.price_cents > 0 && (
              <span className="text-sm font-normal text-muted-foreground">
                {' '}
                / {activePlan.interval === 'year' ? 'ปี' : 'เดือน'}
              </span>
            )}
          </div>
          <ul className="space-y-2 text-sm">
            {(activePlan?.features ?? []).map((feature) => (
              <li key={feature} className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span>{featureLabel(feature)}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
