# Technical Design Document (TD)

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |

---

## 1. Project Structure

```
ynab-notifier/
├── docker-compose.yml              # All services: django, celery, postgres, redis, caddy
├── Dockerfile                      # Django app container
├── Caddyfile                       # Reverse proxy config
├── .env                            # Secrets (not in VCS)
├── .env.example                    # Template
│
├── backend/                        # Django project root
│   ├── manage.py
│   ├── requirements.txt            # or pyproject.toml (uv)
│   │
│   ├── config/                     # Django project settings
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Shared settings
│   │   │   ├── development.py      # Dev overrides
│   │   │   └── production.py       # Prod overrides
│   │   ├── urls.py                 # Root URL config
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py               # Celery app config
│   │
│   ├── apps/
│   │   ├── accounts/               # Authentication & user management
│   │   │   ├── models.py           # Recipient model (extends User)
│   │   │   ├── admin.py            # Django Admin customization
│   │   │   ├── serializers.py      # DRF serializers
│   │   │   ├── views.py            # Auth views (login, logout, token)
│   │   │   ├── urls.py
│   │   │   └── tests/
│   │   │
│   │   ├── budgets/                # YNAB integration & forecasting
│   │   │   ├── models.py           # Category cache, income config
│   │   │   ├── admin.py
│   │   │   ├── services/
│   │   │   │   ├── ynab_client.py  # YNAB API wrapper
│   │   │   │   ├── forecasting.py  # Remaining amount calculations
│   │   │   │   └── sync.py         # Delta sync logic
│   │   │   ├── serializers.py
│   │   │   ├── views.py            # Dashboard & trends API
│   │   │   ├── urls.py
│   │   │   └── tests/
│   │   │
│   │   └── notifications/          # SMS notification service
│   │       ├── models.py           # NotificationLog
│   │       ├── admin.py
│   │       ├── services/
│   │       │   ├── sms.py          # Twilio SMS sender
│   │       │   ├── formatter.py    # Message formatting
│   │       │   └── webhook.py      # Inbound SMS handler
│   │       ├── tasks.py            # Celery tasks
│   │       ├── views.py            # Twilio webhook endpoint
│   │       ├── urls.py
│   │       └── tests/
│   │
│   └── common/                     # Shared utilities
│       ├── middleware.py
│       └── utils.py
│
└── frontend/                       # React app (Vite)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── public/
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/                    # API client functions
        │   ├── client.js           # Axios instance with auth
        │   ├── auth.js             # Login/logout/refresh
        │   └── budget.js           # Dashboard & trends data
        ├── components/
        │   ├── Layout/
        │   ├── Login/
        │   ├── Dashboard/
        │   │   ├── CategoryCard.jsx
        │   │   ├── ProgressBar.jsx
        │   │   └── TotalRemaining.jsx
        │   └── Trends/
        │       └── SpendingChart.jsx
        ├── hooks/
        │   ├── useAuth.js
        │   └── useBudget.js
        ├── context/
        │   └── AuthContext.jsx
        └── styles/
```

## 2. Detailed Component Design

### 2.1 YNAB Service Layer (`budgets/services/`)

#### 2.1.1 `ynab_client.py` - YNAB API Wrapper

```python
# Conceptual interface - not final implementation

class YNABClient:
    """Wraps the ynab Python SDK with caching and delta sync."""

    def __init__(self, access_token: str, budget_id: str):
        self.config = ynab.Configuration(access_token=access_token)
        self.budget_id = budget_id

    def get_categories(self, last_knowledge: int = None) -> CategoriesResult:
        """
        Fetch all categories for the budget.
        Uses delta sync if last_knowledge is provided.
        Returns categories and new server_knowledge value.
        """

    def get_month_categories(self, month: str) -> list[CategoryDetail]:
        """
        Fetch all category details for a specific month.
        Month format: YYYY-MM-DD (first of month).
        """

    def get_scheduled_transactions(self) -> list[ScheduledTransaction]:
        """
        Fetch all scheduled transactions.
        Used to calculate expected income.
        """

    def calculate_expected_income(self) -> int:
        """
        Sum all scheduled income transactions for the current month.
        Returns amount in milliunits.
        Income transactions are identified by positive amount (inflow).
        """
```

**YNAB Milliunit Handling:**
All YNAB amounts are in milliunits (1/1000 of currency unit). The service layer stores values in milliunits internally and only converts to display format at the serializer/formatter level.

```python
# Conversion
display_amount = milliunit_amount / 1000  # 500000 → 500.00
```

