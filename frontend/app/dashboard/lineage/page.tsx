import type { Metadata } from 'next'

import { LineagePage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Lineage | DataAir',
  description: 'Lineage in the DataAir platform.',
}

export default function Page() {
  return <LineagePage />
}
