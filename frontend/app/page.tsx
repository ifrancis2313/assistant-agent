'use client'

import { useState, useCallback } from 'react'
import ChatPanel from '@/components/ChatPanel'
import TaskPanel from '@/components/TaskPanel'

type Tab = 'chat' | 'tasks'

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [activeTab, setActiveTab] = useState<Tab>('chat')

  const handleAgentResponse = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  return (
    <div className="flex h-screen flex-col bg-zinc-50 md:flex-row">

      {/* Desktop: side-by-side. Mobile: tab-controlled panels */}
      <div className={`flex flex-1 flex-col md:w-1/2 md:border-r md:border-zinc-100 md:flex ${activeTab === 'chat' ? 'flex' : 'hidden md:flex'}`}>
        <ChatPanel onAgentResponse={handleAgentResponse} />
      </div>

      <div className={`flex flex-1 flex-col overflow-hidden md:w-1/2 md:flex ${activeTab === 'tasks' ? 'flex' : 'hidden md:flex'}`}>
        <TaskPanel refreshKey={refreshKey} />
      </div>

      {/* Mobile tab bar — hidden on desktop */}
      <nav className="flex shrink-0 border-t border-zinc-100 bg-white md:hidden">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex flex-1 flex-col items-center gap-0.5 py-3 text-xs font-medium transition-colors ${
            activeTab === 'chat' ? 'text-zinc-900' : 'text-zinc-400'
          }`}
        >
          <span className="text-lg">💬</span>
          Chat
        </button>
        <button
          onClick={() => setActiveTab('tasks')}
          className={`flex flex-1 flex-col items-center gap-0.5 py-3 text-xs font-medium transition-colors ${
            activeTab === 'tasks' ? 'text-zinc-900' : 'text-zinc-400'
          }`}
        >
          <span className="text-lg">✅</span>
          Tasks
        </button>
      </nav>
    </div>
  )
}