**Delta Sync Strategy:**
1. On first sync, fetch all categories (no `last_knowledge_of_server`)
2. Store the returned `server_knowledge` value in the database
3. On subsequent syncs, pass `last_knowledge_of_server` to only get changes
4. Update stored `server_knowledge` after each successful sync
5. If delta sync fails, fall back to full sync

#### 2.1.2 `forecasting.py` - Forecasting Engine

```python
# Conceptual interface

class ForecastingEngine:
    """Calculates remaining amounts based on expected income."""

    def calculate_remaining(self, category: CachedCategory) -> int:
        """
        Calculate remaining amount for a single category.

        If category has a goal_target:
            remaining = goal_target + activity  (activity is negative)
        Else:
            remaining = balance  (YNAB's calculated balance)

        Returns amount in milliunits.
        """

    def get_recipient_summary(self, recipient: Recipient) -> RecipientSummary:
        """
        Build a complete budget summary for a recipient.
        Returns filtered categories with remaining amounts
        and a total_remaining sum.
        """

    def get_expected_income(self) -> int:
        """
        Returns expected monthly income in milliunits.
        Manual override takes precedence over scheduled transactions.
        """
```

**Remaining Calculation Deep Dive:**

```
YNAB Category Fields (from API):
  - goal_target:  500000  (= $500.00 goal for the month)
  - activity:    -247500  (= $247.50 spent this month)
  - balance:      152500  (= $152.50 actually assigned - activity)
  - budgeted:     400000  (= $400.00 assigned to category so far)

YNAB's native balance:
  balance = budgeted + activity = 400000 + (-247500) = 152500 ($152.50)
  → Only accounts for money ALREADY assigned to this category

This app's remaining:
  remaining = goal_target + activity = 500000 + (-247500) = 252500 ($252.50)
  → Accounts for the FULL goal, assuming remaining income will fund it

Difference: $100.00 — the paycheck that hasn't arrived yet but is expected
```

#### 2.1.3 `sync.py` - Data Synchronization

```python
# Conceptual interface

class YNABSyncService:
    """Manages periodic synchronization of YNAB data to local cache."""

    def sync_categories(self) -> SyncResult:
        """
        Sync all categories from YNAB to local PostgreSQL cache.
        Uses delta sync when possible.
        Called by Celery periodic task.
        """

    def sync_scheduled_transactions(self) -> SyncResult:
        """
        Sync scheduled transactions for income calculation.
        Called by Celery periodic task.
        """

    def force_sync(self) -> SyncResult:
        """
        Force a full sync (ignoring delta).
        Used for on-demand SMS requests to ensure fresh data.
        """
```

### 2.2 Notification Service (`notifications/services/`)

#### 2.2.1 `sms.py` - Twilio SMS Sender

```python
# Conceptual interface

class SMSService:
    """Sends SMS messages via Twilio."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def send_message(self, to_number: str, body: str) -> MessageResult:
        """
        Send an SMS message.
        Returns message SID and status.
        Logs attempt to NotificationLog.
        """

    def validate_webhook(self, request) -> bool:
        """
        Validate that an inbound webhook request is from Twilio.
        Uses Twilio request signature validation.
        """
```

#### 2.2.2 `formatter.py` - Message Formatter

```python
# Conceptual interface

class MessageFormatter:
    """Formats budget data into SMS-friendly text."""

    def format_daily_notification(
        self,
        recipient_name: str,
        categories: list[CategoryRemaining],
        timestamp: datetime,
    ) -> str:
        """
        Format:
        Daily Budget Update (Mon, Feb 14):

        Groceries:   $252.50 remaining
        Gas:          $89.00 remaining
        Dining Out:   $62.30 remaining
        ─────────────────────
        Total:       $403.80 remaining
        """

    def format_on_demand(
        self,
        categories: list[CategoryRemaining],
        timestamp: datetime,
    ) -> str:
        """Same format but with on-demand header and current time."""
```

#### 2.2.3 `webhook.py` - Inbound SMS Handler

```python
# Conceptual interface

class InboundSMSHandler:
    """Processes inbound SMS messages from recipients."""

    TRIGGER_KEYWORDS = {"UPDATE", "BUDGET", "CHECK"}

    def handle(self, from_number: str, body: str) -> str | None:
        """
        1. Look up recipient by phone number
        2. If body contains a trigger keyword, generate fresh summary
        3. Return response body to send back, or None to ignore
        """
```

#### 2.2.4 `tasks.py` - Celery Tasks

