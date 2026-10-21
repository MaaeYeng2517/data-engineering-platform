import type { Metadata } from 'next'

import { SubscribeForm } from '@/components/billing/subscribe-form'
import { SiteFooter, SiteHeader } from '@/components/marketing/site-chrome'

export const metadata: Metadata = {
  title: 'Choose your plan | DataAir',
  description:
    'เลือกแผนและชำระเงินเพื่อเริ่มใช้งาน DataAir — workspace จะถูกสร้างหลังยืนยันการชำระเงิน',
}

export default function SubscribePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <div className="mx-auto w-full max-w-6xl px-4 py-10">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold tracking-tight">สมัครใช้บริการ</h1>
            <p className="mt-2 text-muted-foreground">
              เลือกแผน — ชำระเงินก่อนเริ่มใช้งาน แล้วระบบจะเปิด workspace ให้คุณอัตโนมัติ
            </p>
          </div>
          <SubscribeForm />
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
