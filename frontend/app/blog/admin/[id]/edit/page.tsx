'use client'

import { useParams } from 'next/navigation'
import { useBlogStore } from '@/lib/blog/store'
import { PostForm } from '@/components/blog/post-form'
import { useEffect, useState } from 'react'

export default function Edit() {
  const params = useParams<{ id: string }>()
  const { getById, hydrated } = useBlogStore()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  if (!mounted || !hydrated) return <div className='container py-10 px-4'>Loading...</div>
  const post = getById(params.id)
  if (!post) return <div className='container py-10 px-4'>ไม่พบบทความ <a href='/blog/admin' className='underline'>กลับ</a></div>
  return (
    <div className='container max-w-4xl py-10 px-4'>
      <h1 className='text-2xl font-bold mb-6'>แก้ไขบทความ</h1>
      <PostForm post={post} />
    </div>
  )
}
