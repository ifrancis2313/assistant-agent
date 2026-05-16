# Agent Core — Task Capture & Retrieval

**Type:** AFK
**Blocked by:** #1 (Infrastructure & Deployment Shell)
**User stories covered:** 1, 2, 8, 9, 10, 16, 17, 19

## What to build

Implement the agent loop using the official Anthropic Python SDK with tool use. This replaces the existing raw `httpx` approach in `bot.py`. The agent receives a user message, fetches the last 20 messages from Supabase as context, calls the model with `create_task` and `get_tasks` tools available, executes any tool calls, and returns the final assistant response. All messages (user and assistant) are persisted to the `messages` table.

The system prompt is migrated directly from `constants.py` and extended to describe the tool use pattern. Prompt caching is enabled on the system prompt from the first call.

**POST /chat endpoint:**
- Request: `{ "message": "remind me to submit my SIC report by Friday" }`
- Response: `{ "response": "Got it — I've added your SIC report..." }`
- Side effect: task row created in Supabase if agent called `create_task`

**Tools available to the agent in this slice:**
- `create_task(task, date, priority, bucket, reminders)` — inserts a row into tasks
- `get_tasks(bucket?)` — reads tasks from Supabase, returns sorted list

**Message service:**
- `fetch_window(n=20)` — returns the last N messages ordered chronologically
- `persist_message(role, content)` — writes a single message to the messages table

The agent loop handles multi-step tool use: the model may call a tool, receive the result, and then produce a final text response — all within a single POST /chat request.

## Acceptance criteria

- [ ] POST /chat with a task-like message creates a task row in Supabase and returns a confirmation
- [ ] POST /chat with a question ("what's my highest priority task?") returns an accurate answer drawn from get_tasks
- [ ] POST /chat with a general question (no task, no query) returns a conversational response
- [ ] Each user message and assistant response is persisted to the messages table
- [ ] Subsequent requests include the last 20 messages as context (agent remembers prior turns)
- [ ] Prompt caching header is set on the system prompt
- [ ] Message service unit tests: window returns exactly N messages in order, both roles persist correctly
- [ ] Agent integration test: send a task message, verify task row exists in test DB

## Blocked by

#1 — Infrastructure & Deployment Shell
