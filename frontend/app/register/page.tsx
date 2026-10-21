import type { Metadata } from 'next'
import Link from 'next/link'
import { Database } from 'lucide-react'

import { RegisterForm } from '@/components/auth/register-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Create account | DataAir',
  description: 'Create your DataAir workspace and start building.',
}

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Database className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl">สร้างบัญชีฟรี</CardTitle>
          <CardDescription>เริ่มต้นด้วยแผนฟรี ไม่ต้องใช้บัตรเครดิต</CardDescription>
        </CardHeader>
        <CardContent>
          <RegisterForm />
          <div className="mt-4 rounded-lg border bg-muted/40 p-3 text-center text-sm">
            <span className="text-muted-foreground">ต้องการแผนแบบเสียเงิน?</span>{' '}
            <Link
              href="/subscribe"
              className="font-medium text-foreground underline underline-offset-4"
            >
              เลือกแผนและชำระเงิน
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}