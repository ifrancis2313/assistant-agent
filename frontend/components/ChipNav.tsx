'use client'

import { View, BUCKETS } from '@/lib/types'

const VIEWS: View[] = ['All', ...BUCKETS]

interface Props {
  active: View
  onSelect: (view: View) => void
}

export default function ChipNav({ active, onSelect }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {VIEWS.map((view) => (
        <button
          key={view}
          onClick={() => onSelect(view)}
          className={`shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            active === view
              ? 'bg-zinc-900 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
          }`}
        >
          {view}
        </button>
      ))}
    </div>
  )
}
