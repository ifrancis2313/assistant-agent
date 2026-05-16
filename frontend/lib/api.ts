import { Task } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getTasks(bucket?: string): Promise<Task[]> {
  const url = bucket ? `${API_URL}/tasks?bucket=${bucket}` : `${API_URL}/tasks`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch tasks')
  return res.json()
}

export async function completeTask(id: string): Promise<Task> {
  const res = await fetch(`${API_URL}/tasks/${id}/complete`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to complete task')
  return res.json()
}

export async function deleteTask(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/tasks/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete task')
}

export async function sendMessage(message: string): Promise<string> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Something went wrong. Please try again.')
  }
  const data = await res.json()
  return data.response
}
