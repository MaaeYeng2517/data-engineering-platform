import type { BlogPost } from '@/lib/blog/types'

export interface ApiBlogPost {
  id: string
  author_id: string
  tenant_id: string
  title: string
  slug: string
  excerpt: string | null
  content: string
  featured_image_url: string | null
  category: string
  read_time: number
  view_count: number
  is_published: boolean
  status: string
  published_at: string | null
  created_at: string
  updated_at: string
  author_name: string | null
  tag_ids: string[]
  tag_names: string[]
}

export interface ApiBlogPostList {
  posts: ApiBlogPost[]
  total: number
  page: number
  page_size: number
}

export function apiPostToBlogPost(apiPost: ApiBlogPost): BlogPost {
  return {
    id: apiPost.id,
    title: apiPost.title,
    slug: apiPost.slug,
    excerpt: apiPost.excerpt ?? '',
    content: apiPost.content ?? '',
    coverImage: apiPost.featured_image_url,
    tags: apiPost.tag_names ?? [],
    author: apiPost.author_name ?? 'Unknown',
    published: apiPost.is_published ?? apiPost.status === 'published',
    publishedAt: apiPost.published_at,
    createdAt: apiPost.created_at ?? new Date().toISOString(),
    updatedAt: apiPost.updated_at ?? new Date().toISOString(),
    readingTime: apiPost.read_time ?? 5,
  }
}

export async function fetchBlogPosts(params?: {
  limit?: number
  offset?: number
  category?: string
  tag?: string
}): Promise<BlogPost[]> {
  const url = new URL('/api/backend/blog/posts', document.baseURI || window.location.origin)
  if (params?.limit) url.searchParams.set('limit', String(params.limit))
  if (params?.offset) url.searchParams.set('offset', String(params.offset))
  if (params?.category) url.searchParams.set('category', params.category)
  if (params?.tag) url.searchParams.set('tag', params.tag)

  const response = await fetch(url.toString(), {
    credentials: 'include',
    signal: AbortSignal.timeout(10000),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch blog posts: ${response.status}`)
  }

  const data = (await response.json()) as ApiBlogPostList
  return data.posts.map(apiPostToBlogPost)
}

export async function fetchBlogPostBySlug(slug: string): Promise<BlogPost | null> {
  const url = new URL(`/api/backend/blog/posts/${encodeURIComponent(slug)}`, document.baseURI || window.location.origin)

  const response = await fetch(url.toString(), {
    credentials: 'include',
    signal: AbortSignal.timeout(10000),
  })

  if (!response.ok) {
    if (response.status === 404) return null
    throw new Error(`Failed to fetch blog post: ${response.status}`)
  }

  const data = (await response.json()) as ApiBlogPost
  return apiPostToBlogPost(data)
}
