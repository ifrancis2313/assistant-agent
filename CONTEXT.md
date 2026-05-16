# Domain Glossary

## Task
A user-defined or imported action item. Has a priority (0–10), bucket, due date, and optional reminder timestamp. The atomic unit of the planner. Tasks can be created manually via chat, or imported from an external source. All tasks live in the `tasks` Supabase table.

## Event
A future concept (Phase 3+). A time-bound occurrence with a specific start/end time, location, and optional attendees — distinct from a Task, which is open-ended and priority-ranked. Not yet implemented. When introduced, the UI will show a combined Task + Event interface with a reminder/ping system.

## Planner
The central interface and source of truth. Everything flows INTO the planner — external sources (Google Calendar, Canvas) are read sources that feed the planner, not sync targets. The planner is not a replica of Google Calendar; it is the user's single actionable view of their life.

## External Source
Any system outside the planner whose data is imported as Tasks: Google Calendar, Canvas LMS, iOS Calendar (via Google). Data flows one direction: External Source → Planner. The planner does not push data back to external sources (except writing Calendar events for reminder delivery, which is a notification mechanism, not a sync).

## Bucket
One of six fixed categories for tasks: SIC (Student Investment Club), BC (Brother Connections), School (academics/homework), Options (Options and Futures Club), Lab (Investment Lab/Silk Analyst), Personal (catch-all). Buckets are constants, not user-configurable in Phase 1 or 2.

## Source
Where a task originated. One of: `manual` (created via chat), `google_calendar` (imported from Google Calendar), `canvas` (imported from Canvas LMS). Stored on every task to enable deduplication and to show the user where a task came from.

## External ID
The identifier of a task's corresponding entity in its external source — e.g., the Google Calendar event ID or the Canvas assignment ID. Used for deduplication: before importing, the system checks whether a task with the same source + external_id already exists.

## Auto-Assignment
The agent always assigns bucket and priority automatically — for manually created tasks, imported Calendar events, and Canvas assignments alike. The agent never asks the user to confirm or clarify a bucket or priority. If the assignment is wrong, the user corrects it in a follow-up message. This applies retroactively to Phase 1 task creation.

## Canvas Sync
On-demand import of Canvas LMS assignments as Tasks. Uses a personal Canvas API token (no OAuth). Assignments are imported with `source = "canvas"` and `external_id = <canvas_assignment_id>`. Bucket defaults to `School`. Deduplication via source + external_id.

## Conversation Window
The last 20 messages sent to the agent as context on each turn. Full history is persisted in Supabase but only the window is sent to the model to cap token cost.
