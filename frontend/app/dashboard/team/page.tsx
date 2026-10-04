import type { Metadata } from 'next'

import { TeamPage } from '@/components/dashboard/misc-pages'

export const metadata: Metadata = {
  title: 'Team | DataAir',
  description: 'Team in the DataAir platform.',
}

export default function Page() {
  return <TeamPage />
}