```python
# Conceptual interface

@shared_task
def dispatch_daily_notifications():
    """
    Runs every minute via Celery Beat.
    Checks which recipients are due for their daily notification
    based on their configured notification time.
    Sends SMS to each due recipient.
    Marks recipients as notified for today.
    """

@shared_task
def sync_ynab_data():
    """
    Runs every 15 minutes via Celery Beat.
    Performs delta sync of YNAB categories and scheduled transactions.
    """

@shared_task
def process_inbound_sms(from_number: str, body: str):
    """
    Triggered by the Twilio webhook view.
    Processes the inbound message and sends a response.
    """
```

### 2.3 Authentication Design

#### Phase 1: Username/Password with JWT

```
Login Flow:
  1. POST /api/auth/login/ { username, password }
  2. Server validates credentials (Django's authenticate())
  3. Server returns { access_token, refresh_token }
  4. Frontend stores tokens in memory (access) and httpOnly cookie (refresh)
  5. All API requests include: Authorization: Bearer <access_token>

Token Refresh:
  1. Access token expires in 15 minutes
  2. Frontend detects 401 response
  3. POST /api/auth/refresh/ with refresh token (from httpOnly cookie)
  4. Server returns new access token
  5. If refresh token expired (7 days), redirect to login

Security Best Practices:
  - Passwords hashed with PBKDF2 (Django default) or Argon2
  - Access tokens are short-lived (15 min)
  - Refresh tokens stored in httpOnly, Secure, SameSite=Strict cookies
  - CORS restricted to frontend origin only
  - Rate limiting on login endpoint (django-ratelimit or DRF throttling)
  - Account lockout after N failed attempts
```

#### Future Phase: Magic Link Upgrade

```
Magic Link Flow:
  1. POST /api/auth/magic-link/ { email_or_phone }
  2. Server generates a single-use, time-limited token
  3. Server sends token via SMS or email as a link
  4. Recipient clicks link: GET /api/auth/verify/?token=<token>
  5. Server validates token, issues JWT pair
  6. Redirect to dashboard

Benefits:
  - No passwords to manage, leak, or forget
  - Authentication via a channel the recipient already uses (SMS)
  - Simpler UX for non-technical users
```

### 2.4 Caching Strategy

#### YNAB Data Cache (PostgreSQL)

```
Cache Layer:
  - All YNAB data is cached in PostgreSQL models (CachedCategory, etc.)
  - The web portal and SMS notifications read from cache, NOT the YNAB API
  - Cache is refreshed every 15 minutes via Celery periodic task
  - On-demand SMS triggers a forced fresh sync before responding

Cache Invalidation:
  - Delta sync via server_knowledge handles incremental updates
  - Full sync runs once daily (midnight) as a safety net
  - Manual "Force Sync" button in Django Admin for immediate refresh

Why PostgreSQL and not Redis for cache?
  - YNAB data is relational (categories, groups, recipients)
  - We need to query/filter by recipient assignments
  - Data survives Redis restarts without warm-up
  - Redis is reserved for Celery broker duty
  - PostgreSQL is already in the stack; no need for a separate cache layer
```

### 2.5 Error Handling Strategy

```
Error Categories and Handling:

1. YNAB API Errors
   - 401 Unauthorized → Alert admin (token expired/revoked), serve from cache
   - 429 Rate Limited → Back off, retry with exponential delay, serve from cache
   - 5xx Server Error → Retry up to 3 times, serve from cache
   - Network Timeout → Retry once, serve from cache
   - All failures: log error, serve stale cache data, notify admin if persistent

2. Twilio Errors
   - Invalid phone number → Log error, skip recipient, alert admin
   - Rate limited → Queue and retry
   - Auth error → Alert admin immediately
   - All failures: log to NotificationLog with error details

3. Frontend API Errors
   - 401 → Attempt token refresh, redirect to login if refresh fails
   - 403 → Show "access denied" message
   - 5xx → Show "temporarily unavailable" with retry button
   - Network error → Show offline indicator, retry on reconnect

4. Celery Task Failures
   - All tasks have max_retries=3 with exponential backoff
   - Dead-letter logging for permanently failed tasks
   - Admin notification on repeated failures
```

### 2.6 Logging Strategy

```
Log Levels:
  - INFO:  Successful operations (sync completed, SMS sent, login)
  - WARNING: Degraded operations (serving from stale cache, retry attempts)
  - ERROR: Failed operations (API errors, SMS delivery failure)
  - DEBUG: Detailed data (API responses, calculation details) - dev only

Log Destinations:
  - Console (stdout) — captured by Docker logs
  - Django's built-in logging framework
  - NotificationLog model for SMS audit trail

Structured Logging Format:
  [timestamp] [level] [component] [message] [context]
  2026-02-14T07:00:01 INFO notifications.sms Sent daily notification recipient=sarah status=delivered sid=SM123
  2026-02-14T07:00:02 ERROR ynab.sync Delta sync failed error="429 Too Many Requests" retry_in=60s
```

