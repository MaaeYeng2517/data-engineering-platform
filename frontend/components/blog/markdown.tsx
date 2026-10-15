'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSlug from 'rehype-slug'
import rehypeAutolinkHeadings from 'rehype-autolink-headings'
import { cn } from '@/lib/utils'

export function Markdown({ content }: { content: string }) {
  return (
    <article className={cn('prose prose-slate dark:prose-invert max-w-none prose-img:rounded-lg prose-a:text-primary')}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug, [rehypeAutolinkHeadings, { behavior: 'wrap' }]]}>
        {content}
      </ReactMarkdown>
    </article>
  )
}
