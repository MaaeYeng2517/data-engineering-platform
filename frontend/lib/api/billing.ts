import { api } from '@/lib/api/client'

export interface MembershipPlan {
  code: string
  name: string
  description: string | null
  price_cents: number
  currency: string
  interval: string
  api_calls_per_month: number
  features: string[]
  requires_payment: boolean
}

export interface SubscribePayload {
  email: string
  password: string
  full_name?: string
  plan_code: string
  success_url?: string
  cancel_url?: string
}

export interface SubscribeResult {
  status: 'activated' | 'checkout_created' | string
  message: string | null
  checkout_url: string | null
  session_id: string | null
  plan_code: string | null
  amount_cents: number
  currency: string
  access_token: string | null
  user: { id: string; email: string; full_name: string | null } | null
  csrf_token: string | null
}

export interface SubscribeStatus {
  status: string
  activated: boolean
  plan_code: string | null
  email: string | null
  message: string | null
}

/** Public plan catalogue. Falls back to the configured defaults when the API is unreachable. */
export const FALLBACK_PLANS: MembershipPlan[] = [
  {
    code: 'free',
    name: 'Free',
    description: 'เริ่มต้นใช้งานแพลตฟอร์มและ API พื้นฐาน',
    price_cents: 0,
    currency: 'thb',
    interval: 'month',
    api_calls_per_month: 1000,
    features: ['basic_search', 'basic_rag', 'api_access'],
    requires_payment: false,
  },
  {
    code: 'pro',
    name: 'Pro',
    description: 'สำหรับทีมที่ต้องการขีดจำกัด API และ workflow ที่ก้าวหน้าขึ้น',
    price_cents: 29000,
    currency: 'thb',
    interval: 'month',
    api_calls_per_month: 100000,
    features: ['basic_search', 'advanced_search', 'rag', 'api_access', 'workflows', 'usage_analytics'],
    requires_payment: true,
  },
  {
    code: 'enterprise',
    name: 'Enterprise',
    description: 'แผนสำหรับองค์กร พร้อมการผสานรวมและการสนับสนุนแบบเฉพาะ',
    price_cents: 99000,
    currency: 'thb',
    interval: 'month',
    api_calls_per_month: 1000000,
    features: ['everything_in_pro', 'custom_integrations', 'sso', 'audit_logs', 'dedicated_support'],
    requires_payment: true,
  },
]

export async function fetchPlans(): Promise<MembershipPlan[]> {
  try {
    const response = await api.get<MembershipPlan[]>('/billing/public-plans')
    const plans = Array.isArray(response.data) ? response.data : []
    if (plans.length === 0) return FALLBACK_PLANS
    return plans
  } catch {
    return FALLBACK_PLANS
  }
}

/** Starts a payment-gated signup and returns where the browser must go next. */
export async function subscribe(payload: SubscribePayload): Promise<SubscribeResult> {
  const response = await api.post<SubscribeResult>('/billing/subscribe', payload)
  return response.data
}

/** Polls until the paid registration has been activated. */
export async function fetchSubscribeStatus(sessionId: string): Promise<SubscribeStatus> {
  const response = await api.get<SubscribeStatus>('/billing/subscribe/status', {
    params: { session_id: sessionId },
  })
  return response.data
}
