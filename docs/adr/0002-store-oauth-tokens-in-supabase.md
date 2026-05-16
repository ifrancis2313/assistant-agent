# ADR 0002: Store OAuth tokens in Supabase user_tokens table

## Status
Accepted

## Context
Google OAuth produces a refresh token that the backend needs to call the Calendar API. It needs to live somewhere secure and accessible to the backend at runtime.

## Decision
Store all external service credentials in a `user_tokens` Supabase table, not in Railway environment variables. One row per provider per user. The backend fetches and updates tokens from this table on each external API call.

## Alternatives considered
- **Railway env vars**: simple for a single token, but token rotation requires a manual dashboard update and redeploy. Doesn't scale to multi-user. Rejected.
- **Supabase secrets/vault**: more secure but adds complexity. Overkill for Phase 2. Revisit if compliance requirements emerge.

## Consequences
- New table required: `user_tokens` with columns `id`, `user_id`, `provider`, `access_token`, `refresh_token`, `token_expiry`, `created_at`, `updated_at`
- Backend must refresh Google access tokens when expired (access tokens expire after 1 hour; refresh tokens do not expire unless revoked)
- Multi-user migration: add `user_id` FK constraint and uniqueness on `(user_id, provider)`
- Canvas API token (non-OAuth) stored as `access_token` with `refresh_token = null` and `token_expiry = null`
