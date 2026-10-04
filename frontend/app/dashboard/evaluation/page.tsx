import type { Metadata } from 'next'

import { EvaluationPage } from '@/components/dashboard/evaluation-page'

export const metadata: Metadata = {
  title: 'Evaluation | DataAir',
  description: 'Evaluation in the DataAir platform.',
}

export default function Page() {
  return <EvaluationPage />
}
