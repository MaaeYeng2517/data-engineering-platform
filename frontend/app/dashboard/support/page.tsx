import type { Metadata } from 'next'

import { SupportPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Support | DataAir',
  description: 'Support in the DataAir platform.',
}

export default function Page() {
  return <SupportPage />
}
