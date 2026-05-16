'use client'

import { useState, useCallback } from 'react'
import ChatPanel from '@/components/ChatPanel'
import TaskPanel from '@/components/TaskPanel'

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0)
  const handleAgentResponse = useCallback(() => setRefreshKey(k => k + 1), [])

  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Chat panel — full width on mobile, left half on desktop */}
      <div className="flex w-full flex-col md:w-1/2 md:border-r md:border-zinc-100">
        <ChatPanel onAgentResponse={handleAgentResponse} />
      </div>

      {/* Task panel — hidden on mobile, right half on desktop */}
      <div className="hidden md:flex md:w-1/2 md:flex-col overflow-hidden">
        <TaskPanel refreshKey={refreshKey} />
      </div>
    </div>
  )
}
