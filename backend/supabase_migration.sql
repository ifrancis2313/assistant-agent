-- Run this in the Supabase SQL editor for your project

-- Phase 1: RLS disabled (single-user, no auth yet)
-- Re-enable with proper policies when auth is added in Phase 2

create table tasks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    task text not null,
    date date not null,
    priority float8 not null check (priority >= 0 and priority <= 10),
    bucket text not null check (bucket in ('SIC','BC','School','Options','Lab','Personal')),
    reminders timestamptz,
    completed boolean not null default false,
    created_at timestamptz not null default now()
);

alter table tasks disable row level security;

create table messages (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    role text not null check (role in ('user','assistant')),
    content text not null,
    created_at timestamptz not null default now()
);

alter table messages disable row level security;
