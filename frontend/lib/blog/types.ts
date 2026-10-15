export interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string
  content: string
  coverImage?: string | null
  tags: string[]
  author: string
  published: boolean
  publishedAt: string | null
  createdAt: string
  updatedAt: string
  readingTime?: number
}

export interface BlogListItem extends Omit<BlogPost, 'content'> {}
