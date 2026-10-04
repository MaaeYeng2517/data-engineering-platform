import type { Metadata } from 'next'

import { ApprovalsPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Approvals | DataAir',
  description: 'Approvals in the DataAir platform.',
}

export default function Page() {
  return <ApprovalsPage />
}
