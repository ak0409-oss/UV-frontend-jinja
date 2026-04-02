# UniVoice – Jinja2 / Flask Frontend

A **Flask + Jinja2** port of the UniVoice hostel grievance management system.
Identical feature-set to the React version, zero JavaScript frameworks required
(Alpine.js CDN only for minor UI interactions like accordion rows).

---

## Tech stack

| Layer | Choice |
|---|---|
| Web framework | Flask 3.1 |
| Templates | Jinja2 (built into Flask) |
| Styling | Tailwind CSS via CDN |
| Micro-interactivity | Alpine.js via CDN |
| Server | Gunicorn |
| Data | In-memory Python dicts (same seed as React mock data) |

---

## Project structure

```
univoice-jinja/
├── app.py                  ← all routes + business logic
├── data/
│   └── mock_data.py        ← seed data (mirrors src/data/mockData.ts)
├── templates/
│   ├── base.html           ← nav, flash messages, Tailwind/Alpine CDN
│   ├── login.html
│   ├── not_found.html
│   ├── student_dashboard.html
│   ├── warden_dashboard.html
│   ├── mentor_dashboard.html
│   └── admin/
│       ├── dashboard.html
│       ├── hostels.html
│       ├── wardens.html
│       ├── mentors.html
│       ├── students.html
│       ├── edit_user.html
│       ├── student_profile.html
│       └── complaints.html
├── requirements.txt
├── Procfile                ← for Render
├── render.yaml             ← one-click Render deploy config
├── runtime.txt
└── .gitignore
```

---

## Running locally

```bash
# 1. Clone / cd into repo
cd univoice-jinja

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open **http://localhost:5000**

---

## Demo credentials

| Role    | Email                  | Password |
|---------|------------------------|----------|
| Admin   | admin@kiit.ac.in       | 12345    |
| Student | student@kiit.ac.in     | 12345    |
| Warden  | warden@kiit.ac.in      | 12345    |
| Mentor  | mentor@kiit.ac.in      | 12345    |

---

## Deploying to Render (free tier)

1. Push this repo to GitHub / GitLab.
2. Go to **render.com → New → Web Service**.
3. Connect your repo — Render auto-detects `render.yaml`.
4. Set env var `SECRET_KEY` to any long random string (or let Render generate it).
5. Deploy — done. ✅

> **Note:** data is in-memory and resets on every deploy/restart. To persist
> data, replace the `_store` dict in `app.py` with a SQLite/PostgreSQL backend.

---

## Deploying to Vercel

Vercel does not natively support Flask, but you can use the
`@vercel/python` runtime:

1. Create `vercel.json` in the repo root:

```json
{
  "version": 2,
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

2. Install Vercel CLI: `npm i -g vercel`
3. Run `vercel` and follow the prompts.

> Vercel Python runtime is serverless — each request may spin up a fresh
> instance, so in-memory data **will reset between requests**. Use a database
> (e.g. Vercel Postgres) for persistence on Vercel.

---

## Connecting to your existing Jinja backend

The app is designed so every route either:
- Reads from `_store` (the in-memory dict), or
- Delegates to Flask's `session` for auth.

To wire it to your real backend:
1. Replace `_store["users"]` reads with API/DB calls.
2. Replace `session`-based auth with whatever your backend uses
   (JWT cookie, server-side session with Redis, etc.).
3. The templates are **pure Jinja2** — they only receive plain Python dicts,
   so no changes are needed in templates when you swap the data layer.

---

## Feature parity with React version

| Feature | React | Jinja |
|---|---|---|
| Role-based login (Admin / Student / Warden / Mentor) | ✅ | ✅ |
| Google OAuth placeholder | ✅ | ✅ |
| Student complaint filing + abusive-word detection | ✅ | ✅ |
| Student complaint history with status colours | ✅ | ✅ |
| Warden 5-section dashboard (urgent/pending/progress/done/archived) | ✅ | ✅ |
| Mentor escalation (mark urgent + comment) | ✅ | ✅ |
| Admin hostel CRUD | ✅ | ✅ |
| Admin warden / mentor / student CRUD | ✅ | ✅ |
| Admin complaint viewer with tab filter + delete | ✅ | ✅ |
| Student profile with flagged complaint history | ✅ | ✅ |
| Edit user (name / email / hostel / mentor) | ✅ | ✅ |
| Flash notifications (replaces sonner toasts) | ✅ | ✅ |
| Responsive Tailwind UI | ✅ | ✅ |
