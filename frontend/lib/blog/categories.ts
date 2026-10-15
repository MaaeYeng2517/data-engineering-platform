'use client'

import { useEffect, useState } from 'react'

export interface Category {
  id: string
  name: string
  slug: string
  color: string
  description?: string
  createdAt: string
  updatedAt: string
}

export type CategoryColor =
  | 'blue'
  | 'violet'
  | 'amber'
  | 'emerald'
  | 'cyan'
  | 'rose'
  | 'indigo'
  | 'teal'
  | 'fuchsia'
  | 'orange'

export const CATEGORY_COLORS: { value: CategoryColor; label: string }[] = [
  { value: 'blue', label: 'Blue' },
  { value: 'violet', label: 'Violet' },
  { value: 'amber', label: 'Amber' },
  { value: 'emerald', label: 'Emerald' },
  { value: 'cyan', label: 'Cyan' },
  { value: 'rose', label: 'Rose' },
  { value: 'indigo', label: 'Indigo' },
  { value: 'teal', label: 'Teal' },
  { value: 'fuchsia', label: 'Fuchsia' },
  { value: 'orange', label: 'Orange' },
]

export const CATEGORY_COLOR_CLASSES: Record<CategoryColor, string> = {
  blue: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  violet: 'bg-violet-500/10 text-violet-600 border-violet-500/20',
  amber: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  emerald: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  cyan: 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20',
  rose: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
  indigo: 'bg-indigo-500/10 text-indigo-600 border-indigo-500/20',
  teal: 'bg-teal-500/10 text-teal-600 border-teal-500/20',
  fuchsia: 'bg-fuchsia-500/10 text-fuchsia-600 border-fuchsia-500/20',
  orange: 'bg-orange-500/10 text-orange-600 border-orange-500/20',
}

export function getCategoryColorClass(color: string): string {
  if (color in CATEGORY_COLOR_CLASSES) {
    return CATEGORY_COLOR_CLASSES[color as CategoryColor]
  }
  let hash = 0
  for (let i = 0; i < color.length; i++) hash = (hash * 31 + color.charCodeAt(i)) | 0
  const keys = Object.keys(CATEGORY_COLOR_CLASSES) as CategoryColor[]
  return CATEGORY_COLOR_CLASSES[keys[Math.abs(hash) % keys.length]]
}

export const CATEGORY_COLOR_BG: Record<CategoryColor, string> = {
  blue: 'bg-blue-500/20',
  violet: 'bg-violet-500/20',
  amber: 'bg-amber-500/20',
  emerald: 'bg-emerald-500/20',
  cyan: 'bg-cyan-500/20',
  rose: 'bg-rose-500/20',
  indigo: 'bg-indigo-500/20',
  teal: 'bg-teal-500/20',
  fuchsia: 'bg-fuchsia-500/20',
  orange: 'bg-orange-500/20',
}

export function getCategoryBgClass(color: string): string {
  if (color in CATEGORY_COLOR_BG) {
    return CATEGORY_COLOR_BG[color as CategoryColor]
  }
  let hash = 0
  for (let i = 0; i < color.length; i++) hash = (hash * 31 + color.charCodeAt(i)) | 0
  const keys = Object.keys(CATEGORY_COLOR_BG) as CategoryColor[]
  return CATEGORY_COLOR_BG[keys[Math.abs(hash) % keys.length]]
}

export function slugifyCategory(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\u0E00-\u0E7F\s-]+/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

const KEY = 'dataair_blog_categories_v1'

const defaultCategories: Category[] = [
  {
    id: '1',
    name: 'Technology',
    slug: 'technology',
    color: 'blue',
    description: 'Platform architecture and underlying technologies',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    name: 'Data Engineering',
    slug: 'data-engineering',
    color: 'violet',
    description: 'ETL, data pipelines, warehouses and orchestration',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '3',
    name: 'AI & Machine Learning',
    slug: 'ai-ml',
    color: 'amber',
    description: 'Machine learning, RAG and AI agents',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '4',
    name: 'Tutorial',
    slug: 'tutorial',
    color: 'emerald',
    description: 'Step-by-step guides and how-tos',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '5',
    name: 'Architecture',
    slug: 'architecture',
    color: 'cyan',
    description: 'System design and architectural patterns',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '6',
    name: 'Governance',
    slug: 'governance',
    color: 'rose',
    description: 'Security, compliance and data governance',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
]

function load(): Category[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Category[]
    if (Array.isArray(parsed) && parsed.length > 0) return parsed
    return defaultCategories
  } catch {
    return defaultCategories
  }
}

function save(categories: Category[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(KEY, JSON.stringify(categories))
}

export function useCategoryStore() {
  const [categories, setCategories] = useState<Category[]>([])
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setCategories(load())
    setHydrated(true)
  }, [])

  const persist = (next: Category[]) => {
    setCategories(next)
    save(next)
  }

  const list = () => [...categories].sort((a, b) => a.name.localeCompare(b.name))

  const getBySlug = (slug: string) => categories.find((c) => c.slug === slug)
  const getById = (id: string) => categories.find((c) => c.id === id)

  const create = (input: {
    name: string
    color: CategoryColor
    description?: string
  }) => {
    const now = new Date().toISOString()
    const baseSlug = slugifyCategory(input.name)
    let finalSlug = baseSlug
    let i = 1
    while (categories.some((c) => c.slug === finalSlug)) {
      finalSlug = `${baseSlug}-${i++}`
    }
    const category: Category = {
      id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`,
      name: input.name,
      slug: finalSlug,
      color: input.color,
      description: input.description,
      createdAt: now,
      updatedAt: now,
    }
    persist([...categories, category])
    return category
  }

  const update = (id: string, input: Partial<Category>) => {
    const now = new Date().toISOString()
    const next = categories.map((c) => {
      if (c.id !== id) return c
      let finalSlug = c.slug
      if (input.name && input.name !== c.name) {
        const baseSlug = slugifyCategory(input.name)
        finalSlug = baseSlug
        let i = 1
        while (categories.some((x) => x.id !== id && x.slug === finalSlug)) {
          finalSlug = `${baseSlug}-${i++}`
        }
      }
      return {
        ...c,
        ...input,
        slug: finalSlug,
        updatedAt: now,
      }
    })
    persist(next)
    return next.find((c) => c.id === id)
  }

  const remove = (id: string) => {
    persist(categories.filter((c) => c.id !== id))
  }

  return {
    categories,
    hydrated,
    list,
    getBySlug,
    getById,
    create,
    update,
    remove,
  }
}
