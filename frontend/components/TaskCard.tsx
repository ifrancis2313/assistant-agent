'use client'

import { Task } from '@/lib/types'

interface Props {
  task: Task
  onComplete: (id: string) => void
  onDelete: (id: string) => void
}

function priorityColor(p: number): string {
  if (p >= 7) return 'text-red-500'
  if (p >= 4) return 'text-amber-500'
  return 'text-green-500'
}

export default function TaskCard({ task, onComplete, onDelete }: Props) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-zinc-100 bg-white p-4 shadow-sm">
      <input
        type="checkbox"
        checked={task.completed}
        onChange={() => onComplete(task.id)}
        className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-zinc-900"
      />
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium text-zinc-900">{task.task}</p>
        <div className="mt-1 flex flex-wrap gap-2 text-xs text-zinc-400">
          <span>{task.date}</span>
          <span className={`font-semibold ${priorityColor(task.priority)}`}>
            P{task.priority.toFixed(1)}
          </span>
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-zinc-600">
            {task.bucket}
          </span>
        </div>
      </div>
      <button
        onClick={() => onDelete(task.id)}
        className="shrink-0 text-zinc-300 hover:text-red-400 transition-colors"
        aria-label="Delete task"
      >
        ✕
      </button>
    </div>
  )
}
