import type { Metadata } from 'next'

import { ApiKeysPage } from '@/components/dashboard/api-keys-page'

export const metadata: Metadata = {
  title: 'API Keys | DataAir',
  description: 'API Keys in the DataAir platform.',
}

export default function Page() {
  return <ApiKeysPage />
}
