'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { useRouter } from 'next/navigation'
import { useBlogStore } from '@/lib/blog/store'
import { BlogPost } from '@/lib/blog/types'
import { DragDropEditor, Block } from './drag-drop-editor'

const schema = z.object({
  title: z.string().min(1),
  slug: z.string().min(1),
  excerpt: z.string().min(1),
  content: z.string().min(1),
  coverImage: z.string().optional(),
  tags: z.string().optional().default(''),
  author: z.string().min(1),
  published: z.boolean().default(false),
})

type FormValues = z.infer<typeof schema>

function parseTags(tags: string): string[] {
  return tags.split(',').map((s) => s.trim()).filter(Boolean)
}

function markdownToBlocks(markdown: string): Block[] {
  if (!markdown.trim()) return []
  const blocks: Block[] = []
  const lines = markdown.split('\n')
  let currentBlock: Block | null = null
  let codeContent = ''
  let inCodeBlock = false

  for (const line of lines) {
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        blocks.push({ id: `${Date.now()}-${Math.random()}`, type: 'code', content: codeContent.trim() })
        codeContent = ''
        inCodeBlock = false
        currentBlock = null
      } else {
        inCodeBlock = true
        currentBlock = null
      }
      continue
    }

    if (inCodeBlock) {
      codeContent += line + '\n'
      continue
    }

    if (line.startsWith('# ')) {
      if (currentBlock) blocks.push(currentBlock)
      currentBlock = { id: `${Date.now()}-${Math.random()}`, type: 'heading1', content: line.slice(2) }
    } else if (line.startsWith('## ')) {
      if (currentBlock) blocks.push(currentBlock)
      currentBlock = { id: `${Date.now()}-${Math.random()}`, type: 'heading2', content: line.slice(3) }
    } else if (line.startsWith('> ')) {
      if (currentBlock) blocks.push(currentBlock)
      currentBlock = { id: `${Date.now()}-${Math.random()}`, type: 'quote', content: line.slice(2) }
    } else if (line.startsWith('![') && line.includes('](')) {
      const altMatch = line.match(/!\[([^\]]*)\]/)
      const urlMatch = line.match(/\(([^)]+)\)/)
      if (currentBlock) blocks.push(currentBlock)
      currentBlock = {
        id: `${Date.now()}-${Math.random()}`,
        type: 'image',
        content: '',
        imageUrl: urlMatch?.[1] || '',
        imageAlt: altMatch?.[1] || '',
      }
    } else if (line.trim() === '') {
      if (currentBlock) blocks.push(currentBlock)
      currentBlock = null
    } else {
      if (!currentBlock || currentBlock.type !== 'paragraph') {
        if (currentBlock) blocks.push(currentBlock)
        currentBlock = { id: `${Date.now()}-${Math.random()}`, type: 'paragraph', content: line }
      } else {
        currentBlock.content += '\n' + line
      }
    }
  }
  if (currentBlock) blocks.push(currentBlock)
  return blocks.length > 0 ? blocks : [{ id: '1', type: 'heading1', content: '' }, { id: '2', type: 'paragraph', content: '' }]
}

export function PostForm({ post }: { post?: BlogPost }) {
  const router = useRouter()
  const { create, update } = useBlogStore()
  const [activeTab, setActiveTab] = useState<string>('visual')
  const [blocks, setBlocks] = useState<Block[]>([])

  useEffect(() => {
    if (post?.content) {
      setBlocks(markdownToBlocks(post.content))
    }
  }, [post?.content])

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: post?.title || '',
      slug: post?.slug || '',
      excerpt: post?.excerpt || '',
      content: post?.content || '',
      coverImage: post?.coverImage || '',
      tags: post?.tags.join(', ') || '',
      author: post?.author || 'Admin',
      published: post?.published || false,
    },
  })

  const handleBlocksChange = (newBlocks: Block[]) => {
    setBlocks(newBlocks)
    const markdown = newBlocks.map((block) => {
      switch (block.type) {
        case 'heading1': return `# ${block.content}`
        case 'heading2': return `## ${block.content}`
        case 'paragraph': return block.content
        case 'code': return `\`\`\`\n${block.content}\n\`\`\``
        case 'quote': return `> ${block.content}`
        case 'image': return block.imageUrl ? `![${block.imageAlt || ''}](${block.imageUrl})` : ''
        default: return block.content
      }
    }).filter(Boolean).join('\n\n')
    form.setValue('content', markdown, { shouldValidate: true })
  }

  const onSubmit = (v: FormValues) => {
    const data = {
      title: v.title,
      slug: v.slug,
      excerpt: v.excerpt,
      content: v.content,
      coverImage: v.coverImage || null,
      tags: parseTags(v.tags || ''),
      author: v.author,
      published: v.published,
    }
    if (post) update(post.id, data)
    else create(data)
    router.push('/blog/admin')
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className='space-y-6'>
      <div className='grid md:grid-cols-2 gap-4'>
        <div><Label>ชื่อเรื่อง</Label><Input {...form.register('title')} /></div>
        <div><Label>Slug</Label><Input {...form.register('slug')} /></div>
      </div>
      <div><Label>คำอธิบายย่อ</Label><Textarea rows={2} {...form.register('excerpt')} /></div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className='w-full'>
        <TabsList className='grid w-full grid-cols-2'>
          <TabsTrigger value='visual'>Visual Editor (Drag & Drop)</TabsTrigger>
          <TabsTrigger value='markdown'>Markdown</TabsTrigger>
        </TabsList>
        <TabsContent value='visual'>
          <DragDropEditor initialBlocks={blocks} onChange={handleBlocksChange} />
        </TabsContent>
        <TabsContent value='markdown'>
          <div><Label>เนื้อหา (Markdown)</Label><Textarea rows={20} {...form.register('content')} placeholder='# หัวข้อ\n\nเนื้อหา...' /></div>
        </TabsContent>
      </Tabs>

      <div className='grid md:grid-cols-2 gap-4'>
        <div><Label>Cover Image URL</Label><Input {...form.register('coverImage')} /></div>
        <div><Label>Tags (,)</Label><Input {...form.register('tags')} /></div>
      </div>
      <div className='grid md:grid-cols-2 gap-4'>
        <div><Label>ผู้เขียน</Label><Input {...form.register('author')} /></div>
        <div className='flex items-center gap-2 pt-6'>
          <Switch checked={form.watch('published')} onCheckedChange={(v) => form.setValue('published', v)} />
          <Label>เผยแพร่ทันที</Label>
        </div>
      </div>
      <div className='flex gap-2'>
        <Button type='submit'>{post ? 'บันทึก' : 'สร้าง'}</Button>
        <Button type='button' variant='outline' onClick={() => router.back()}>ยกเลิก</Button>
      </div>
    </form>
  )
}
