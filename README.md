# Help Finder

A Discord bot + dashboard that matches stuck cohort builders with the right peer, based on tech stack automatically analyzed from public GitHub repos.

## What it does

- Ingests all cohort submission repos from the [cursor-boston submissions](https://github.com/rogerSuperBuilderAlpha/cursor-boston/tree/c1w1pm-submission/content/summer-cohort/c1/w1-pm/submissions)
- Analyzes each repo for languages, frameworks, and activity via GitHub API
- Summarizes projects using Groq (free tier) or falls back to README parsing
- Exposes a searchable dashboard: "who else is building with Next.js + Supabase?"
- Discord slash command: `/help [topic]` → top 3 matched cohort members

## Why

Discord doesn't know who knows what. Help Finder does.

## Stack

- **Backend (Ori):** Python, GitHub API, Groq API (free), `rapidfuzz`, SQLite
- **Frontend (Johnny):** Next.js, Tailwind, Shadcn, Vercel

## Getting started

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # add GITHUB_TOKEN and optionally GROQ_API_KEY
python ingest.py

# Frontend
cd frontend
npm install
npm run dev
```

## Tickets

See [TICKETS.md](./TICKETS.md) for the full task breakdown and merge schedule.
