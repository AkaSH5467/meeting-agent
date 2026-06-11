# Meeting Intelligence Agent

An autonomous agent that monitors your Google Calendar, researches the companies behind your upcoming meetings, and delivers a ready-to-use intelligence brief — before the meeting starts.

---

## What It Does

1. **Calendar Listener** — polls Google Calendar every 60 seconds for upcoming meetings
2. **Company Extraction** — infers company from meeting title (priority), then attendee emails, then description
3. **Research Pipeline** — runs three parallel AI agents (news, tech, pain points) and synthesises into a structured brief
4. **Live Dashboard** — shows all upcoming meetings as clean cards; click any card to open the full brief in a new tab

---

## Architecture

```
Google Calendar API
       │
       ▼
 Calendar Listener (polls every 60s)
       │
       ▼
 Parser (extract company from title → email → description)
       │
  ┌────┴─────────────────────────┐
  │                              │
  ▼                              ▼
Company found               No company found
  │                              │
  ▼                              ▼
Research Pipeline          Saved as no_company
  │                         (graceful fallback)
  ├── News Agent    (Serper — Google Search)
  ├── Tech Agent    (Exa — semantic search)
  └── Pain Point Agent (Serper — job listings)
       │
       ▼
  Synthesis Agent (Gemini 2.5 Flash)
       │
       ▼
  Brief saved to Cloud SQL (PostgreSQL)
       │
       ▼
  WebSocket broadcast → React Dashboard
```

**Stack:**
- Backend: FastAPI + Python 3.11, Google ADK (Agent Development Kit), Gemini 2.5 Flash
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Database: PostgreSQL (Google Cloud SQL)
- External APIs: Google Calendar, Serper.dev (news/web search), Exa (semantic company research)

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Cloud project with Calendar API enabled

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/meeting-intel.git
cd meeting-intel
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
# Gemini
GOOGLE_API_KEY=your_gemini_api_key

# Google OAuth (for Calendar access)
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token

# Research APIs
SERPER_API_KEY=your_serper_api_key
EXA_API_KEY=your_exa_api_key

# Database (PostgreSQL)
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASS=your_db_password
DB_NAME=meeting_intel
```

Run the backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_GOOGLE_CLIENT_ID=your_oauth_web_client_id
```

Run the frontend:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Getting Credentials

### Google OAuth Refresh Token (for Calendar access)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop app type)
3. Download the JSON, then run:

```bash
pip install google-auth-oauthlib
python - << 'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/calendar.readonly']
)
creds = flow.run_local_server(port=0)
print("REFRESH TOKEN:", creds.refresh_token)
EOF
```

### Serper API Key
Sign up at [serper.dev](https://serper.dev) — free tier includes 2,500 searches/month.

### Exa API Key
Sign up at [exa.ai](https://exa.ai) — free tier available.

---

## Deployment

### Backend → Google Cloud Run

```bash
cd backend

# Build image on Google's servers (no Docker needed locally)
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/meeting-intel-backend

# Deploy
gcloud run deploy meeting-intel-backend \
  --image gcr.io/YOUR_PROJECT_ID/meeting-intel-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT:REGION:INSTANCE \
  --set-env-vars CLOUD_SQL_UNIX_SOCKET=1 \
  --set-env-vars DB_USER=postgres \
  --set-env-vars DB_PASS=your_db_password \
  --set-env-vars DB_NAME=meeting_intel \
  --set-env-vars CLOUD_SQL_INSTANCE=YOUR_PROJECT:REGION:INSTANCE \
  --set-env-vars GOOGLE_API_KEY=your_gemini_key \
  --set-env-vars GOOGLE_CLIENT_ID=your_client_id \
  --set-env-vars GOOGLE_CLIENT_SECRET=your_client_secret \
  --set-env-vars "GOOGLE_REFRESH_TOKEN=your_refresh_token" \
  --set-env-vars SERPER_API_KEY=your_serper_key \
  --set-env-vars EXA_API_KEY=your_exa_key \
  --port 8000 \
  --min-instances 1
```

> `--min-instances 1` is required — prevents Cloud Run from scaling to zero, which would kill the calendar polling loop.

After deploy, update the frontend API URLs to point at your Cloud Run URL (`https://...run.app`), and change `ws://` to `wss://`.

### Frontend → Vercel

```bash
cd frontend
vercel --prod
```

Or connect the GitHub repo at [vercel.com](https://vercel.com) and set:
```
VITE_GOOGLE_CLIENT_ID = your_oauth_web_client_id
```

Then add your Vercel URL as an **Authorized JavaScript Origin** in Google Cloud Console → APIs & Services → Credentials.

---

## Environment Variables Reference

### Backend

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key (from Google AI Studio) |
| `GOOGLE_CLIENT_ID` | OAuth client ID (Desktop app) for Calendar |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret for Calendar |
| `GOOGLE_REFRESH_TOKEN` | Long-lived token for Calendar access |
| `SERPER_API_KEY` | Serper.dev API key (web/news search) |
| `EXA_API_KEY` | Exa API key (semantic company research) |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port (default: 5432) |
| `DB_USER` | Database user |
| `DB_PASS` | Database password |
| `DB_NAME` | Database name |
| `CLOUD_SQL_INSTANCE` | Cloud SQL instance (project:region:instance) — Cloud Run only |
| `CLOUD_SQL_UNIX_SOCKET` | Set to `1` on Cloud Run to use unix socket |

### Frontend

| Variable | Description |
|---|---|
| `VITE_GOOGLE_CLIENT_ID` | OAuth client ID (Web app) for Google Sign-In |

---

## Access Control

Dashboard login is restricted to an allowlist of Google accounts. To add or remove users, edit `frontend/src/hooks/useAuth.ts`:

```ts
const ALLOWED_EMAILS = [
  "you@gmail.com",
  "colleague@company.com",
];
```

---

## Key Design Decisions

**Title-first company extraction** — the parser checks the meeting title before attendee emails. A meeting titled "AT&T - Marketing Catchup" with Google employees as attendees researches AT&T, not Google. Known brands with special characters (AT&T, T-Mobile, IBM) are matched with a hardcoded lookup before regex runs.

**Multi-agent research with Google ADK** — three specialist sub-agents (news, tech, pain points) run in parallel via Gemini function calling, then pass results to a synthesis agent. This produces more focused, higher-quality output than a single large prompt.

**WebSocket-driven updates** — the dashboard receives real-time status updates (pending → done) via WebSocket rather than polling, so brief cards update the moment research completes.

**18-hour meeting expiry** — meetings are automatically hidden from the dashboard 18 hours after their start time to keep the view clean.

**Graceful fallback** — personal emails (gmail, yahoo, etc.) and generic vendor domains (google.com, microsoft.com) don't trigger research unless no company is found in the title. Unresolvable meetings show a clear "Company could not be identified" state.
