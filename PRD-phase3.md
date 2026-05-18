# PRD: Phase 3 — Gmail Sync, Parametrized Sync, and Defaults

## Problem Statement

Even with Google Calendar and Canvas connected, the planner misses a critical source of action items: email. Deadlines, meeting confirmations, requests, and follow-ups land in the inbox and go untracked unless manually re-entered. Additionally, the existing sync tools are inflexible — "sync my calendar" always pulls the same window from all accounts, with no way to target a specific account or adjust the time range without rephrasing the whole command. There's also no way to save preferences, so the user has to re-specify their intent every time.

## Solution

Add Gmail as a third External Source. The agent scans Gmail inboxes on demand, identifies actionable emails, and imports them as Tasks automatically — same Auto-Assignment behavior as Calendar and Canvas. Simultaneously, all sync tools (Gmail, Calendar, Canvas) gain a unified parameter model: optional `accounts` and `days` arguments, with a stored Default Configuration that makes bare commands like "sync my email" work without any additional specification. The user can set defaults once and override them on the fly without changing what's stored.

## User Stories

1. As a user, I want to say "check my email" and have actionable emails automatically become tasks in the planner, so that I don't have to manually re-enter action items from my inbox.
2. As a user, I want the agent to decide which emails are actionable without asking me, so that syncing email is as fast and frictionless as syncing my calendar.
3. As a user, I want email tasks to be deduplicated so that syncing twice doesn't create duplicate tasks from the same email.
4. As a user, I want the agent to auto-assign bucket and priority to email-imported tasks, so that they appear in the right view without any manual categorization.
5. As a user, I want to say "sync email from my USF account" and have it pull only from that account, so that I can target specific inboxes when I need to.
6. As a user, I want to say "sync email from the last 3 days" and have it respect that window, so that I can narrow or widen the pull without changing my stored defaults.
7. As a user, I want to say "sync email from my USF account for the last 30 days" and have both parameters respected simultaneously, so that I can fully control a one-off sync.
8. As a user, I want to set default email accounts and a default day window so that bare "sync my email" commands always do what I expect.
9. As a user, I want to set defaults for calendar sync as well, so that "sync my calendar" pulls from specific accounts for a specific window by default.
10. As a user, I want overriding defaults on a single sync to not change my stored defaults, so that one-off changes don't break my usual workflow.
11. As a user, I want the agent to scan up to 25 emails per account, most recent first, so that syncs are fast and cost-predictable.
12. As a user, I want all my connected Google accounts to have Gmail access, so that I don't need separate authorization flows for Calendar vs Gmail.
13. As a user, I want to re-authorize my existing Google accounts to add Gmail access by visiting the same auth URL, so that the setup is simple.
14. As a user, I want "sync my calendar" to also accept account and day parameters, so that all sync tools work consistently.
15. As a user, I want "sync my canvas" to accept account parameters for future-proofing, so that the tool interface is consistent even if Canvas is currently single-account.
16. As a user, I want my defaults to persist across sessions, so that I don't have to re-configure after closing the app.
17. As a user, I want to see a summary of what was imported after each email sync, so that I know what the agent found and acted on.
18. As a user, I want emails that contain no actionable items to result in a clear "nothing to import" message, so that I know the sync ran successfully.

## Implementation Decisions

### Schema Changes

**New `user_defaults` table:**
- `id` (uuid, primary key, default gen_random_uuid())
- `user_id` (uuid, nullable — reserved for multi-user)
- `sync_type` (text): `gmail` | `google_calendar` | `canvas`
- `accounts` (jsonb): JSON array of email address strings
- `days` (integer): default day window
- `created_at` (timestamptz, default now())
- `updated_at` (timestamptz, default now())
- Unique constraint on `(user_id, sync_type)` — one row per sync type per user
- Upserted on update, never inserted twice

No changes to `user_tokens` — the `gmail_enabled` flag approach was rejected. All Google accounts receive `gmail.readonly` scope at authorization time.

### OAuth Scope Update

`gmail.readonly` is added to the global Google OAuth scopes list alongside the existing Calendar scopes. All future `/auth/google` authorizations request Calendar + Gmail simultaneously. Existing accounts must re-authorize to receive the new scope — this is done by visiting `/auth/google` again. The callback upserts the token row as before; no other changes to the auth flow.

### New: Gmail Service

A deep module. All Gmail API interaction is hidden behind a simple interface:

- `fetch_emails(account_email, days, limit)` → returns list of dicts, each with: `id` (Gmail message ID), `from` (sender), `subject`, `snippet` (first ~150 chars of body). Returns empty list if credentials are missing or invalid. Filters to unread emails within the day window. Most recent first. Limit defaults to 25.

Tested in isolation with mocked Gmail API responses.

