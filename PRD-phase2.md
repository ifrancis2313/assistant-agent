# PRD: Phase 2 — External Source Integrations

## Problem Statement

The planner requires manual task entry for everything — classes, meetings, and deadlines that already exist in Google Calendar and Canvas go unseen unless the user re-enters them by hand. This defeats the purpose of a unified planner. Deadlines get missed not because the user forgot to act, but because they forgot to import them. There is also no reminder delivery — the `reminders` field on every task stores a timestamp that is never acted on.

## Solution

Connect the planner to the user's two primary external sources: Google Calendar (covering all calendar events including iOS Calendar via native sync) and Canvas LMS (covering academic assignments). Both are imported on-demand via chat as Tasks, with deduplication preventing duplicates across syncs. When a task has a reminder timestamp and Google Calendar is authenticated, the backend automatically creates a Google Calendar event with a popup notification — which Google syncs to iOS, delivering a native push notification. The planner becomes the single actionable view of the user's life without requiring any manual re-entry.

## User Stories

1. As a user, I want to say "sync my calendar" and have my upcoming Google Calendar events appear as tasks in the planner, so that I don't have to manually re-enter events I've already scheduled.
2. As a user, I want the agent to auto-assign a bucket and priority to every imported event, so that I don't have to categorize things manually.
3. As a user, I want the sync to default to the next 14 days, so that I see what's immediately relevant without being overwhelmed by distant events.
4. As a user, I want to specify a time range ("sync this week", "sync next month"), so that I can control how far ahead the import looks.
5. As a user, I want duplicate events to be skipped on re-sync, so that syncing twice doesn't fill my planner with duplicate tasks.
6. As a user, I want to say "sync my Canvas" and have my unsubmitted assignments appear as tasks, so that academic deadlines are captured automatically.
7. As a user, I want only unsubmitted Canvas assignments to be imported, so that already-submitted work doesn't clutter the planner.
8. As a user, I want Canvas assignments to always be placed in the School bucket, so that academic work is consistently categorized.
9. As a user, I want to provide my Canvas API token via chat ("set my Canvas token to..."), so that I can connect Canvas without navigating to a settings page.
10. As a user, I want to authorize Google Calendar access once via a URL, so that subsequent syncs happen silently without re-authorization.
11. As a user, I want reminder timestamps on tasks to automatically create Google Calendar events with popup notifications, so that I receive iOS push notifications at the right time without any extra steps.
12. As a user, I want reminder delivery to work only when Google Calendar is connected, so that the system degrades gracefully if I haven't authenticated.
13. As a user, I want to see a confirmation message after syncing that summarizes what was imported, so that I know what the agent found and added.
14. As a user, I want imported tasks to behave identically to manually-created tasks (complete, delete, update via chat), so that there's no difference in how I manage them.
15. As a user, I want the agent to tell me if no new events were found during a sync, so that I know the sync ran and simply had nothing new to import.
16. As a user, I want the course name included in the task description for Canvas assignments, so that I know which class the assignment belongs to without checking Canvas.
17. As a user, I want tasks imported from Google Calendar to be attributed to their source, so that I can tell which tasks came from my calendar vs. manual entry.
18. As a user, I want the Google OAuth flow to request both read and write permissions upfront, so that reminder delivery works without requiring re-authorization later.

## Implementation Decisions

### Schema Changes

**`tasks` table — add two columns:**
- `source` (text, default `'manual'`): one of `manual | google_calendar | canvas`. All existing tasks implicitly have `source = 'manual'` via the DEFAULT. Never null.
- `external_id` (text, nullable): the Google Calendar event ID or Canvas assignment ID. Null for manually-created tasks.

Deduplication query before any import: check for existing task with matching `source` + `external_id`. If found, skip.

**New `user_tokens` table:**
- `id` (uuid, primary key, default gen_random_uuid())
- `user_id` (uuid, nullable — reserved for future multi-user)
- `provider` (text): `google` | `canvas`
- `access_token` (text)
- `refresh_token` (text, nullable — null for Canvas which uses a static token)
- `token_expiry` (timestamptz, nullable — null for Canvas)
- `created_at` (timestamptz, default now())
- `updated_at` (timestamptz, default now())

One row per provider. Upserted (not inserted) on token setup or refresh, so re-authorizing replaces the existing row.

### New Backend Modules

**Token Service** — read/write credentials from `user_tokens`. Interface: `get_token(provider)`, `upsert_token(provider, access_token, refresh_token, token_expiry)`. Called by both Google Calendar and Canvas services. No business logic — pure Supabase CRUD.

**Google Calendar Service** — all Google Calendar API interaction. Interface:
- `get_auth_url()` → authorization URL to redirect user to
- `exchange_code(code)` → exchanges OAuth code for tokens, stores via token service
- `refresh_access_token()` → refreshes expired access token, updates via token service
- `fetch_events(days_ahead)` → returns list of calendar events for the next N days
- `create_reminder_event(task_name, reminder_datetime)` → creates a Google Calendar event with a popup notification

Access token refresh is handled internally — callers never manage token state.

