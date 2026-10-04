import type { Metadata } from 'next'

import { SettingsPage } from '@/components/dashboard/workspace-pages'

export const metadata: Metadata = {
  title: 'Settings | DataAir',
  description: 'Settings in the DataAir platform.',
}

export default function Page() {
  return <SettingsPage />
}
