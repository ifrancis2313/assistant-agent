'use client'

import { useState, useEffect, useCallback } from 'react'
import { Task, View } from '@/lib/types'
import { getTasks, completeTask, deleteTask } from '@/lib/api'
import ChipNav from './ChipNav'
import TaskCard from './TaskCard'

export default function TaskPanel() {
  const [activeView, setActiveView] = useState<View>('All')
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      const bucket = activeView === 'All' ? undefined : activeView
      setTasks(await getTasks(bucket))
    } catch {
      // backend may not be running locally yet
    } finally {
      setLoading(false)
    }
  }, [activeView])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  const handleComplete = async (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id))
    try { await completeTask(id) } catch { fetchTasks() }
  }

  const handleDelete = async (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id))
    try { await deleteTask(id) } catch { fetchTasks() }
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <ChipNav active={activeView} onSelect={setActiveView} />

      {loading ? (
        <div className="flex flex-1 items-center justify-center text-sm text-zinc-400">
          Loading…
        </div>
      ) : tasks.length === 0 ? (
        <div className="flex flex-1 items-center justify-center text-sm text-zinc-400">
          No tasks in {activeView}
        </div>
      ) : (
        <div className="flex flex-col gap-3 overflow-y-auto">
          {tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onComplete={handleComplete}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
