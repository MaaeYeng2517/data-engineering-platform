'use client'

import { useState, useCallback, useMemo } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { cn } from '@/lib/utils'
import { GripVertical, Plus, Trash2, Type, Image, Code, Heading1, Heading2, Quote } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export type BlockType = 'heading1' | 'heading2' | 'paragraph' | 'code' | 'quote' | 'image'

export interface Block {
  id: string
  type: BlockType
  content: string
  imageUrl?: string
  imageAlt?: string
}

const BLOCK_TYPES: { type: BlockType; label: string; icon: any }[] = [
  { type: 'heading1', label: 'H1', icon: Heading1 },
  { type: 'heading2', label: 'H2', icon: Heading2 },
  { type: 'paragraph', label: 'Paragraph', icon: Type },
  { type: 'code', label: 'Code', icon: Code },
  { type: 'quote', label: 'Quote', icon: Quote },
  { type: 'image', label: 'Image', icon: Image },
]

interface BlockItemProps {
  block: Block
  index: number
  onUpdate: (id: string, content: string, extra?: { imageUrl?: string; imageAlt?: string }) => void
  onRemove: (id: string) => void
}

function BlockItem({ block, index, onUpdate, onRemove }: BlockItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: block.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const renderEditor = () => {
    switch (block.type) {
      case 'heading1':
        return <Input value={block.content} onChange={(e) => onUpdate(block.id, e.target.value)} placeholder='Heading 1' className='text-2xl font-bold border-none bg-transparent focus:ring-0' />
      case 'heading2':
        return <Input value={block.content} onChange={(e) => onUpdate(block.id, e.target.value)} placeholder='Heading 2' className='text-xl font-bold border-none bg-transparent focus:ring-0' />
      case 'paragraph':
        return <Textarea value={block.content} onChange={(e) => onUpdate(block.id, e.target.value)} placeholder='Write content...' rows={3} className='border-none bg-transparent focus:ring-0 resize-none' />
      case 'code':
        return <Textarea value={block.content} onChange={(e) => onUpdate(block.id, e.target.value)} placeholder='Code...' rows={6} className='font-mono border-none bg-muted focus:ring-0 resize-none p-3 rounded' />
      case 'quote':
        return <Textarea value={block.content} onChange={(e) => onUpdate(block.id, e.target.value)} placeholder='Quote...' rows={2} className='border-l-4 border-primary pl-4 italic bg-transparent focus:ring-0 resize-none' />
      case 'image':
        return (
          <div className='space-y-2'>
            <Input value={block.imageUrl || ''} onChange={(e) => onUpdate(block.id, block.content, { imageUrl: e.target.value })} placeholder='Image URL' />
            <Input value={block.imageAlt || ''} onChange={(e) => onUpdate(block.id, block.content, { imageAlt: e.target.value })} placeholder='Alt text' />
            {block.imageUrl && <img src={block.imageUrl} alt={block.imageAlt || ''} className='max-h-48 rounded-lg object-cover' />}
          </div>
        )
    }
  }

  return (
    <Card ref={setNodeRef} style={style} className={cn('relative', isDragging && 'shadow-lg ring-2 ring-primary')}>
      <div
        {...attributes}
        {...listeners}
        className='absolute left-2 top-2 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground p-1'
        aria-label='Drag to reorder'
      >
        <GripVertical className='h-5 w-5' />
      </div>
      <div className='pl-10 pr-4 py-3 space-y-2'>
        <div className='flex items-center gap-2'>
          <span className='text-xs text-muted-foreground uppercase'>{BLOCK_TYPES.find(b => b.type === block.type)?.label}</span>
          <Button variant='ghost' size='icon' onClick={() => onRemove(block.id)} className='ml-auto'>
            <Trash2 className='h-4 w-4 text-destructive' />
          </Button>
        </div>
        {renderEditor()}
      </div>
    </Card>
  )
}

interface DragDropEditorProps {
  initialBlocks?: Block[]
  onChange: (blocks: Block[]) => void
  className?: string
}

export function DragDropEditor({ initialBlocks = [], onChange, className }: DragDropEditorProps) {
  const [blocks, setBlocks] = useState<Block[]>(initialBlocks.length > 0 ? initialBlocks : [
    { id: '1', type: 'heading1', content: '' },
    { id: '2', type: 'paragraph', content: '' },
  ])
  const [showAddMenu, setShowAddMenu] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setShowAddMenu(null)
  }, [])

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      setBlocks((items) => {
        const oldIndex = items.findIndex((b) => b.id === active.id)
        const newIndex = items.findIndex((b) => b.id === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }, [])

  const addBlock = useCallback((type: BlockType, afterId?: string) => {
    const newBlock: Block = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      type,
      content: '',
    }
    setBlocks((items) => {
      if (!afterId) return [...items, newBlock]
      const index = items.findIndex((b) => b.id === afterId)
      if (index === -1) return [...items, newBlock]
      return [...items.slice(0, index + 1), newBlock, ...items.slice(index + 1)]
    })
    setShowAddMenu(null)
  }, [])

  const updateBlock = useCallback((id: string, content: string, extra?: { imageUrl?: string; imageAlt?: string }) => {
    setBlocks((items) => items.map((b) => b.id === id ? { ...b, content, ...extra } : b))
  }, [])

  const removeBlock = useCallback((id: string) => {
    if (blocks.length <= 1) return
    setBlocks((items) => items.filter((b) => b.id !== id))
  }, [blocks.length])

  const blocksToMarkdown = useMemo(() => {
    return blocks.map((block) => {
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
  }, [blocks])

  const handleBlocksChange = useCallback((newBlocks: Block[]) => {
    setBlocks(newBlocks)
    onChange(newBlocks)
  }, [onChange])

  return (
    <div className={cn('space-y-4', className)}>
      <div className='flex flex-wrap gap-2 mb-4'>
        {BLOCK_TYPES.map((bt) => (
          <Button
            key={bt.type}
            variant='outline'
            size='sm'
            onClick={() => addBlock(bt.type)}
            className='gap-1'
          >
            <bt.icon className='h-4 w-4' />
            {bt.label}
          </Button>
        ))}
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
          <div className='space-y-3' role='list' aria-label='Content blocks'>
            {blocks.map((block, index) => (
              <div key={block.id} role='listitem'>
                <BlockItem
                  block={block}
                  index={index}
                  onUpdate={(id, content, extra) => updateBlock(id, content, extra)}
                  onRemove={removeBlock}
                />
                <div className='absolute left-4 bottom-0 -translate-y-1/2 translate-x-0 hidden group-hover:block'>
                  <Button variant='ghost' size='icon' onClick={() => setShowAddMenu(block.id)}>
                    <Plus className='h-4 w-4' />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <div className='border-t pt-4'>
        <Label className='block mb-2'>Markdown Output (copy to content field)</Label>
        <Textarea value={blocksToMarkdown} readOnly rows={8} className='font-mono text-sm' />
      </div>
    </div>
  )
}
