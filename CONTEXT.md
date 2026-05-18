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

## Token Setup
The process of providing external service credentials to the planner. Phase 2: done via chat command ("set my Canvas token to..."), which stores the token in the `user_tokens` table. Future UI cleanup phase: a dedicated settings page replaces the chat command without changing the storage layer.

## User Tokens
A Supabase table (`user_tokens`) that stores credentials for external services. Columns: `id`, `user_id` (nullable for now), `provider` (text: "google" | "canvas"), `account_email` (text, the Google account email or Canvas institution URL — identifies which account within a provider), `access_token`, `refresh_token` (null for non-OAuth providers like Canvas), `token_expiry` (null for non-expiring tokens), `created_at`, `updated_at`. One row per (provider, account_email) — supports multiple Google accounts. Uniqueness constraint on (provider, account_email).

## Auto-Assignment
The agent always assigns bucket and priority automatically — for manually created tasks, imported Calendar events, and Canvas assignments alike. The agent never asks the user to confirm or clarify a bucket or priority. If the assignment is wrong, the user corrects it in a follow-up message. This applies retroactively to Phase 1 task creation.

## iOS Calendar
Not a separate integration. iOS Calendar events sync bidirectionally with Google Calendar natively (via iOS Settings → Calendar → Accounts). Covered entirely by Google Calendar Sync. iOS push notifications for reminders are delivered automatically: backend creates a Google Calendar event with a popup reminder → Google syncs to iPhone → iOS fires the notification natively.

## Reminder Delivery
Automatic. When a task is created with a `reminders` timestamp AND Google Calendar is authenticated, the backend immediately creates a corresponding Google Calendar event with a popup notification at the reminder time. Google's sync delivers the notification to iOS. If Google is not authenticated, the reminder timestamp is stored in Supabase but not delivered (same behavior as Phase 1).

## Google Calendar Sync
On-demand import of Google Calendar events as Tasks across ALL connected Google accounts simultaneously. Uses OAuth 2.0 with scopes `calendar.readonly` + `calendar.events` (read + write). Multiple Google accounts are supported — each stored as a separate row in `user_tokens` keyed by (provider="google", account_email). Sync fetches events from every connected account and merges results. Events imported with `source = "google_calendar"` and `external_id = <google_event_id>`. Deduplication via source + external_id prevents duplicates across syncs and across accounts. Default sync window: next 14 days. Agent interprets explicit time ranges when specified.

## Canvas Sync
On-demand import of Canvas LMS assignments as Tasks. Uses a personal Canvas API token (no OAuth). Institution URL: `https://usfca.instructure.com`. Imports unsubmitted assignments only (submitted = done, no value in the planner). Fields imported: assignment name, due date, course name. Bucket always `School`. Priority auto-assigned based on due date proximity. Deduplication via `source = "canvas"` + `external_id = <canvas_assignment_id>`.

## Gmail Sync
On-demand import of actionable emails as Tasks. The agent scans specified Gmail inboxes (up to 25 emails per account, most recent first), extracts action items and deadlines, and creates tasks automatically. Auto-assignment rules apply. Deduplication via `source = "gmail"` + `external_id = <gmail_message_id>`. All connected Google accounts are authorized for Gmail access (same OAuth flow as Calendar, with `gmail.readonly` scope added). Sync accepts optional Sync Parameters; when omitted, stored Defaults are used. The agent receives each email as: sender, subject, and a short snippet, then decides which are actionable.

## Sync Parameters
The optional arguments accepted by any sync tool: `accounts` (list of email addresses to include) and `days` (how far back to look for email, or how far forward for calendar). When not provided, the tool falls back to the user's stored Defaults, or if no Defaults are set, to the hardcoded fallback: all connected accounts, 7 days back for Gmail, 14 days forward for Calendar.

## Defaults
Stored user preferences for sync tools. Lives in a `user_defaults` Supabase table with one row per sync type (`gmail`, `google_calendar`, `canvas`), columns: `sync_type`, `accounts` (JSON array of email strings), `days` (integer). Set via chat ("make ifrancis2313 and ifrancis@dons my default email accounts, 7 days"). Override on the fly without changing the stored Default ("sync email from my USF account for the last 30 days"). A `set_defaults` agent tool handles updates.

## Conversation Window
The last 20 messages sent to the agent as context on each turn. Full history is persisted in Supabase but only the window is sent to the model to cap token cost.
