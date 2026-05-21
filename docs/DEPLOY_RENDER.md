# Deploy BlackBoxNet — Neon + Render + GitHub (full walkthrough)

One GitHub repo → one public demo link. **Neon** holds Postgres. **Render** hosts the API (Docker) and the static React app. Pushes to `main` auto-redeploy Render when Auto-Deploy is enabled.

**Cost:** $0 on free tiers.

---

## What you are connecting

```
GitHub (dkabduli/BlackBoxNet)
    │
    ▼  auto-deploy on push
Render ── blackboxnet-web  →  https://blackboxnet-web.onrender.com  (portfolio link)
    │
    └── blackboxnet-api   →  https://blackboxnet-api.onrender.com
              │
              ▼  DATABASE_URL (SSL)
            Neon Postgres
```

| Piece | You do once | Updates on `git push`? |
|-------|-------------|-------------------------|
| Neon | Create project, copy connection string | No (data persists) |
| Render env | Paste `DATABASE_URL` on API service | Only if you change env in dashboard |
| Render services | Blueprint from repo | **Yes** — rebuild API + web |

---

## Before you start

- [ ] Code is on GitHub (e.g. `https://github.com/dkabduli/BlackBoxNet`)
- [ ] Free accounts: [Neon](https://neon.tech), [Render](https://render.com)
- [ ] ~15–20 minutes for first deploy

---

## Part 1 — Neon (database)

### 1.1 Create account and project

1. Go to [https://console.neon.tech](https://console.neon.tech) and sign up (GitHub login is fine).
2. Click **New Project**.
3. Name it e.g. `blackboxnet` (any region close to you or to Render `oregon` is fine).
4. Postgres version: default (15/16) is OK.
5. Click **Create project**.

### 1.2 Get the connection string

1. On the project **Dashboard**, find **Connection details**.
2. Choose **Connection string** (not “psql” only).
3. Role: default (`neondb_owner` or similar).
4. Database: default (`neondb`) — you do not need a separate DB name unless you want one.
5. Copy the **URI** that looks like:

   ```
   postgresql://neondb_owner:xxxxxxxx@ep-cool-name-12345678.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

6. Keep this secret. You will paste it only into Render (not into GitHub).

**Pooled vs direct:** Either works. Pooled (`-pooler` in host) is fine for this demo.

### 1.3 Nothing else on Neon for now

- You do **not** run migrations in the Neon console.
- The API runs `alembic upgrade head` on startup and creates tables automatically.

---

## Part 2 — Push code to GitHub (if not already)

On your machine, from the project folder:

```bash
cd /path/to/BlackBoxNet
git remote -v   # should show github.com/dkabduli/BlackBoxNet (or your fork)
git push origin main
```

Render will deploy from this repo.

---

## Part 3 — Render (hosting)

### 3.1 Connect GitHub to Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com).
2. Sign up / log in → authorize **GitHub** when asked.
3. Render can now see your repositories.

### 3.2 Deploy with Blueprint (recommended)

The repo includes `render.yaml`, which creates both services for you.

1. Click **New +** → **Blueprint**.
2. Connect the **BlackBoxNet** repository (same account that owns the repo).
3. Render shows a preview of two services:
   - `blackboxnet-api` (Docker, web service)
   - `blackboxnet-web` (static site)
4. Click **Apply** (or **Create**).

Blueprint deploy may **fail the first time** for the API if `DATABASE_URL` is missing — that is normal. Continue below.

### 3.3 Add Neon to the API service

1. Open **blackboxnet-api** in the Render dashboard.
2. Go to **Environment** (left sidebar).
3. Add or edit:

   | Key | Value |
   |-----|--------|
   | `DATABASE_URL` | Paste your full Neon URI from Part 1 |
   | `REAL_DEVICE_ENABLED` | `false` |

   Optional (usually not needed):

   | Key | Value |
   |-----|--------|
   | `DATABASE_URL_SYNC` | Same as `DATABASE_URL` (plain `postgresql://`, no `+asyncpg`) |

   These are already set by the blueprint — confirm they exist:

   | Key | Value |
   |-----|--------|
   | `SCENARIOS_DIR` | `/packages/mock-scenarios` |
   | `GIT_REPO_PATH` | `/data/config-repo` |
   | `CORS_ORIGINS` | Linked from web service hostname |

4. Click **Save Changes**.
5. Trigger a deploy: **Manual Deploy** → **Deploy latest commit** (or push a small commit to `main`).

Wait until status is **Live** (API build can take 5–10 minutes first time).

### 3.4 Confirm the web service

1. Open **blackboxnet-web**.
2. Under **Environment**, you should see:
   - `VITE_API_URL` → from `blackboxnet-api` hostname
   - `VITE_SHOW_DEMO_BANNER` → `true`
3. If the API was not live when the web service first built, click **Manual Deploy** on **blackboxnet-web** after the API is live (so the frontend points at the correct API).

### 3.5 Turn on auto-deploy (usually already on)

For **each** service (`blackboxnet-api`, `blackboxnet-web`):

1. **Settings** → **Build & Deploy**
2. **Auto-Deploy** = **Yes**
3. **Branch** = `main` (or your default branch)

After this, every `git push origin main` rebuilds and updates the live site.

---

## Part 4 — Wire it together (checklist)

| Connection | How it is wired |
|------------|------------------|
| Neon → API | `DATABASE_URL` env var on `blackboxnet-api` |
| API → Browser | `VITE_API_URL` baked into static build → calls `https://blackboxnet-api.onrender.com` |
| API → Browser CORS | `CORS_ORIGINS` includes `blackboxnet-web.onrender.com` |
| GitHub → Render | Auto-deploy on push to `main` |

You do **not** put the Neon password in GitHub or in the repo.

---

## Part 5 — Verify live

### 5.1 API

Open (replace with your host if different):

```
https://blackboxnet-api.onrender.com/api/health
```

Expected:

```json
{"status":"healthy","service":"blackboxnet-api"}
```

First request after idle may take **30–60 seconds** (free tier sleep).

Scenarios list:

```
https://blackboxnet-api.onrender.com/api/scenarios
```

Should return 6 scenarios with `topology` objects.

### 5.2 Frontend (your portfolio link)

```
https://blackboxnet-web.onrender.com
```

1. Header: **Cisco | Juniper | Nokia**
2. Pick a scenario → should reset to T1
3. **Run T1** … **Run T5** → incident appears
4. Yellow banner about cold start is OK

### 5.3 If something fails

| Problem | What to do |
|---------|------------|
| API deploy failed | **Logs** tab on `blackboxnet-api` — often missing/wrong `DATABASE_URL` or Neon SSL |
| White screen / API errors | Redeploy **web** after API is live; check browser Network tab for CORS or 502 |
| CORS error | API → Environment → set `CORS_ORIGINS` to `blackboxnet-web.onrender.com` (no `https://`) → redeploy API |
| 502 on first click | Wait for cold start; retry |
| Old UI after push | Wait for both services **Live**; hard refresh browser (Cmd+Shift+R) |

---

## Part 6 — Day-to-day workflow

```bash
# local changes
git add .
git commit -m "your message"
git push origin main
```

1. Render builds API + web automatically.
2. Neon keeps existing DB data (simulations already run stay until reset in the app).
3. API runs migrations on startup if you added new Alembic revisions.

Share only the **web** URL on your resume:

`https://blackboxnet-web.onrender.com`

---

## Environment reference

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | API | Neon `postgresql://...?sslmode=require` |
| `DATABASE_URL_SYNC` | API | Optional; Alembic (derived if omitted) |
| `SCENARIOS_DIR` | API | `/packages/mock-scenarios` |
| `GIT_REPO_PATH` | API | `/data/config-repo` |
| `REAL_DEVICE_ENABLED` | API | `false` for public demo |
| `CORS_ORIGINS` | API | Web hostname (from blueprint) |
| `VITE_API_URL` | Web | API hostname at build time |
| `VITE_SHOW_DEMO_BANNER` | Web | `true` |

See `.env.render.example` in the repo root.

---

## Optional: custom domain

Render → **blackboxnet-web** → **Settings** → **Custom Domain** → follow DNS instructions.

If the hostname changes, update `CORS_ORIGINS` on the API to match.

---

## Security (public demo)

- Never commit Neon URL to GitHub.
- Keep `REAL_DEVICE_ENABLED=false` on Render.
- Do not store lab SSH credentials in Render for the portfolio instance.
