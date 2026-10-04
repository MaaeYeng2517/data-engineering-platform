import type { Metadata } from 'next'

import { AuditPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Audit | DataAir',
  description: 'Audit in the DataAir platform.',
}

export default function Page() {
  return <AuditPage />
}