**Canvas Service** — all Canvas LMS API interaction. Institution URL hardcoded to `https://usfca.instructure.com`. Interface:
- `fetch_unsubmitted_assignments()` → returns list of unsubmitted assignments across all active courses, including assignment name, due date, course name, and Canvas assignment ID

### Modified Modules

**Task Service** — `TaskCreate` and `Task` models gain optional `source` (default `"manual"`) and `external_id` (nullable) fields. `get_tasks()` and `create_task()` pass these fields through to Supabase transparently.

**Tool Registry (`chat.py`)** — three new agent tools added:
- `sync_google_calendar(days_ahead?)` — calls Google Calendar service, deduplicates, batch-creates new tasks, returns import summary
- `sync_canvas()` — calls Canvas service, deduplicates, batch-creates new tasks, returns import summary
- `set_canvas_token(token)` — stores token via token service, confirms success

System prompt updated to describe the three new tools and their trigger conditions.

**Reminder Delivery** — `create_task()` gains a side-effect: if the task has a `reminders` timestamp AND Google Calendar is authenticated (token exists in `user_tokens`), it calls `google_calendar_service.create_reminder_event()` immediately after creating the task. Failure to create the calendar event is logged but does not fail the task creation.

### New Auth Routes

- `GET /auth/google` — generates Google OAuth URL and redirects the user's browser to it. Scopes: `calendar.readonly` + `calendar.events`.
- `GET /auth/google/callback` — receives the authorization code from Google, calls `google_calendar_service.exchange_code(code)`, stores tokens, returns a success page.

These routes are thin wrappers — all logic lives in Google Calendar Service.

### Google OAuth Configuration

A Google Cloud project must be created with the Calendar API enabled. Authorized redirect URI registered as `https://assistant-agent-production.up.railway.app/auth/google/callback`. Client ID and Client Secret stored as Railway environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

### Agent Behavior

The agent auto-assigns bucket and priority for all imported tasks — no confirmation step, no clarifying questions. Canvas assignments always receive bucket `School`. Google Calendar events receive a bucket inferred from the event title and description using the same bucket inference rules as manual task creation. Priority is assigned based on due date proximity using the standard 0–10 scale.

## Testing Decisions

A good test verifies observable behavior through the module's public interface — what it produces given an input — not how it's implemented internally. Tests should not assert on internal method calls or private state.

**Token Service** — unit tests: `get_token` returns the correct token for a given provider; returns `None` when no token exists; `upsert_token` creates a new row when none exists and updates the existing row on second call. Tests mock the Supabase client (same pattern as existing message service tests).

**Google Calendar Service** — unit tests mock the Google API client (same pattern as existing chat router tests mock the Anthropic client):
- `fetch_events(14)` returns a list of event dicts with the correct fields
- `fetch_events` skips all-day events with no actionable time (if applicable)
- `create_reminder_event` calls the Calendar API with the correct event payload including a popup reminder
- `refresh_access_token` updates the stored token via token service when called
- `get_auth_url` returns a URL containing the correct scopes

**Canvas Service** — unit tests mock the Canvas HTTP responses:
- `fetch_unsubmitted_assignments` returns only assignments where submission status is not submitted
- `fetch_unsubmitted_assignments` includes assignment name, due date, and course name in each result
- `fetch_unsubmitted_assignments` returns an empty list gracefully when all assignments are submitted

Prior art: existing tests in `test_message_service.py` (mocking Supabase), `test_chat_router.py` (mocking Anthropic SDK).

## Out of Scope

- **Settings UI** — token setup via chat command only. A settings page is a future UI cleanup phase.
- **Scheduled/automatic sync** — sync is on-demand via chat. Background cron jobs are Phase 3.
- **Gmail integration** — Phase 3.
- **Writing tasks back to Google Calendar** — the planner does not push tasks to Calendar. The only write to Calendar is reminder event creation, which is a notification mechanism, not a sync.
- **Multi-user OAuth** — single user only. `user_id` column exists in `user_tokens` for future readiness but no multi-user flows are built.
- **iOS Calendar as a separate integration** — covered entirely by Google Calendar sync via native iOS ↔ Google bidirectional sync.
- **Canvas announcements, quizzes, discussions** — assignments only.
- **Event type** — calendar events are imported as Tasks. A dedicated Event type with combined Task+Event UI and full reminder system is a future phase.

## Further Notes

- The one-time Google OAuth flow requires the user to visit `/auth/google` in a browser once. After that, all Calendar API calls are silent. The refresh token does not expire unless manually revoked.
- Canvas personal access tokens do not expire by default but can be revoked in Canvas Settings → Approved Integrations.
- The `usfca.instructure.com` Canvas URL is hardcoded for Phase 2. When multi-user is introduced, this becomes a per-user setting stored alongside the token.
- Reminder delivery failure (e.g., Google Calendar API down) must not fail task creation. Log the error, create the task, move on.
- The Google Cloud project must have the Calendar API enabled and the OAuth consent screen configured before the `/auth/google` route will work.
- All three new agent tools (`sync_google_calendar`, `sync_canvas`, `set_canvas_token`) extend the existing tool registry pattern in `chat.py` — adding a tool is one entry in the registry plus a handler function.
