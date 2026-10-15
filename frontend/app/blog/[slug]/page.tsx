'use client'

import { notFound, useParams } from 'next/navigation'
import { useBlogStore } from '@/lib/blog/store'
import { Markdown } from '@/components/blog/markdown'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function Detail() {
  const params = useParams<{ slug: string }>()
  const { getBySlug, hydrated } = useBlogStore()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  if (!mounted || !hydrated) return <div className='container py-10 px-4'>Loading...</div>
  const post = getBySlug(params.slug)
  if (!post) return notFound()
  return (
    <div className='container mx-auto max-w-3xl py-10 px-4'>
      <Link href='/' className='text-sm underline'>← กลับ</Link>
      <h1 className='text-3xl font-bold mt-4 mb-2'>{post.title}</h1>
      <div className='flex gap-2 mb-6 flex-wrap'>
        {post.tags.map((t) => <Badge key={t}>{t}</Badge>)}
      </div>
      <Markdown content={post.content} />
    </div>
  )
}
