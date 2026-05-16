# PRD: AI Personal Assistant Agent

## Problem Statement

Managing tasks, deadlines, and ideas across multiple life domains (university clubs, academics, personal projects) is fragmented and cognitively expensive. Current tools don't let you capture a task and brainstorm about it in the same place, and they don't understand your personal context — which club a deadline belongs to, how urgent it actually is, or how to rank competing priorities. The user needs a single assistant they can talk to from their phone that captures tasks from natural language, ranks them intelligently, and lets them brainstorm ideas before committing them to a planner.

## Solution

A mobile-responsive full-stack web application with two tightly integrated panels: a chat interface powered by an AI agent, and a task management panel with seven views. The agent understands the user's personal domain vocabulary (SIC, BC, School, Options, Lab, Personal), captures tasks from conversational input, assigns intelligent priority scores and due dates, and can read and modify the task list on command. Conversation history persists across sessions so brainstorms can be resumed the next day. The agent is built on tool use — not prompt parsing — so it can both write and query the task database mid-conversation.

## User Stories

1. As a user, I want to type a message like "remind me to submit my SIC report by Friday" and have it automatically create a task with the correct bucket, deadline, and priority, so that I don't have to fill out a form.
2. As a user, I want the agent to assign an estimated priority score (0–10) to each task based on deadline proximity and importance, so that I can focus on what matters most without having to rank things manually.
3. As a user, I want to see all my tasks ranked by priority in a single unified view, so that I can quickly see what needs my attention most.
4. As a user, I want to filter tasks by bucket (SIC, BC, School, Options, Lab, Personal) with a single tap, so that I can focus on one area of my life at a time.
5. As a user, I want to mark a task as complete directly from the task card, so that I can check things off without typing a command.
6. As a user, I want to delete a task directly from the task card, so that I can remove irrelevant tasks quickly.
7. As a user, I want to say "reschedule all my School tasks to next week" and have the agent update them, so that I can bulk-manage tasks through natural language.
8. As a user, I want to say "what's my highest priority task today?" and get an accurate answer, so that I can start my day with the right focus.
9. As a user, I want to brainstorm an idea with the agent over multiple messages, then say "turn that into a task", so that ideas don't get lost in chat.
10. As a user, I want the agent to remember what we discussed yesterday when I open the app today, so that I can continue a brainstorm without re-explaining context.
11. As a user, I want to access the app from my phone browser and have it feel native, so that I can capture tasks on the go.
12. As a user, I want the chat panel and task panel to coexist on the same screen, so that I can see my task list update in real time as I talk to the agent.
13. As a user, I want the task panel to use a horizontal chip row (All | SIC | BC | School | Options | Lab | Personal) for view switching, so that navigation is fast and thumb-friendly.
14. As a user, I want tasks to be sorted by priority within each view, so that the most urgent item is always at the top.
15. As a user, I want to say "complete my Options meeting task" and have the agent find and complete it, so that I can manage tasks hands-free.
16. As a user, I want the agent to handle ambiguous input gracefully (e.g., asking a clarifying question if it can't determine the bucket), so that tasks are never mis-categorized silently.
17. As a user, I want the agent to respond conversationally when I ask a general question (not a task), so that it works as a thinking partner and not just a task recorder.
18. As a user, I want task reminder timestamps stored with each task, so that reminder delivery can be wired up later without a schema migration.
19. As a user, I want the app to respond quickly, so that it doesn't interrupt my flow when I'm on the move.
20. As a user, I want each task to store a `user_id` field even though it's single-user today, so that the schema doesn't need to change if the app becomes multi-user.

## Implementation Decisions

### Agent Architecture
- The agent uses Anthropic's tool use API (not prompt-to-JSON parsing). The model decides when to call a tool; the backend executes it against Supabase and returns the result to the model.
- Five core tools: `create_task`, `get_tasks`, `update_task`, `complete_task`, `delete_task`. Each maps to a backend service function.
- Tool interfaces are designed to be extended — `add_calendar_event`, `get_calendar_events`, `read_emails` will be added in later phases without changing the agent loop.
- The official Anthropic Python SDK replaces the current raw `httpx` implementation. Prompt caching is enabled on the system prompt from day one.

### Conversation Memory
- All messages (user and assistant) are persisted to a `messages` table in Supabase.
- The agent receives the last 20 messages as context on each turn (sliding window). Window size is a config constant, tunable without code changes.
- Full history is stored and queryable but only the window is sent to the model, capping token cost at ~$3–5/month at moderate personal use.

### Data Model

**`tasks` table**
- `id` (uuid, primary key)
- `user_id` (uuid, foreign key — nullable for now, populated when auth is added)
- `task` (text)
- `date` (date, yyyy-mm-dd)
- `priority` (float, 0.0–10.0)
- `bucket` (enum: SIC | BC | School | Options | Lab | Personal)
- `reminders` (timestamptz, yyyy-mm-dd HH:MM — stored, not yet delivered)
- `completed` (bool, default false)
- `created_at` (timestamptz, default now())

**`messages` table**
- `id` (uuid, primary key)
- `user_id` (uuid, nullable)
- `role` (enum: user | assistant)
- `content` (text)
- `created_at` (timestamptz, default now())

### Backend Modules (FastAPI)

- **Agent router** — receives user messages, fetches conversation window from Supabase, calls Anthropic SDK with tools, handles the tool-call loop, persists messages, returns final response.
- **Task service** — pure functions for task CRUD against Supabase. No business logic, no AI — just database operations. Called by tool handlers.
- **Message service** — fetches the sliding window and persists new messages. Isolated from agent logic.
- **Tool registry** — maps tool names to handler functions. Adding a new tool is one entry in this registry.
- **Config** — all environment variables and constants (model name, window size, buckets, priority range) in one place.

### Frontend Modules (Next.js)

- **Chat panel** — message thread display, input box, sends messages to FastAPI backend, streams or polls for response.
- **Task panel** — renders the active view (All or a bucket), sorted by priority descending.
- **Chip navigation** — horizontal scrollable row, controls which view is active.
- **Task card** — displays task fields, complete checkbox, delete button. Optimistic UI update on action.
- **API client** — typed fetch wrapper for all backend calls. Single place to update if the API changes.

### AI Model
- Default: `claude-haiku-4-5` — fast, cheap, sufficient for task parsing and short brainstorms.
- Upgrade path: swap to `claude-sonnet-4-6` via config for more complex reasoning. No other code changes required.

### Deployment
- Frontend: Vercel (auto-deploy from GitHub on push to main)
- Backend: Railway (~$5/month, always-on, GitHub integration)
- Database: Supabase (hosted PostgreSQL, free tier)

## Testing Decisions

A good test verifies external behavior — what the module produces given an input — not how it's implemented internally. Tests should not mock Supabase unless testing the agent loop in isolation; task service tests should hit a test schema.

**Modules to test:**

- **Task service** — unit tests for each CRUD operation. Verify correct rows are created, updated, completed, and deleted. Test priority bounds validation and bucket validation.
- **Message service** — verify sliding window returns exactly N most recent messages in chronological order, and that persistence writes both roles correctly.
- **Tool registry** — verify each tool name resolves to the correct handler and that unknown tool names fail gracefully.
- **Validator (existing)** — already partially tested via the existing `test.py` scratch file. Formalize into proper test cases: valid task, valid interactive, missing mode key, invalid bucket, priority out of range, missing response key.
- **Agent router** — integration test: send a message that should trigger `create_task`, verify the task appears in the database and the response is a valid assistant message.

No tests are required for the frontend components in Phase 1 — visual correctness is validated by running the app.

## Out of Scope

- **Authentication / multi-user** — single user only. `user_id` columns are added to the schema for future readiness but no login flow is built.
- **Reminder delivery** — reminder timestamps are stored in the database but no notification system is implemented. Delivery via Google Calendar events is planned for Phase 2.
- **Google Calendar integration** — Phase 2.
- **Canvas LMS integration** — Phase 2.
- **iOS Calendar sync** — Phase 2.
- **Gmail reading** — Phase 3.
- **Task editing via UI** — complete and delete are in scope; inline editing of task fields via the UI is deferred. Editing via chat is in scope.
- **Voice input** — not in scope for Phase 1.
- **Dark mode / theming** — not in scope for Phase 1.

## Further Notes

- The project is a portfolio piece as well as a daily-use tool. Tech choices (Next.js, TypeScript, PostgreSQL) are optimized for employer recognition, not speed of development.
- The six task buckets (SIC, BC, School, Options, Lab, Personal) reflect the user's specific life context and are constants, not user-configurable in Phase 1.
- The existing `bot.py`, `validator.py`, and `constants.py` contain useful domain logic (system prompt, bucket definitions, priority range) that should be migrated into the new backend rather than discarded.
- The system prompt in `constants.py` encodes important business rules (priority scoring rubric, date format, reminder heuristics) that should be preserved and extended in the new agent system prompt.
- Future phases should not require schema migrations if the data model decisions above are followed — `user_id`, `reminders`, and `completed` are included from day one precisely to avoid this.