## 3. Frontend Technical Design

### 3.1 Technology Choices

| Library          | Purpose                        | Justification                        |
|------------------|--------------------------------|--------------------------------------|
| React 19         | UI framework                   | User preference, component model     |
| Vite 6           | Build tool / dev server        | User preference, fast HMR            |
| React Router 7   | Client-side routing            | Standard for React SPAs              |
| Axios            | HTTP client                    | Interceptors for auth token handling |
| Recharts         | Charting (spending trends)     | Simple, React-native, responsive     |
| CSS Modules      | Styling                        | Scoped styles, no extra dependency   |

### 3.2 Route Structure

```
/login              → Login page
/dashboard          → Main category dashboard (default after login)
/trends             → Spending trends / charts
```

### 3.3 State Management

```
Approach: React Context + hooks (no Redux)

AuthContext:
  - user (current recipient info)
  - accessToken (in memory only)
  - login(username, password)
  - logout()
  - refreshToken()

Data Fetching:
  - Custom hooks (useDashboard, useTrends) using useEffect + fetch
  - Loading/error states handled per-component
  - No global state for budget data (fetched fresh on mount)
  - Auto-refresh dashboard data every 5 minutes while tab is active
```

### 3.4 Mobile-First Responsive Design

```
Breakpoints:
  - Mobile: 0 - 768px (primary target)
  - Tablet: 769px - 1024px
  - Desktop: 1025px+

Mobile Layout:
  - Single column, full-width category cards
  - Sticky header with total remaining
  - Touch-friendly tap targets (min 44px)
  - Bottom navigation (Dashboard | Trends)

Desktop Layout:
  - Category cards in 2-column grid
  - Sidebar navigation
  - Wider charts with more data points
```

## 4. Celery Configuration

```python
# config/celery.py configuration

CELERY_BEAT_SCHEDULE = {
    'sync-ynab-data': {
        'task': 'apps.budgets.tasks.sync_ynab_data',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'dispatch-daily-notifications': {
        'task': 'apps.notifications.tasks.dispatch_daily_notifications',
        'schedule': crontab(minute='*'),  # Every minute (checks recipient times)
    },
    'full-sync-daily': {
        'task': 'apps.budgets.tasks.full_sync',
        'schedule': crontab(hour=0, minute=0),  # Midnight full sync
    },
}

CELERY_TASK_ALWAYS_EAGER = False  # True in tests
CELERY_TASK_ACKS_LATE = True      # Re-queue on worker crash
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Prevent memory leaks
```

**Notification Dispatch Logic:**

The `dispatch_daily_notifications` task runs every minute and uses this logic:
```
1. Query all recipients where:
   - notification_time is within the current minute window
   - has not been notified today (last_notified_date < today)
   - is active
2. For each matching recipient:
   a. Build category summary from cache
   b. Format SMS message
   c. Send via Twilio
   d. Log result to NotificationLog
   e. Update last_notified_date
```

## 5. Docker Compose Architecture

```yaml
# Conceptual docker-compose.yml structure

services:
  django:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=postgres://user:pass@postgres:5432/ynab_notifier
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery-worker:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - postgres
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./frontend/dist:/srv/frontend  # Built React static files
```

## 6. Environment Variables

```bash
# Django
DJANGO_SECRET_KEY=           # Django secret key
DJANGO_DEBUG=                # true/false
DJANGO_ALLOWED_HOSTS=        # comma-separated hostnames
DJANGO_SETTINGS_MODULE=      # config.settings.production

# Database
DATABASE_URL=                # postgres://user:pass@host:5432/dbname

# Redis
REDIS_URL=                   # redis://host:6379/0

# YNAB
YNAB_ACCESS_TOKEN=           # Personal access token
YNAB_BUDGET_ID=              # Budget UUID

# Twilio
TWILIO_ACCOUNT_SID=          # Account SID
TWILIO_AUTH_TOKEN=            # Auth token
TWILIO_FROM_NUMBER=           # Twilio phone number (+1XXXXXXXXXX)

# App Config
DEFAULT_NOTIFICATION_TIME=   # HH:MM (24hr format), e.g., "07:00"
FRONTEND_URL=                # https://budget.yourdomain.com
```
