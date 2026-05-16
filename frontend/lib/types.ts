export interface Task {
  id: string
  user_id: string | null
  task: string
  date: string
  priority: number
  bucket: string
  reminders: string | null
  completed: boolean
  created_at: string
}

export const BUCKETS = ['SIC', 'BC', 'School', 'Options', 'Lab', 'Personal'] as const
export type Bucket = typeof BUCKETS[number]
export type View = 'All' | Bucket
