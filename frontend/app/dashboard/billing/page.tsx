import type { Metadata } from 'next'

import { BillingPage } from '@/components/dashboard/billing-page'

export const metadata: Metadata = {
  title: 'Billing | DataAir',
  description: 'Billing in the DataAir platform.',
}

export default function Page() {
  return <BillingPage />
}
