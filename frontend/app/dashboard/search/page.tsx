import type { Metadata } from 'next'

import { SearchPage } from '@/components/dashboard/search-page'

export const metadata: Metadata = {
  title: 'Search | DataAir',
  description: 'Search in the DataAir platform.',
}

export default function Page() {
  return <SearchPage />
}
