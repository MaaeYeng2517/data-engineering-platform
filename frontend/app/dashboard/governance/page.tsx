import type { Metadata } from 'next'

import { GovernancePage } from '@/components/dashboard/governance-page'

export const metadata: Metadata = {
  title: 'Governance | DataAir',
  description: 'Governance in the DataAir platform.',
}

export default function Page() {
  return <GovernancePage />
}
