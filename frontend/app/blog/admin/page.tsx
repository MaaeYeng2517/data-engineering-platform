'use client'

import Link from 'next/link'
import { useBlogStore } from '@/lib/blog/store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Pencil, Plus, Trash2, Eye } from 'lucide-react'

export default function Admin() {
  const { posts, remove, hydrated } = useBlogStore()
  if (!hydrated) return <div className='container py-10 px-4'>Loading...</div>
  return (
    <div className='container mx-auto max-w-6xl py-10 px-4'>
      <div className='mb-6 flex justify-between'>
        <h1 className='text-2xl font-bold'>Blog Admin</h1>
        <Button asChild><Link href='/blog/admin/new'><Plus className='mr-2 h-4 w-4'/>New</Link></Button>
      </div>
      <div className='grid gap-4'>
        {posts.map((p) => (
          <Card key={p.id}>
            <CardHeader className='flex flex-row justify-between'>
              <CardTitle className='text-lg'>{p.title}</CardTitle>
              <div className='flex gap-2'>
                <Button size='sm' variant='outline' asChild><Link href={`/blog/${p.slug}`} target='_blank'><Eye className='h-4 w-4'/></Link></Button>
                <Button size='sm' variant='outline' asChild><Link href={`/blog/admin/${p.id}/edit`}><Pencil className='h-4 w-4'/></Link></Button>
                <Button size='sm' variant='destructive' onClick={() => remove(p.id)}><Trash2 className='h-4 w-4'/></Button>
              </div>
            </CardHeader>
            <CardContent className='flex gap-2 text-sm'>
              <Badge variant={p.published?'default':'secondary'}>{p.published?'เผยแพร่':'ร่าง'}</Badge>
              <span>/{p.slug}</span>
            </CardContent>
          </Card>
        ))}
        {posts.length===0 && <p className='text-muted-foreground'>ยังไม่มีบทความ</p>}
      </div>
      <div className='mt-6'><Button variant='ghost' asChild><Link href='/'>กลับหน้าแรก</Link></Button></div>
    </div>
  )
}
