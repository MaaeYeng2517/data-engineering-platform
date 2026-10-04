import type { Metadata } from 'next'

import { ConfigurationPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Configuration | DataAir',
  description: 'Configuration in the DataAir platform.',
}

export default function Page() {
  return <ConfigurationPage />
}
