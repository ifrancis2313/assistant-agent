# Agent Task Management Tools

**Type:** AFK
**Blocked by:** #4 (Agent Core — Task Capture & Retrieval)
**User stories covered:** 7, 8, 15

## What to build

Extend the agent's tool registry with the three remaining tools: `update_task`, `complete_task`, and `delete_task`. After this slice the agent can manage the full task lifecycle through natural language — not just create and read, but reschedule, complete, and remove tasks on command.

**Tools to add:**
- `update_task(id, **fields)` — updates any subset of task fields (date, priority, bucket, task name). Enables "reschedule all my School tasks to next week" (agent calls get_tasks to find them, then calls update_task for each).
- `complete_task(id)` — sets completed = true
- `delete_task(id)` — removes the task row

The agent uses `get_tasks` (already available from #4) to look up tasks by name or description before calling update/complete/delete. The tool registry is a simple map of tool name → handler function; adding a new tool is one entry.

**Tool registry tests:**
- Each tool name resolves to the correct handler
- Unknown tool names fail gracefully with a clear error (not a 500)
- Calling `complete_task` with a non-existent ID returns a meaningful error to the agent

## Acceptance criteria

- [ ] "Mark my SIC report task as done" completes the correct task in Supabase
- [ ] "Reschedule all my School tasks to next week" updates dates on all matching tasks
- [ ] "Delete my Options meeting task" removes the task from Supabase
- [ ] Agent handles ambiguous references gracefully (asks for clarification rather than acting on the wrong task)
- [ ] Tool registry unit tests: all 5 tools resolve, unknown tool name returns controlled error
- [ ] Task panel in UI reflects changes after agent response (inherits from #5's auto-refresh)

## Blocked by

#4 — Agent Core — Task Capture & Retrieval
