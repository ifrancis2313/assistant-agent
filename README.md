# Assistant Agent

AI-powered personal assistant with task management and conversational brainstorming. Built with Next.js, FastAPI, Supabase, and Claude.

## Stack

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS → Vercel
- **Backend**: FastAPI (Python) + Anthropic SDK → Railway
- **Database**: Supabase (PostgreSQL)
- **AI**: Claude Haiku 4.5

## Local Development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. Health check: `GET /health`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # fill in NEXT_PUBLIC_API_URL
npm run dev
```

Frontend runs at http://localhost:3000.

### Database

Run `backend/supabase_migration.sql` in the Supabase SQL editor to create the `tasks` and `messages` tables.

## Project Structure

```
/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── supabase_migration.sql
├── issues/            # Issue definitions
└── PRD.md
```

## Deployment

- **Frontend**: Import repo in Vercel, set root directory to `frontend`. Add env var: `NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app`
- **Backend**: Create Railway service from repo, set root directory to `backend`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add env vars from `backend/.env.example`.
- **Database**: Supabase free tier. Run `backend/supabase_migration.sql` in the SQL editor.
