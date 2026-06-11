# Meeting Intel Agent

## Setup

### 1. Backend
```bash
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --reload --port 8080
```

### 2. Frontend

**Set your Google OAuth Client ID:**
- Go to https://console.cloud.google.com/apis/credentials
- Create OAuth 2.0 Client ID → Web application
- Add `http://localhost:5173` as Authorized JavaScript origin
- Copy the Client ID into `frontend/.env`:
  ```
  VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
  ```

**Set allowed emails** in `frontend/src/hooks/useAuth.ts` (line 5):
```ts
const ALLOWED_EMAILS = [
  "your.email@gmail.com",
  "colleague@gmail.com",
];
```

**Run:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Features
- Google OAuth login (allowlist of 2 emails)
- Dashboard shows today's + upcoming meetings
- Click any card → opens full intelligence brief in a new tab
- Live WebSocket updates as research completes
