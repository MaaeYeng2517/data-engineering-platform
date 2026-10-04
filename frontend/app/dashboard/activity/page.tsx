import type { Metadata } from 'next'

import { ActivityPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Activity | DataAir',
  description: 'Activity in the DataAir platform.',
}

export default function Page() {
  return <ActivityPage />
}
