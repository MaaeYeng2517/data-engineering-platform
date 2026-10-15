'use client'

import { BlogPost } from './types'
import { getReadingTime, slugify } from './utils'
import { useEffect, useState } from 'react'

const KEY = 'dataair_blog_posts_v1'

function load(): BlogPost[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    return JSON.parse(raw) as BlogPost[]
  } catch {
    return []
  }
}

function save(posts: BlogPost[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(KEY, JSON.stringify(posts))
}

export function useBlogStore() {
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setPosts(load())
    setHydrated(true)
  }, [])

  const persist = (next: BlogPost[]) => {
    setPosts(next)
    save(next)
  }

  const list = (publishedOnly = true) =>
    [...posts]
      .filter((p) => (publishedOnly ? p.published : true))
      .sort((a, b) => {
        const ta = a.publishedAt ? new Date(a.publishedAt).getTime() : new Date(a.createdAt).getTime()
        const tb = b.publishedAt ? new Date(b.publishedAt).getTime() : new Date(b.createdAt).getTime()
        return tb - ta
      })

  const getBySlug = (slug: string) => posts.find((p) => p.slug === slug && p.published)
  const getById = (id: string) => posts.find((p) => p.id === id)

  const create = (input: Partial<BlogPost>) => {
    const now = new Date().toISOString()
    const id = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`
    const title = input.title || 'Untitled'
    const baseSlug = input.slug?.trim() || slugify(title)
    let finalSlug = baseSlug
    let i = 1
    while (posts.some((p) => p.slug === finalSlug)) {
      finalSlug = `${baseSlug}-${i++}`
    }
    const post: BlogPost = {
      id,
      title,
      slug: finalSlug,
      excerpt: input.excerpt || '',
      content: input.content || '',
      coverImage: input.coverImage || null,
      tags: input.tags || [],
      author: input.author || 'Admin',
      published: input.published ?? false,
      publishedAt: input.published ? (input.publishedAt || now) : null,
      createdAt: now,
      updatedAt: now,
      readingTime: getReadingTime(input.content || ''),
    }
    persist([...posts, post])
    return post
  }

  const update = (id: string, input: Partial<BlogPost>) => {
    const now = new Date().toISOString()
    const next = posts.map((p) => {
      if (p.id !== id) return p
      const slugVal = input.slug?.trim() || p.slug
      let finalSlug = slugVal
      if (slugVal !== p.slug) {
        let i = 1
        while (posts.some((x) => x.id !== id && x.slug === finalSlug)) {
          finalSlug = `${slugVal}-${i++}`
        }
      }
      const published = input.published ?? p.published
      const publishedAt = published ? (input.publishedAt || p.publishedAt || now) : null
      return {
        ...p,
        ...input,
        slug: finalSlug,
        published,
        publishedAt,
        updatedAt: now,
        readingTime: input.content !== undefined ? getReadingTime(input.content) : p.readingTime,
      }
    })
    persist(next)
    return next.find((p) => p.id === id)
  }

  const remove = (id: string) => {
    persist(posts.filter((p) => p.id !== id))
  }

  return { posts, hydrated, list, getBySlug, getById, create, update, remove }
}
