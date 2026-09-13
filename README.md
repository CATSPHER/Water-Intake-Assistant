# Hydration Tracker (FastAPI + LangChain + Streamlit)

An AI-assisted daily water intake tracker. Built as a standalone Python
service so it can be called from your MERN app's Node backend as an
internal microservice (per your architecture: Node → FastAPI).

## Structure

```
hydration-tracker/
  backend/            FastAPI service — the real API your Node backend calls
    main.py
    models.py
    schemas.py
    database.py
    ai_feedback.py    LangChain + Claude logic for smart feedback
    requirements.txt
  streamlit_app/       Standalone UI for local testing/demoing the API
    app.py
    requirements.txt
```

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
uvicorn main:app --reload --port 8000
```

Get a free token at https://huggingface.co/settings/tokens (read access is enough).
Default model is `mistralai/Mistral-7B-Instruct-v0.3` — override with the
`HF_MODEL` env var if you want a different one. Note: some HF models require
you to accept their terms on the model page before the API will serve requests.

**Streamlit (in a separate terminal):**
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Streamlit defaults to hitting `http://localhost:8000` — override with
`API_BASE_URL` env var if needed.

## API endpoints

- `POST /api/hydration/log` — `{ user_id, amount_ml }` → logs an intake entry
- `GET /api/hydration/logs/today?user_id=...` — today's entries (for the log table)
- `GET /api/hydration/logs/monthly?user_id=...` — daily totals, last 30 days (for the chart)
- `POST /api/hydration/feedback` — `{ user_id, daily_goal_ml }` → AI-generated feedback

## Deploying (per your existing setup)

- Deploy `backend/` as its own **Render Web Service**, Root Directory set to `backend`.
  Build: `pip install -r requirements.txt`. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Set `HUGGINGFACEHUB_API_TOKEN` and `ALLOWED_ORIGINS` (comma-separated list of
  your Node backend / any domains that will call this service) as env vars on Render.
- `streamlit_app/` is for testing only — deploy it separately on Render too if
  you want a persistent demo, or just run it locally. It's not meant to be
  embedded in your MERN frontend.

## Integrating with your MERN app

Your **Node backend** (not React directly) should call this service, per your
chosen architecture:

```js
// In your Node backend
const axios = require("axios");
const AI_SERVICE_URL = process.env.AI_SERVICE_URL; // Render URL of this FastAPI service

app.post("/api/hydration/log", authenticateJWT, async (req, res) => {
  const { amount_ml } = req.body;
  const user_id = req.user.id; // from verified JWT
  const response = await axios.post(`${AI_SERVICE_URL}/api/hydration/log`, { user_id, amount_ml });
  res.json(response.data);
});
```

Repeat this proxy pattern for the `logs/today`, `logs/monthly`, and `feedback`
routes — Node verifies the user, then forwards `user_id` to FastAPI and
returns the result to React.

## Notes / things to decide as you build

- Database is SQLite by default (`hydration.db` file) — fine for development.
  For production, set `DATABASE_URL` to a Postgres connection string
  (e.g. from a free Render Postgres instance) — no code changes needed
  beyond that env var.
- `daily_goal_ml` currently defaults to 2500ml and is passed per-request.
  If you want per-user persistent goals, you'll want a small `users` or
  `user_settings` table — happy to add that when you're ready.
- The AI feedback prompt is intentionally simple (2-3 sentences, no medical
  advice) — easy to extend with streaks, hydration reminders, etc. later.
