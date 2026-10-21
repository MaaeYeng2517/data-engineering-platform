'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchSubscribeStatus } from '@/lib/api/billing'

const POLL_INTERVAL_MS = 2000
const MAX_POLLS = 30

export function SubscribeStatusView() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id')

  const [state, setState] = useState<'waiting' | 'activated' | 'failed' | 'unknown'>('waiting')
  const [message, setMessage] = useState('กำลังรอการยืนยันการชำระเงิน…')

  useEffect(() => {
    if (!sessionId) {
      setState('unknown')
      setMessage('ไม่พบรหัสรายการชำระเงิน — กรุณาเริ่มต้นการสมัครใช้งานใหม่')
      return
    }

    let cancelled = false
    let attempts = 0

    async function poll() {
      attempts += 1
      try {
        const status = await fetchSubscribeStatus(sessionId as string)
        if (cancelled) return
        if (status.activated) {
          setState('activated')
          setMessage(status.message || 'ชำระเงินสำเร็จ — workspace ของคุณพร้อมใช้งาน')
          return
        }
        if (status.status === 'failed') {
          setState('failed')
          setMessage(status.message || 'การชำระเงินไม่สำเร็จ')
          return
        }
        setMessage(status.message || 'กำลังรอการยืนยันการชำระเงิน…')
      } catch {
        if (cancelled) return
        setMessage('กำลังเชื่อมต่อเซิร์ฟเวอร์…')
      }

      if (!cancelled && attempts < MAX_POLLS) {
        window.setTimeout(poll, POLL_INTERVAL_MS)
      } else if (!cancelled) {
        setState('failed')
        setMessage('ตรวจสอบสถานะไม่สำเร็จ — หากชำระเงินแล้ว บัญชีจะถูกเปิดใช้งานภายในไม่กี่นาที')
      }
    }

    poll()
    return () => {
      cancelled = true
    }
  }, [sessionId])

  return (
    <Card className="mx-auto w-full max-w-md">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
          {state === 'activated' && <CheckCircle2 className="h-6 w-6 text-green-600" />}
          {state === 'failed' && <XCircle className="h-6 w-6 text-destructive" />}
          {state === 'waiting' && <Loader2 className="h-6 w-6 animate-spin text-primary" />}
          {state === 'unknown' && <XCircle className="h-6 w-6 text-muted-foreground" />}
        </div>
        <CardTitle className="text-2xl">
          {state === 'activated'
            ? 'ชำระเงินสำเร็จ'
            : state === 'failed'
              ? 'ยังไม่สามารถเปิดใช้งานได้'
              : state === 'unknown'
                ? 'ไม่พบรายการชำระเงิน'
                : 'กำลังประมวลผลการชำระเงิน'}
        </CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {state === 'activated' ? (
          <Button asChild className="w-full">
            <Link href="/dashboard">เข้าสู่ workspace</Link>
          </Button>
        ) : (
          <>
            <Button asChild className="w-full" variant="outline">
              <Link href="/subscribe">กลับไปหน้าเลือกแผน</Link>
            </Button>
            <Button asChild className="w-full" variant="ghost">
              <Link href="/login">มีบัญชีอยู่แล้ว — เข้าสู่ระบบ</Link>
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}
