import type { Metadata } from 'next'

import { ProfileDetailPage } from '@/components/dashboard/profile-detail-page'

export const metadata: Metadata = {
  title: 'Profile | DataAir',
  description: 'Services, tokens and configuration for one DataAir environment.',
}

export default function Page() {
  return <ProfileDetailPage />
}
