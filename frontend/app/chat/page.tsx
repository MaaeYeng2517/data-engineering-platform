export default function ChatPage() {
  return (
    <div className='container mx-auto py-10 px-4'>
      <h1 className='text-3xl font-bold mb-4'>Chat</h1>
      <p className='text-muted-foreground'>Chat module</p>
      <div className='mt-6 flex gap-2'>
        <a href='/' className='text-sm underline'>← Blog</a>
        <a href='/dataair' className='text-sm underline'>DataAir Site</a>
      </div>
    </div>
  )
}
