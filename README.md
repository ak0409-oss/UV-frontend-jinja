# UniVoice – Jinja2 / Flask Frontend

A **Flask + Jinja2** port of the UniVoice hostel grievance management system,
with **Google OAuth 2.0** sign-in.

---

## Tech stack

| Layer | Choice |
|---|---|
| Web framework | Flask 3.1 |
| Templates | Jinja2 (built-in) |
| OAuth 2.0 | Authlib 1.3 |
| Styling | Tailwind CSS (CDN) |
| Micro-interactivity | Alpine.js (CDN) |
| WSGI server | Gunicorn |
| Data | In-memory Python dicts |

---

## Project structure

```
univoice-jinja/
├── app.py                     ← routes, auth, Google OAuth, business logic
├── data/mock_data.py          ← seed data (mirrors mockData.ts)
├── templates/
│   ├── base.html              ← nav (with Google avatar), flash messages
│   ├── login.html             ← manual + Google Sign-In
│   ├── student_dashboard.html
│   ├── warden_dashboard.html
│   ├── mentor_dashboard.html
│   ├── not_found.html
│   └── admin/
│       ├── dashboard.html
│       ├── hostels.html
│       ├── wardens.html
│       ├── mentors.html
│       ├── students.html
│       ├── edit_user.html
│       ├── student_profile.html
│       └── complaints.html
├── .env.example               ← copy → .env and fill in credentials
├── requirements.txt
├── Procfile                   ← Render
├── render.yaml                ← one-click Render deploy
├── vercel.json                ← Vercel deploy
├── runtime.txt
└── .gitignore
```

---

## Running locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env with your credentials (see .env.example)
cp .env.example .env
# Edit .env — fill in SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# Load env vars and start
export $(grep -v '^#' .env | xargs)   # Linux/macOS
# On Windows (PowerShell): Get-Content .env | ForEach-Object { ... }

python app.py
```

Open **http://localhost:5000**

---

## Setting up Google OAuth 2.0

### Step 1 — Google Cloud Console

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Create a project (or select an existing one).
3. **APIs & Services → OAuth consent screen**
   - User type: **External**
   - App name: `UniVoice`, support email, developer email → Save
   - Scopes: add `email` and `profile`
   - Test users: add your own Google account for local testing
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Name: `UniVoice Web`
   - Authorised redirect URIs — add **all** of:
     ```
     http://localhost:5000/auth/google/callback          ← local dev
     https://your-app.onrender.com/auth/google/callback  ← Render
     https://your-app.vercel.app/auth/google/callback    ← Vercel
     ```
5. Click **Create** → copy **Client ID** and **Client Secret**.

### Step 2 — Set environment variables

**Locally (.env file):**
```
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx
SECRET_KEY=any-long-random-string
```

**Render:** Dashboard → your service → Environment → add the same three vars.

**Vercel:** Dashboard → your project → Settings → Environment Variables → add them.

### How sign-in works

1. User clicks **Sign in with Google**.
2. Google shows the account picker / consent screen.
3. After approval, Google redirects to `/auth/google/callback`.
4. The app extracts the user's **email** from Google's token.
5. That email is looked up in the user store:
   - **Found** → session is set, user is redirected to their dashboard.
   - **Not found** → flash error: *"No account found for email@x.com.
     Ask your administrator to register your email first."*

> **Important:** a Google account alone is not enough.  
> The administrator must first create a user record with that exact Google
> email address via **Admin → Manage Students / Wardens / Mentors**.

---

## Demo credentials (manual login)

| Role    | Email                  | Password |
|---------|------------------------|----------|
| Admin   | admin@kiit.ac.in       | 12345    |
| Student | student@kiit.ac.in     | 12345    |
| Warden  | warden@kiit.ac.in      | 12345    |
| Mentor  | mentor@kiit.ac.in      | 12345    |

---

## Deploying to Render

1. Push this repo to GitHub.
2. **render.com → New → Web Service** → connect repo.
3. Render auto-detects `render.yaml` — click **Deploy**.
4. In your service's **Environment** tab, add:
   - `SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `FLASK_ENV` = `production`
5. Add `https://your-app.onrender.com/auth/google/callback` to Google Console.

## Deploying to Vercel

1. Push repo to GitHub.
2. **vercel.com → New Project** → import repo.
3. Add env vars in **Settings → Environment Variables**.
4. Add the Vercel callback URL to Google Console.

> ⚠️ Vercel is serverless — in-memory data resets on each cold start.
> Use a database (e.g. Vercel Postgres, PlanetScale) for persistence.

---

## Connecting to your real backend

Every route in `app.py` reads from `_store` (a plain dict).  
To wire it to your actual Jinja backend:

1. Replace `_store["users"]` reads with your ORM / API calls.
2. Replace `session`-based auth with whatever your backend uses.
3. The Jinja templates receive only plain Python dicts — **no template
   changes needed** when swapping the data layer.
