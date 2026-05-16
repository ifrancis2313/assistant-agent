# Task Service & REST API

**Type:** AFK
**Blocked by:** #1 (Infrastructure & Deployment Shell)
**User stories covered:** 1, 2, 3, 4, 5, 6, 7, 8, 14, 18, 20

## What to build

Implement the task service and expose it as a REST API. This is a pure data layer — no agent, no UI. The task service is a set of functions that perform CRUD against the Supabase `tasks` table. FastAPI routes expose these as HTTP endpoints. Tests verify each operation against a Supabase test schema.

All reads must return tasks sorted by `priority` descending. Bucket filtering is a query parameter on the GET endpoint. The `get_tasks` function is the single source of truth for sorting and filtering — the agent and the UI both use it.

**Endpoints:**
- `POST /tasks` — create a task
- `GET /tasks?bucket=SIC` — list tasks (bucket optional, omit for All view)
- `PATCH /tasks/{id}` — update task fields (any subset)
- `POST /tasks/{id}/complete` — mark completed
- `DELETE /tasks/{id}` — delete

## Acceptance criteria

- [ ] All 5 endpoints return correct data and status codes
- [ ] GET /tasks returns tasks sorted by priority descending
- [ ] GET /tasks?bucket=School returns only School tasks
- [ ] Priority is rejected if outside 0.0–10.0
- [ ] Bucket is rejected if not one of the 6 valid values
- [ ] Task service has unit tests covering all operations
- [ ] Tests run against a Supabase test schema (not production)
- [ ] Invalid task IDs return 404, not 500

## Blocked by

#1 — Infrastructure & Deployment Shell
