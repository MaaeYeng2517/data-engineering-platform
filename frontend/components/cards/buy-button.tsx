'use client'

import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/providers/auth-provider'

/**
 * Sends the buyer to the checkout page, or to the login page first when there
 * is no session — the purchase needs an account, so the target is carried
 * through the login as a `next` parameter.
 */
export function BuyButton({ cardId }: { cardId: string }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  function buy() {
    const target = `/payment?card=${encodeURIComponent(cardId)}`
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent(target)}`)
      return
    }
    router.push(target)
  }

  return (
    <Button size="sm" onClick={buy} disabled={isLoading} className="mt-3 w-full">
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      Buy Now
    </Button>
  )
}
