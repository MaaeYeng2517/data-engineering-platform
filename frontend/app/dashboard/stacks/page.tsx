import type { Metadata } from 'next'

import { StacksPage } from '@/components/dashboard/stacks-page'

export const metadata: Metadata = {
  title: 'Stacks | DataAir',
  description: 'Languages, runtimes and libraries used by the DataAir platform.',
}

export default function Page() {
  return <StacksPage />
}