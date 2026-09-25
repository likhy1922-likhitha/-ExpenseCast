# ExpenseCast

**Intelligent expense tracking and financial forecasting with an LSTM model**

ExpenseCast is a full-stack personal-finance application for recording income and expenses, creating budgets and savings goals, tracking investments, importing statements, and forecasting future spending.

## Live application

- Website: [https://expensecast.onrender.com](https://expensecast.onrender.com)
- API health check: [https://expensecast-api.onrender.com/health](https://expensecast-api.onrender.com/health)
- Interactive API documentation: [https://expensecast-api.onrender.com/docs](https://expensecast-api.onrender.com/docs)

> The free Render backend can take about a minute to wake after being idle.

## Technology stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts
- **Backend:** FastAPI, SQLAlchemy, Alembic, Pydantic
- **Authentication:** Supabase Auth
- **Production database:** Supabase PostgreSQL
- **Machine learning:** TensorFlow/Keras LSTM and scikit-learn baselines
- **Deployment:** Render Web Service and Render Static Site

## Main features

- Email/password authentication and protected routes
- User onboarding and profile settings
- Income, expense, savings, and investment transactions
- Search, filtering, sorting, pagination, and soft deletion
- Default and custom categories with rule-based categorization
- CSV import with column mapping and duplicate detection
- PDF statement import with confidence scoring
- Monthly budgets and warning thresholds
- Savings goals and contribution tracking
- Investment and recurring-payment tracking
- LSTM forecasts for 7, 30, and 90 days
- Dashboard charts, financial insights, and reports
- Audit logging and API rate limiting

## Architecture

1. The React frontend authenticates users through Supabase Auth.
2. The frontend sends the Supabase access token to FastAPI as a bearer token.
3. FastAPI verifies legacy HS256 tokens or modern ES256/RS256 tokens through Supabase JWKS.
4. Protected API queries are scoped to the authenticated `user_id`.
5. SQLAlchemy stores application records in Supabase PostgreSQL.
6. The forecasting service uses the trained LSTM model and saved scalers.

Supabase Auth accounts and ExpenseCast financial records are separate: Auth stores login identities, while the application tables store transactions, budgets, goals, and investments.

## Repository structure

```text
ExpenseCast/
├── frontend/             React/Vite/TypeScript application
├── backend/              FastAPI API, Alembic migrations, and tests
├── machine-learning/     Data preparation, training, and evaluation
├── supabase/             Optional Row-Level Security policy SQL
└── docker-compose.yml
```

## Prerequisites

- Python 3.11
- Node.js 18 or newer
- npm
- A Supabase project

## Run locally on Windows

Clone the repository into a folder without the repository's leading hyphen:

```bat
git clone https://github.com/likhy1922-likhitha/-ExpenseCast.git ExpenseCast
cd ExpenseCast
```

### 1. Start the backend

```bat
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`, then run:

```bat
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000), with documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the frontend

Open a second Command Prompt:

```bat
cd ExpenseCast\frontend
npm install
copy .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Environment variables

### Frontend (`frontend/.env`)

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_LEGACY_ANON_KEY
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_ENABLE_DEMO_MODE=false
```

`VITE_SUPABASE_URL` must contain only the base project URL. Do not append `/rest/v1/` and do not repeat `VITE_SUPABASE_URL=` inside its value.

### Backend (`backend/.env`)

```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite:///./expensecast.db
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_LEGACY_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_BACKEND_ONLY_SECRET_KEY
SUPABASE_JWT_SECRET=YOUR_LEGACY_JWT_SECRET_IF_APPLICABLE
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
ENABLE_DEMO_MODE=false
```

Modern Supabase ES256/RS256 access tokens are verified automatically through JWKS. `SUPABASE_JWT_SECRET` is required only for a project that still issues legacy HS256 tokens.

Never place a secret/service-role key in `frontend/.env`, and never commit any `.env` or `.db` file.

## Supabase setup

1. Create a Supabase project.
2. Copy the project URL and publishable/anon key from **Project Settings → API Keys**.
3. Copy a PostgreSQL connection string from **Connect → Direct → Session pooler** when deploying to Render.
4. Set the production website under **Authentication → URL Configuration**:
   - Site URL: `https://expensecast.onrender.com`
   - Redirect URL: `https://expensecast.onrender.com/**`
5. Run the Alembic migration against the PostgreSQL `DATABASE_URL` to create the application tables.
6. Optionally run `supabase/rls-policies.sql` if browser/direct Supabase table access is enabled.

The FastAPI API also enforces user isolation by validating the bearer token and filtering protected queries by `user_id`.

## Render deployment

### Backend Web Service

| Setting | Value |
| --- | --- |
| Service | Web Service |
| Runtime | Python 3 |
| Root directory | Leave blank |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `cd backend && python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Important backend variables:

```env
PYTHON_VERSION=3.11.11
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=YOUR_SUPABASE_SESSION_POOLER_URI
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
CORS_ORIGINS=http://localhost:5173,https://expensecast.onrender.com
FRONTEND_URL=https://expensecast.onrender.com
ENABLE_DEMO_MODE=false
```

Do not use production SQLite on a free Render Web Service. Its filesystem is ephemeral, so SQLite records can disappear after a restart, spin-down, or redeployment. Use Supabase PostgreSQL for persistent records.

### Frontend Static Site

| Setting | Value |
| --- | --- |
| Service | Static Site |
| Root directory | `frontend` |
| Build command | `npm install && npm run build` |
| Publish directory | `dist` |

Set these production variables:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_LEGACY_ANON_KEY
VITE_API_BASE_URL=https://expensecast-api.onrender.com
VITE_ENABLE_DEMO_MODE=false
```

Add this Render rewrite rule so React Router pages work when refreshed:

| Source | Destination | Action |
| --- | --- | --- |
| `/*` | `/index.html` | Rewrite |

## Machine-learning pipeline

The repository includes trained model artifacts. To retrain them:

```bash
cd machine-learning
pip install -r ../backend/requirements.txt
python data/generate_sample_data.py --demo
python scripts/preprocess.py
python scripts/train_baseline.py
python scripts/train_lstm.py
python scripts/evaluate.py
```

The pipeline generates the LSTM model, scalers, metadata, evaluation metrics, and training history.

## Tests

Backend:

```bash
cd backend
python -m pytest tests -v
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

## Demo Mode

Demo Mode is optional and is disabled in the current production deployment. To enable it in another environment, set both `VITE_ENABLE_DEMO_MODE=true` and `ENABLE_DEMO_MODE=true`. Keep demo data separate from real user records.

## Known limitations

- A free Render backend can have a cold-start delay after being idle.
- The LSTM is trained mainly on synthetic financial records, so accuracy can decrease for very different real spending patterns.
- PDF extraction relies on heuristics and may require manual review for unfamiliar bank layouts.
- Scanned PDFs need optional OCR dependencies.
- Pending import previews are stored in process memory and should move to Redis before multi-worker scaling.

## Security notes

- Frontend code may contain only the Supabase project URL and publishable/anon key.
- Supabase secret/service-role keys and database passwords are backend-only.
- Never commit `.env`, local SQLite `.db`, statement files, or personal financial exports.
- Rotate any secret immediately if it is accidentally exposed.
