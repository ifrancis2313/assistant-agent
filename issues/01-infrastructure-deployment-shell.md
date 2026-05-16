# Infrastructure & Deployment Shell

**Type:** HITL
**Blocked by:** None — start here

## What to build

Set up the full project skeleton end-to-end so every subsequent slice has a real environment to deploy into. This means: a GitHub repo with a monorepo layout (`frontend/` for Next.js, `backend/` for FastAPI), both apps scaffolded to a working hello-world state, Supabase project created with both tables matching the PRD schema, and all three services wired together via environment variables.

No features — just a deployable skeleton where Vercel serves a placeholder page, Railway responds to a health check, and Supabase has the correct tables.

**Monorepo layout:**
```
/
├── frontend/   ← Next.js + TypeScript + Tailwind
├── backend/    ← FastAPI + Python
├── PRD.md
└── issues/
```

**Supabase tables to create:**

`tasks`: id (uuid pk), user_id (uuid nullable), task (text), date (date), priority (float8), bucket (text, constrained to SIC|BC|School|Options|Lab|Personal), reminders (timestamptz nullable), completed (bool default false), created_at (timestamptz default now())

`messages`: id (uuid pk), user_id (uuid nullable), role (text, constrained to user|assistant), content (text), created_at (timestamptz default now())

## Acceptance criteria

- [ ] GitHub repo exists with `frontend/` and `backend/` directories
- [ ] Next.js app scaffolded with TypeScript and Tailwind, auto-deploys to Vercel on push to main
- [ ] FastAPI app scaffolded, `GET /health` returns `{"status": "ok"}`, deployed on Railway
- [ ] Supabase project created with `tasks` and `messages` tables matching the schema above
- [ ] `.env.example` files exist in both `frontend/` and `backend/` listing all required environment variables
- [ ] README explains how to run both apps locally

## Blocked by

None — can start immediately
