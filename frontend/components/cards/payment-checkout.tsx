'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatPrice } from '@/lib/cards'

interface PaymentCheckoutProps {
  cardId: string
  cardName: string
  amountCents: number
}

/**
 * Starts the payment.
 *
 * The request goes to `/api/checkout`, which prices the cart on the server
 * and hands back a Stripe Checkout URL. The browser never decides the price.
 */
export function PaymentCheckout({ cardId, cardName, amountCents }: PaymentCheckoutProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  async function pay() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: [{ cardId }] }),
      })
      const data = await response.json().catch(() => null)

      if (!response.ok) {
        if (response.status === 401) {
          router.push(`/login?next=${encodeURIComponent(`/payment?card=${cardId}`)}`)
          return
        }
        setError(data?.message || 'The payment could not be started')
        return
      }

      if (!data?.url) {
        setError('The payment could not be started')
        return
      }
      window.location.href = data.url
    } catch {
      setError('The payment could not be started')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Button onClick={pay} disabled={loading} className="w-full" size="lg">
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        ชำระเงิน {formatPrice(amountCents)}
      </Button>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <p className="text-xs text-muted-foreground">
        กดชำระเงินเพื่อไปที่หน้าชำระเงินของ Stripe — รายการซื้อ {cardName} จะถูกยืนยันหลังชำระเงินสำเร็จ
      </p>
    </div>
  )
}
