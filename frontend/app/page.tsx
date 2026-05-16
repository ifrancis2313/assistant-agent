import TaskPanel from '@/components/TaskPanel'

export default function Home() {
  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Chat panel placeholder — Issue #5 */}
      <div className="hidden md:flex md:w-1/2 items-center justify-center border-r border-zinc-100 bg-white text-sm text-zinc-300">
        Chat coming soon
      </div>

      {/* Task panel */}
      <div className="w-full md:w-1/2 overflow-hidden">
        <TaskPanel />
      </div>
    </div>
  )
}
