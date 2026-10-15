'use client'

import { useState } from 'react'
import {
  Edit3,
  Plus,
  Tag,
  Trash2,
} from 'lucide-react'

import { useCategoryStore } from '@/lib/blog/categories'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  getCategoryColorClass,
  getCategoryBgClass,
  type Category,
  type CategoryColor,
  CATEGORY_COLORS,
} from '@/lib/blog/categories'

function ColorPicker({
  value,
  onChange,
}: {
  value: CategoryColor
  onChange: (v: CategoryColor) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {CATEGORY_COLORS.map((c) => (
        <button
          key={c.value}
          type="button"
          onClick={() => onChange(c.value)}
          aria-label={c.label}
          className={`h-9 w-9 rounded-lg border-2 transition-all ${
            value === c.value
              ? 'border-foreground ring-2 ring-ring ring-offset-2 ring-offset-background'
              : 'border-border hover:border-foreground'
          } ${getCategoryBgClass(c.value)}`}
        >
          <span className="sr-only">{c.label}</span>
          <div className="h-full w-full rounded-sm" />
        </button>
      ))}
    </div>
  )
}

function CategoryForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<Category>
  onSubmit: (data: { name: string; color: CategoryColor; description?: string }) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name || '')
  const [color, setColor] = useState<CategoryColor>((initial?.color as CategoryColor) || 'blue')
  const [description, setDescription] = useState(initial?.description || '')

  const handleSubmit = () => {
    if (!name.trim()) return
    onSubmit({ name: name.trim(), color, description: description.trim() || undefined })
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="space-y-2">
        <Label htmlFor="cat-name">Name</Label>
        <Input
          id="cat-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Data Engineering"
          autoFocus
        />
      </div>
      <div className="space-y-2">
        <Label>Color</Label>
        <ColorPicker value={color} onChange={setColor} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="cat-desc">Description (optional)</Label>
        <Textarea
          id="cat-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What articles does this category cover?"
          rows={3}
        />
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSubmit}>{initial ? 'Save' : 'Create'}</Button>
      </DialogFooter>
    </div>
  )
}

function CategoryCard({ category }: { category: Category }) {
  const { update, remove } = useCategoryStore()
  const colorClass = getCategoryColorClass(category.color)

  const [editOpen, setEditOpen] = useState(false)

  return (
    <>
      <Card className="group transition-shadow hover:shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className={cn(colorClass, 'flex h-8 w-8 items-center justify-center rounded-lg border')}>
                <Tag className="h-4 w-4" />
              </div>
              <CardTitle className="text-lg">{category.name}</CardTitle>
            </div>
            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              <Dialog open={editOpen} onOpenChange={setEditOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="ghost">
                    <Edit3 className="h-3.5 w-3.5" />
                    <span className="sr-only">Edit</span>
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Edit category</DialogTitle>
                    <DialogDescription>
                      Update the name, color and description for this category.
                    </DialogDescription>
                  </DialogHeader>
                  <CategoryForm
                    initial={category}
                    onSubmit={(data) => {
                      update(category.id, data)
                      setEditOpen(false)
                    }}
                    onCancel={() => setEditOpen(false)}
                  />
                </DialogContent>
              </Dialog>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="sr-only">Delete</span>
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete category</AlertDialogTitle>
                    <AlertDialogDescription>
                      Remove &quot;{category.name}&quot; from the list of categories.
                      This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground"
                      onClick={() => remove(category.id)}
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
          {category.description && (
            <p className="text-sm text-muted-foreground">{category.description}</p>
          )}
        </CardHeader>
        <CardContent>
          <Badge variant="outline" className={colorClass}>
            {category.slug}
          </Badge>
        </CardContent>
      </Card>
    </>
  )
}

export function CategoryManager() {
  const { categories, hydrated, create, list } = useCategoryStore()
  const [createOpen, setCreateOpen] = useState(false)

  const allCategories = hydrated ? list() : []

  return (
    <section className="border-t bg-muted/30 py-16">
      <div className="container">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">หมวดหมู่บทความ</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              จัดการหมวดหมู่และแท็กสำหรับบทความ
            </p>
          </div>
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                เพิ่มหมวดหมู่
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>เพิ่มหมวดหมู่ใหม่</DialogTitle>
                <DialogDescription>
                  สร้างหมวดหมู่ใหม่เพื่อจัดกลุ่มบทความตามหัวข้อเทคโนโลยี
                </DialogDescription>
              </DialogHeader>
              <CategoryForm
                onSubmit={(data) => {
                  create(data)
                  setCreateOpen(false)
                }}
                onCancel={() => setCreateOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        {!hydrated ? (
          <p className="text-muted-foreground">กำลังโหลดหมวดหมู่...</p>
        ) : allCategories.length === 0 ? (
          <div className="py-12 text-center">
            <Tag className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
            <p className="text-muted-foreground">
              ยังไม่มีหมวดหมู่ — เพิ่มหมวดหมู่แรกของคุณ
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {allCategories.map((cat) => (
              <CategoryCard key={cat.id} category={cat} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
