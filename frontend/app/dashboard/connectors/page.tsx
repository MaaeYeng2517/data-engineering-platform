import type { Metadata } from 'next'

import { ConnectorsPage } from '@/components/dashboard/connectors-page'

export const metadata: Metadata = {
  title: 'Connectors | DataAir',
  description: 'Connectors in the DataAir platform.',
}

export default function Page() {
  return <ConnectorsPage />
}
