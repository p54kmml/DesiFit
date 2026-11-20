# ⚡ DesiFit — AI Fitness Companion

A commercial-grade, full-stack fitness and nutrition platform built with **FastAPI**, **Streamlit**, **SQLite/SQLAlchemy**, **Plotly**, and **AI Assistant Integration**.

---

## 🚀 Key Features

1. **Authentication & Multi-User Onboarding System**:
   - JWT-based authentication with bcrypt password hashing.
   - **Secure Account Recovery & Password Reset**:
     - Cryptographically secure single-use reset tokens with 15-minute expiration windows.
     - SHA-256 hashed token persistence ensuring plaintext tokens are never stored in the database.
     - Robust multi-tiered rate limiting by client IP (5/15 min) and email address (3/15 min).
     - Account enumeration protection ensuring timing-attack and presence leaks are prevented.
     - Multi-user isolation guaranteeing User A's token cannot reset User B's password.
     - Safe development mode fallback allowing complete local verification without requiring an external SMTP provider.
     - Full SMTP integration supporting STARTTLS/SSL email delivery with dark-themed responsive templates.
   - **First-Time User Onboarding Wizard**: Every newly registered user completes their own fitness baseline (Age, Biological Sex, Height, Current Body Weight, Target Goal Weight, Fitness Goal, Physical Activity Level, Dietary Preference, and Experience Level).
   - **Zero Leaked Defaults**: Newly registered accounts start clean without another user's personal defaults or 70kg weight.
   - **Automatic Mifflin-St Jeor TDEE Calibration**: Scientifically calculates individualized Basal Metabolic Rate (BMR), Total Daily Energy Expenditure (TDEE), daily caloric targets, and protein targets (g/day).
   - **Strict Data Isolation**: Every workout routine, logged exercise, nutrition record, body measurement, and AI conversation is linked strictly to the authenticated `user_id`. Existing onboarded accounts seamlessly bypass onboarding and retain their existing profile (e.g. 70kg baseline).

2. **Personalized Dashboard**:
   - Real-time KPIs: Current Weight, Target Weight, Daily Calorie & Protein Targets vs. Consumption.
   - Interactive weekly training frequency chart via Plotly.
   - Daily macro breakdown donut chart.
   - Quick action shortcuts and recent activity feed.

3. **DesiFit AI Fitness Assistant**:
   - Personal coach for workout planning, muscle hypertrophy, fat loss, and Indian nutrition.
   - Seamless integration with OpenAI API (`gpt-4o-mini`).
   - Built-in intelligent rule-based expert engine as an automatic fallback when no API key is provided.
   - Persistent conversation memory across sessions.

4. **Workout Management**:
   - Create and organize structured workout routines.
   - Custom sets, repetitions, and rest intervals.
   - Comprehensive exercise library with Muscle Groups: Chest, Back, Shoulders, Biceps, Triceps, Legs, Abs.
   - Workout session logging with exercise weights and reps.

5. **Nutrition & Macro Tracker**:
   - Food logging by meal category: Breakfast, Lunch, Dinner, Snacks.
   - Pre-seeded with authentic Desi fitness staples (paneer, yellow moong dal, whole wheat roti, soya chunks, chicken tikka, curd/dahi, egg bhurji, chana masala) and gym nutrition staples.
   - Real automatic nutritional calculations and dynamic progress bars against daily targets.
   - Custom food item addition.

6. **Body Progress Tracker**:
   - Log body weight, circumferences (chest, waist, arm, thigh), notes, and dates.
   - Interactive Plotly visualization for Weight Trajectory with goal line.
   - Multi-line chart for tracking body circumference changes over time.

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI + Uvicorn
- **Database**: SQLite
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Data Visualizations**: Plotly
- **Authentication**: PyJWT + Passlib / Bcrypt
- **AI Integration**: OpenAI Python SDK + Rule-Based Fallback
- **API Client**: Requests / HTTPX

---

## 📂 Project Structure

