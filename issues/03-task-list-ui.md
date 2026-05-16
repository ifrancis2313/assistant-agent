# Task List UI

**Type:** AFK
**Blocked by:** #2 (Task Service & REST API)
**User stories covered:** 3, 4, 5, 6, 11, 13, 14

## What to build

Build the task panel in the Next.js frontend. This is the right side of the eventual split-panel layout. It shows tasks fetched from the REST API, lets the user switch between the 7 views via a chip navigation row, and provides complete and delete controls on each task card.

No chat panel yet — this slice is just the task panel working in isolation, verifiable by opening the app and seeing tasks load from Supabase.

**Task panel structure:**
- Chip navigation row at the top: horizontal scrollable row of chips — `All | SIC | BC | School | Options | Lab | Personal`. Active chip is visually distinct. Tapping a chip switches the view.
- Task list below: tasks sorted by priority descending, re-fetched when the active chip changes.
- Task card: displays task name, date, priority score, bucket label. Complete checkbox (optimistic update — strikes through immediately, then patches API). Delete button (optimistic remove, then calls DELETE endpoint).

The layout should be mobile-responsive from the start — this panel will take full width on mobile and share width with the chat panel on desktop.

## Acceptance criteria

- [ ] Chip row renders all 7 views (All + 6 buckets), active chip is styled differently
- [ ] Selecting a chip fetches and displays only the matching tasks
- [ ] All view shows tasks from all buckets sorted by priority descending
- [ ] Task card shows: task name, date, priority, bucket
- [ ] Checking the complete checkbox marks the task complete optimistically and calls the API
- [ ] Delete button removes the task optimistically and calls the API
- [ ] Panel is readable and usable on a 390px wide mobile screen
- [ ] Empty state shown when no tasks exist for the selected view

## Blocked by

#2 — Task Service & REST API
