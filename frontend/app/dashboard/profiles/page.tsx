import type { Metadata } from 'next'

import { ProfilesPage } from '@/components/dashboard/profiles-page'

export const metadata: Metadata = {
  title: 'Service Profiles | DataAir',
  description: 'System configuration and services per environment in DataAir.',
}

export default function Page() {
  return <ProfilesPage />
}
