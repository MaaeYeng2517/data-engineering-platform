import type { Metadata } from 'next'

import { WorkGroupsPage } from '@/components/dashboard/work-groups-page'

export const metadata: Metadata = {
  title: 'Work Groups | DataAir',
  description: 'Organise workspace members into collaborating teams.',
}

export default function Page() {
  return <WorkGroupsPage />
}
