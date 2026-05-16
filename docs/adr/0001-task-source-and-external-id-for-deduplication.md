# ADR 0001: Store source and external_id on tasks for deduplication

## Status
Accepted

## Context
The planner imports tasks from external sources (Google Calendar, Canvas LMS). Without a way to identify whether an event has already been imported, every sync creates duplicates with no programmatic cleanup path.

## Decision
Add two nullable columns to the `tasks` table:
- `source` (text): `manual` | `google_calendar` | `canvas`
- `external_id` (text): the ID of the corresponding entity in the external system

Before importing, the sync tool checks for an existing task with the same `source` + `external_id`. If found, skip. If not, create.

Manually-created tasks have `source = "manual"` and `external_id = null`.

## Alternatives considered
- **No deduplication**: simple, but syncing twice creates duplicate tasks with no cleanup path. Rejected.
- **Deduplication by task name + date**: fragile — event names change, dates shift. Rejected.

## Consequences
- Schema change required: `ALTER TABLE tasks ADD COLUMN source text DEFAULT 'manual', ADD COLUMN external_id text;`
- All existing tasks implicitly have `source = "manual"` (handled by the DEFAULT)
- When auth is added for multi-user, `external_id` uniqueness must be scoped to `user_id + source + external_id`
