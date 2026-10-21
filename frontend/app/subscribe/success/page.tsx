import type { Metadata } from 'next'
import { Suspense } from 'react'

import { SubscribeStatusView } from '@/components/billing/subscribe-status-view'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'

export const metadata: Metadata = {
  title: 'Payment confirmed | DataAir',
  description: 'กำลังยืนยันการชำระเงินและเปิดใช้งาน workspace ของคุณ',
}

export default function SubscribeSuccessPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex flex-1 items-center justify-center p-4">
        <Suspense fallback={null}>
          <SubscribeStatusView />
        </Suspense>
      </main>
      <SiteFooter />
    </div>
  )
}
