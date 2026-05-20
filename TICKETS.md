# Help Finder — Hackathon Tickets

A Discord bot + dashboard that matches stuck cohort builders with the right peer based on tech stack, analyzed from public GitHub data.

**Cohort:** Cursor Boston Summer Cohort C1
**Source data:** [cohort submissions repo](https://github.com/rogerSuperBuilderAlpha/cursor-boston/tree/c1w1pm-submission/content/summer-cohort/c1/w1-pm/submissions) — 17 JSON files, each with `githubHandle`, `name`, `repoUrl`, `liveUrl`, `pitch`.

---

## Timeline — 3 days, 2 people

Branches:

- `feature/backend` — Ari
- `feature/frontend` — Johnny

Merge schedule:

- **End of Day 1:** schema-only merge — both agree on the `participants.json` shape
- **End of Day 2:** integration merge — frontend swaps mock data for real
- **Day 3:** polish on `main`, deploy, record demo

---

## Shared Data Schema (lock this Day 1)

```json
{
  "githubHandle": "bme3412",
  "name": "Brendan Erhard",
  "avatarUrl": "https://...",
  "repoUrl": "https://github.com/bme3412/boston-cursor-week-1",
  "liveUrl": "https://...",
  "pitch": "Launchpad — a cohort feed for builders to share progress.",
  "summary": "Next.js feed showing PRs and ship updates with auth.",
  "techStack": ["Next.js", "React", "TypeScript", "Tailwind", "Shadcn"],
  "languages": { "TypeScript": 199886, "CSS": 4368 },
  "lastCommitAt": "2026-05-19T14:30:00Z",
  "commitsLast7d": 23,
  "repoPrivate": false
}
```

---

## Ori — Backend / Data Pipeline + Discord Bot

Branch: `feature/backend`

### A1 — Scaffolding & schema

- Choose language (Python recommended for fast API + LLM work)
- Define `Participant` dataclass matching the schema above
- Create `data/participants.sample.json` with 3 mock entries — this unblocks Johnny
- **DoD:** sample file committed, schema documented in README

### A2 — Submission scraper

- Fetch all 17 submission JSONs from the cohort repo via GitHub API
- Parse into `Participant` objects with base fields (`githubHandle`, `name`, `repoUrl`, `pitch`, etc.)
- Handle missing optional fields (`liveUrl`, `loomUrl` can be empty/placeholder)
- **DoD:** `python scrape_submissions.py` outputs 17 participant stubs

### A3 — GitHub repo analyzer

- For each `repoUrl`: call `/repos/{owner}/{repo}/languages`
- Parse `package.json`, `requirements.txt`, `pyproject.toml` for specific frameworks
- Normalize tech tags (e.g. `@types/react` → `React`, `next` → `Next.js`)
- Skip private/404 repos gracefully → set `repoPrivate: true`
- **DoD:** every public participant has a non-empty `techStack` array

### A4 — README summarizer (free LLM)

- Fetch `README.md` from each repo
- Summarize using Groq free tier (see free LLM options below) → 1-line `summary`
- Fallback: extract first non-empty paragraph from README if no API key set
- Cache by repo SHA so we don't re-summarize unchanged READMEs
- **DoD:** every public participant has a `summary` field

### A5 — Commit activity tracker

- Fetch recent commits via `/repos/{owner}/{repo}/commits?since=...`
- Set `lastCommitAt` and `commitsLast7d`
- **DoD:** activity fields populated and refresh-safe

### A6 — Data store + refresh script

- One command: `python ingest.py` runs A2 → A5 end-to-end
- Output: `data/participants.json` (single source of truth)
- Optional: cron / scheduled refresh
- **DoD:** running ingest produces a complete `participants.json` for all 17 cohort members

### A7 — Discord bot

- Slash command `/help [topic]`
- Tier 1 (no cost): keyword + fuzzy match against `techStack` tags using `rapidfuzz`
- Tier 2 (if time): natural language via Groq free tier — parse intent then fuzzy-match
- Reply with top 3 matches: name, handle, tech stack, "active Xh ago", dashboard link
- **DoD:** bot works in a test Discord server

---

## Johnny — Dashboard UI

Branch: `feature/frontend`

### B1 — Next.js app setup

- Bootstrap Next.js + Tailwind + Shadcn
- Read from `data/participants.sample.json` (swap for real `participants.json` on Day 2)
- Vercel-ready from day one
- **DoD:** dashboard renders against sample data

### B2 — Participant card component

- Avatar, name, GitHub handle
- Pitch + Claude-generated summary
- Tech stack tags (clickable → filter)
- Last activity badge ("Active 2h ago")
- Links to repo, live URL
- **DoD:** card renders all fields, looks clean

### B3 — Dashboard list view

- Grid of participant cards
- Sort: by activity (default) / alphabetical
- Loading + empty states
- **DoD:** all 17 cards visible, sortable

### B4 — Search & filter

- Free-text search across name, pitch, summary
- Click a tag → filter to everyone with that tag
- Prominent header search: "Find help with [X]"
- **DoD:** "react" finds everyone using React; clearing search resets

### B5 — Stack overlap ("people like you")

- Dropdown: "I am [participant]"
- Show "X others share Y% of your stack"
- Sort matches by overlap descending
- **DoD:** selecting yourself surfaces nearest neighbors

### B6 — Polish + deploy

- Deploy to Vercel
- Mobile-responsive
- Error states for missing fields
- **DoD:** live URL works on phone + desktop

---

## Merge Checkpoints

**Day 1 EOD**

- Both push to their feature branches
- Merge `data/participants.sample.json` + schema docs into `main`
- Both rebase on updated `main`

**Day 2 EOD**

- Ori merges `feature/backend` → `main`
- Johnny pulls `main`, swaps sample for real data, fixes any drift
- Johnny merges `feature/frontend` → `main`

**Day 3**

- Work on `main` directly with small commits
- Final polish, Vercel deploy, demo recording

---

## Free LLM Options (no paid API needed)

### Option 1 — Groq (recommended)

- Sign up at groq.com — free tier, no credit card
- 14,400 requests/day on Llama 3.1 8B, very fast inference
- `pip install groq` → drop-in for OpenAI SDK style calls
- Best for: README summarization + natural language bot queries

### Option 2 — Google Gemini Flash

- Free tier: 15 RPM, 1M tokens/day
- `pip install google-generativeai`
- Best for: summarization if Groq rate limits hit

### Option 3 — No LLM (zero dependency fallback)

- Summarization: take first non-empty paragraph from README (already in A4)
- Bot matching: `rapidfuzz` fuzzy match on `techStack` tags covers 90% of queries
- This alone is demo-worthy — the structure of the data does the heavy lifting

**Recommendation for hackathon:** Build with the no-LLM fallback first so it always works. Add Groq on top if time permits for the NLP bot queries.

---

## Demo Script (for Day 3)

1. Open dashboard — 17 real cohort members already populated, no signup needed
2. Show stack overlap — "I'm building with Next.js, here are the 4 closest peers"
3. Switch to Discord — type `/help streamlit` → bot surfaces Alaska Lam
4. Click through to her repo from the dashboard
5. Closing line: "Discord is great for chat, but it doesn't know who knows what. Help Finder does."