### New: Defaults Service

A deep module. All `user_defaults` Supabase interaction:

- `get_defaults(sync_type)` → returns the stored defaults dict for that sync type, or `None` if not set
- `set_defaults(sync_type, accounts, days)` → upserts the defaults row

Tested in isolation with mocked Supabase client, same pattern as token_service tests.

### Modified: sync_google_calendar Tool Handler

Upgraded to accept optional `accounts` (list of emails) and `days_ahead` (integer). Resolution order:
1. Use parameters if provided
2. Fall back to stored Defaults for `google_calendar`
3. Fall back to hardcoded: all connected Google accounts, 14 days

### Modified: sync_canvas Tool Handler

Accepts optional `accounts` parameter for interface consistency. Currently single-account so the parameter is accepted but has no effect on behavior. `days` parameter not applicable to Canvas (Canvas returns upcoming unsubmitted work, not a date-windowed query).

### New: sync_gmail Tool Handler

Accepts optional `accounts` (list of email strings) and `days` (integer). Resolution order:
1. Use parameters if provided
2. Fall back to stored Defaults for `gmail`
3. Fall back to hardcoded: all connected Google accounts, 7 days

For each resolved account, calls `gmail_service.fetch_emails(account, days, limit=25)`. Formats results as a structured list (sender, subject, snippet per email) and returns them to the agent. The agent then calls `create_task` for each email it judges actionable, using the Gmail message ID as `external_id` and `source = "gmail"` for deduplication.

### New: set_defaults Tool Handler

Accepts `sync_type`, `accounts` (list), and `days` (integer). Calls `defaults_service.set_defaults()` and confirms success. Allows updating just accounts or just days — unspecified fields retain their current values.

### System Prompt Update

Three new tools described to the agent: `sync_gmail`, `set_defaults`. `sync_google_calendar` and `sync_canvas` descriptions updated to mention optional account and day parameters.

### Hardcoded Fallbacks

Stored in `config.py`:
- Gmail default: all connected Google accounts, 7 days back
- Calendar default: all connected Google accounts, 14 days forward
- Canvas default: n/a (single account, no window)

## Testing Decisions

A good test verifies observable behavior through the module's public interface — what it returns given an input — not how it's implemented internally. Tests should not assert on internal method calls unless verifying a side effect that has no other observable output.

**Gmail Service** — unit tests with mocked Gmail API client (same pattern as google_calendar_service tests):
- `fetch_emails` returns list with correct fields (id, from, subject, snippet)
- `fetch_emails` returns only unread emails within the day window
- `fetch_emails` respects the limit (returns at most 25)
- `fetch_emails` returns empty list when credentials are missing
- `fetch_emails` returns empty list when no unread emails exist

**Defaults Service** — unit tests with mocked Supabase client (same pattern as token_service tests):
- `get_defaults` returns the stored defaults dict when a row exists
- `get_defaults` returns None when no defaults are set for that sync type
- `set_defaults` upserts a new row when none exists
- `set_defaults` updates the existing row when called again for the same sync type

No tests required for the tool handler upgrades (sync_google_calendar, sync_canvas, sync_gmail, set_defaults) — these are thin wrappers over the deep modules, and the deep modules are already tested.

## Out of Scope

- **Sending emails** — the agent reads Gmail but never sends or replies.
- **Email labels/folders** — sync always targets the primary inbox. Label-based filtering is a future enhancement.
- **Attachment handling** — email attachments are ignored. Only subject and snippet are processed.
- **Scheduled/automatic Gmail sync** — sync is on-demand only. Background polling is a future phase.
- **Gmail push notifications via webhook** — not implemented. On-demand sync covers the use case.
- **Canvas day-window parameter** — Canvas returns upcoming unsubmitted work regardless of date; a day window parameter is not applicable.
- **Settings UI for Defaults** — defaults are set via chat command. A settings page is deferred to the UI cleanup phase.
- **Multi-user** — single user only. `user_id` column in `user_defaults` is nullable and reserved for future use.

## Further Notes

- Re-authorizing existing Google accounts to add `gmail.readonly` is a one-time step. The user visits `/auth/google` for each of the 3 accounts. Existing Calendar functionality is unaffected — re-authorization adds scopes, it does not remove them.
- The agent is the intelligence layer for Gmail — it reads email summaries and decides what's actionable. This is consistent with Phase 2's design where the agent processes tool results and takes action. No secondary Claude call is needed inside the Gmail service itself.
- The `source = "gmail"` + `external_id = <gmail_message_id>` deduplication pattern is identical to how Calendar and Canvas deduplication works. No schema changes needed.
- The parametrized sync upgrade to `sync_google_calendar` is backward-compatible — existing bare "sync my calendar" commands continue to work via the fallback chain.