```
DesiFit/
│
├── backend/
│   ├── main.py              # FastAPI app and lifespan database initializer
│   ├── database.py          # SQLite engine, SessionLocal, Base
│   ├── models.py            # SQLAlchemy database models (including PasswordResetToken)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT token generation, bcrypt, user dependencies, password validator
│   ├── security/
│   │   └── rate_limiter.py  # Thread-safe sliding window rate limiting for IP and email
│   ├── routers/
│   │   ├── auth.py          # /auth/register, /auth/login, /auth/forgot-password, /auth/reset-password
│   │   ├── profile.py       # /profile GET & PUT
│   │   ├── dashboard.py     # /dashboard/stats
│   │   ├── workouts.py      # /workouts/plans, /workouts/logs
│   │   ├── exercises.py     # /exercises library & custom additions
│   │   ├── nutrition.py     # /nutrition/foods, /nutrition/logs, /nutrition/summary
│   │   ├── progress.py      # /progress/measurements
│   │   └── ai.py            # /ai/chat, /ai/history, /ai/status
│   └── services/
│       ├── ai_service.py    # OpenAI integration and rule-based fallback
│       ├── email_service.py # Secure SMTP delivery and dark HTML password recovery templates
│       ├── seed_data.py     # Exercise and Desi nutrition seeding
│       └── stats_service.py # Real-time dashboard KPI computations
│
├── frontend/
│   ├── app.py               # Main Streamlit application entrypoint
│   ├── api_client.py        # Typed REST API client for backend communication
│   ├── styles.py            # Dark charcoal + lime green SaaS UI theme & CSS
│   ├── components/
│   │   └── charts.py        # Plotly dark-themed visualizations
│   └── views/
│       ├── auth_view.py     # Login, registration, forgot-password, and reset-password views
│       ├── dashboard_view.py# Executive dashboard with KPIs & charts
│       ├── ai_view.py       # DesiFit AI chat interface
│       ├── workouts_view.py # Plan creator, session logger & history
│       ├── exercises_view.py# Muscle group explorer & exercise catalog
│       ├── nutrition_view.py# Food logging, macro donut & daily progress
│       ├── progress_view.py # Weight trajectory & measurement charts
│       └── profile_view.py  # User settings & Mifflin-St Jeor macro calculator
│
├── tests/
│   ├── conftest.py          # Pytest fixtures and in-memory test database
│   ├── test_auth.py         # Authentication and registration tests
│   ├── test_password_reset.py # Complete password recovery and security test suite
│   ├── test_workouts.py     # Workout plan and exercise tests
│   ├── test_nutrition.py    # Food logging and nutrition summary tests
│   ├── test_progress.py     # Body measurement and dashboard tests
│   └── test_ai.py           # AI assistant and fallback mode tests
│
├── requirements.txt         # Project dependencies
├── .env.example             # Environment template
├── .env                     # Local configuration
├── .gitignore               # Ignored files (database, cache, virtualenvs)
├── README.md                # Project documentation
└── run.py                   # Unified launcher for Backend & Frontend
```

---

## ⚡ Quick Start Instructions (Windows)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`, then generate and set a unique signing key:
```powershell
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Paste the generated value after `SECRET_KEY=` in `.env`. Never commit or share `.env`.

#### Configure Email (SMTP) for Password Recovery
DesiFit supports both production SMTP email delivery and safe local development testing:

**Local Development (Default - No SMTP server required):**
Leave `SMTP_HOST` blank in `.env`. The backend runs in development mode, where:
- Plaintext reset tokens are never exposed in production or logged to application logs.
- The UI displays an in-app developer helper box with your 15-minute test recovery token.
- Clicking the provided button or link immediately loads the password reset form with the token prefilled.
- No dummy/fake emails are falsely reported as sent.

**Production Deployment:**
Provide valid SMTP credentials in your production environment or `.env`:
```env
SMTP_HOST="smtp.mailgun.org"       # Or smtp.sendgrid.net, smtp.gmail.com, etc.
SMTP_PORT=587                     # 587 for STARTTLS, 465 for SSL
SMTP_USERNAME="postmaster@yourdomain.com"
SMTP_PASSWORD="your-secure-smtp-password"
SMTP_FROM_EMAIL="noreply@desifit.in"
FRONTEND_URL="https://app.desifit.in"
ENVIRONMENT="production"
```
In production:
- Reset tokens are sent directly to the user's registered email via secure TLS.
- Tokens and dev reset links are strictly omitted from API responses and client interfaces.
- Generic response messages prevent user registration enumeration.

*(Optional)* Add your OpenAI API key in `.env` if you want live OpenAI responses:
```env
OPENAI_API_KEY="sk-..."
```
*Note: If no API key is provided, DesiFit automatically activates its built-in rule-based expert fitness assistant.*

### 3. Run the Entire Application
Launch both the FastAPI backend and Streamlit frontend simultaneously with the unified runner:
```bash
python run.py
```

Or run the services individually:
- **FastAPI Backend**:
  ```bash
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Streamlit Frontend**:
  ```bash
  python -m streamlit run frontend/app.py --server.port 8501
  ```

### 4. Access URLs
- **Streamlit Frontend App**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing

Run the full automated test suite:
```bash
python -m pytest -v
```
The automated test suite covers:
- Safe database table creation and automated library seeding.
- User registration, duplicate detection, login, and JWT-protected routes.
- Authenticated endpoint access guards and multi-user data isolation.
- Exercise library filtering and custom exercise ownership.
- Workout plan creation, session logging, and custom split persistence.
- Nutrition logging, macro aggregations, and daily summary calculations.
- Body measurement records, profile synchronization, and recent-record ordering.
- AI assistant query processing, saved workout preferences, and rule-based fallback responses.
- Forgot password requests and user enumeration protection.
- Cryptographic token generation and SHA-256 token hashing in SQLite.
- Token expiration enforcement (15-minute window) and single-use invalidation.
- Token invalidation when subsequent requests are initiated.
- Multi-tier sliding-window rate limiting by IP (5/15 min) and email (3/15 min).
- Strict multi-user isolation preventing cross-account password tampering.
- Password complexity validation and bcrypt re-hashing verification.
- Safe SMTP email dispatch and error handling without secret leakage.
