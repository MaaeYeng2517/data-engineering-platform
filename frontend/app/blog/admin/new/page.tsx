'use client'

import { PostForm } from '@/components/blog/post-form'

export default function New() {
  return (
    <div className='container max-w-4xl py-10 px-4'>
      <h1 className='text-2xl font-bold mb-6'>สร้างบทความใหม่</h1>
      <PostForm />
    </div>
  )
}
