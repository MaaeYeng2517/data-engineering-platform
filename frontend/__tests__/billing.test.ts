import {
  FALLBACK_PLANS,
  fetchPlans,
  fetchSubscribeStatus,
  subscribe,
} from '@/lib/api/billing'

const api = {
  get: jest.fn(),
  post: jest.fn(),
}

jest.mock('@/lib/api/client', () => ({
  api: {
    get: (...args: unknown[]) => api.get(...args),
    post: (...args: unknown[]) => api.post(...args),
  },
}))

beforeEach(() => {
  api.get.mockReset()
  api.post.mockReset()
})

describe('billing api', () => {
  it('falls back to the built-in catalogue when the API is unreachable', async () => {
    api.get.mockRejectedValue(new Error('offline'))

    const plans = await fetchPlans()

    expect(plans).toEqual(FALLBACK_PLANS)
    expect(plans.map((p) => p.code)).toEqual(['free', 'pro', 'enterprise'])
  })

  it('reads the public plan endpoint', async () => {
    api.get.mockResolvedValue({ data: FALLBACK_PLANS })

    await fetchPlans()

    expect(api.get).toHaveBeenCalledWith('/billing/public-plans')
  })

  it('marks every paid plan as requiring payment', () => {
    const free = FALLBACK_PLANS.find((p) => p.code === 'free')
    const pro = FALLBACK_PLANS.find((p) => p.code === 'pro')

    expect(free?.requires_payment).toBe(false)
    expect(pro?.requires_payment).toBe(true)
  })

  it('posts the signup to the subscribe endpoint', async () => {
    api.post.mockResolvedValue({
      data: { status: 'checkout_created', checkout_url: 'https://pay.test/abc' },
    })

    const result = await subscribe({
      email: 'payer@example.com',
      password: 'longenough',
      plan_code: 'pro',
    })

    expect(api.post).toHaveBeenCalledWith('/billing/subscribe', {
      email: 'payer@example.com',
      password: 'longenough',
      plan_code: 'pro',
    })
    expect(result.checkout_url).toBe('https://pay.test/abc')
  })

  it('passes the checkout session id when polling for activation', async () => {
    api.get.mockResolvedValue({
      data: { status: 'completed', activated: true, plan_code: 'pro', email: 'payer@example.com' },
    })

    const status = await fetchSubscribeStatus('cs_test_123')

    expect(api.get).toHaveBeenCalledWith('/billing/subscribe/status', {
      params: { session_id: 'cs_test_123' },
    })
    expect(status.activated).toBe(true)
  })

  it('reports a registration that is still waiting for the payment', async () => {
    api.get.mockResolvedValue({
      data: { status: 'checkout_created', activated: false, plan_code: 'pro' },
    })

    const status = await fetchSubscribeStatus('cs_test_456')

    expect(status.activated).toBe(false)
    expect(status.status).toBe('checkout_created')
  })
})
