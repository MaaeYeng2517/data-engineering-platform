'use client'

import Link from 'next/link'
import { useBlogStore } from '@/lib/blog/store'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useMemo, useState } from 'react'

export default function HomeBlogPage() {
  const { list, hydrated } = useBlogStore()
  const posts = list(true)
  const [q, setQ] = useState('')
  const [tag, setTag] = useState<string | null>(null)

  const tags = useMemo(() => {
    const set = new Set<string>()
    posts.forEach((p) => p.tags.forEach((t) => set.add(t)))
    return Array.from(set)
  }, [posts])

  const filtered = useMemo(() => {
    return posts.filter((p) => {
      const text = (p.title + ' ' + p.excerpt + ' ' + p.tags.join(' ')).toLowerCase()
      const matchQ = q ? text.includes(q.toLowerCase()) : true
      const matchT = tag ? p.tags.includes(tag) : true
      return matchQ && matchT
    })
  }, [posts, q, tag])

  return (
    <div className='container mx-auto max-w-6xl py-10 px-4'>
      <div className='mb-8 flex flex-col gap-4'>
        <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
          <div>
            <h1 className='text-3xl font-bold'>Blog</h1>
            <p className='text-muted-foreground'>รวมบทความล่าสุด</p>
          </div>
          <div className='flex gap-2'>
            <Button variant='outline' asChild><Link href='/dataair'>DataAir Site</Link></Button>
            <Button variant='outline' asChild><Link href='/chat'>Chat</Link></Button>
            <Button asChild><Link href='/blog/admin'>Admin</Link></Button>
          </div>
        </div>
        <input
          placeholder='ค้นหาบทความ...'
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className='flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'
        />
        {tags.length > 0 && (
          <div className='flex flex-wrap gap-2'>
            <Badge variant={tag === null ? 'default' : 'secondary'} className='cursor-pointer' onClick={() => setTag(null)}>
              ทั้งหมด
            </Badge>
            {tags.map((t) => (
              <Badge key={t} variant={tag === t ? 'default' : 'secondary'} className='cursor-pointer' onClick={() => setTag(t)}>
                {t}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {!hydrated ? (
        <p className='text-muted-foreground'>กำลังโหลด...</p>
      ) : filtered.length === 0 ? (
        <p className='text-muted-foreground'>ยังไม่มีบทความที่เผยแพร่</p>
      ) : (
        <div className='grid gap-6 sm:grid-cols-2 lg:grid-cols-3'>
          {filtered.map((post) => (
            <Link key={post.id} href={`/blog/${post.slug}`}>
              <Card className='h-full transition hover:shadow-md'>
                <CardHeader>
                  <CardTitle className='line-clamp-2'>{post.title}</CardTitle>
                  <CardDescription className='line-clamp-2'>{post.excerpt}</CardDescription>
                </CardHeader>
                <CardContent className='flex flex-wrap items-center gap-2'>
                  {post.tags.slice(0, 3).map((t) => (
                    <Badge key={t} variant='outline'>{t}</Badge>
                  ))}
                  {post.readingTime && <span className='text-xs text-muted-foreground ml-auto'>{post.readingTime} นาทีอ่าน</span>}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
