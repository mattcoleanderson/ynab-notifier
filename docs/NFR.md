# Non-Functional Requirements (NFR)

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-15                   |

---

## 1. Security

### 1.1 Authentication & Authorization

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-1.1 | Passwords shall be hashed using Django's PBKDF2 (default) or Argon2                              | P0       |
| NFR-1.2 | JWT access tokens shall expire after 15 minutes                                                  | P0       |
| NFR-1.3 | JWT refresh tokens shall expire after 7 days                                                     | P0       |
| NFR-1.4 | Refresh tokens shall be stored in httpOnly, Secure, SameSite=Strict cookies                      | P0       |
| NFR-1.5 | Access tokens shall be stored in memory only (not localStorage/sessionStorage)                    | P0       |
| NFR-1.6 | Login endpoint shall be rate-limited to 5 attempts per minute per IP                              | P1       |
| NFR-1.7 | Account lockout shall activate after 10 consecutive failed login attempts                         | P1       |
| NFR-1.8 | All API endpoints (except auth) shall require valid JWT                                           | P0       |
| NFR-1.9 | Recipients shall only access their own assigned categories (server-side enforcement)              | P0       |
| NFR-1.10| Twilio webhook endpoints shall validate request signatures                                       | P0       |
| NFR-1.11| Django Admin shall require `is_staff=True` and enforce 2FA (future)                              | P1       |

### 1.2 Transport Security

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-1.12| All traffic shall be served over HTTPS (TLS 1.2+)                                                | P0       |
| NFR-1.13| HTTP requests shall be redirected to HTTPS                                                        | P0       |
| NFR-1.14| Caddy shall manage TLS certificates automatically (or Cloudflare Tunnel)                          | P0       |
| NFR-1.15| Internal service communication (Django ↔ Postgres, Django ↔ Redis) may use unencrypted connections within Docker network | P0 |

### 1.3 Data Protection

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-1.16| All secrets (API keys, tokens, passwords) shall be stored as environment variables, never in code | P0       |
| NFR-1.17| `.env` files shall be excluded from version control via `.gitignore`                              | P0       |
| NFR-1.18| CSRF protection shall be enabled on all form-based endpoints                                      | P0       |
| NFR-1.19| CORS shall be restricted to the frontend origin only                                              | P0       |
| NFR-1.20| SQL injection shall be prevented by using Django ORM (no raw SQL)                                 | P0       |
| NFR-1.21| XSS shall be mitigated by React's default output escaping and DRF serializer validation           | P0       |
| NFR-1.22| Django security middleware shall be enabled: `SecurityMiddleware`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security` | P0 |
| NFR-1.23| Phone numbers shall be stored in E.164 format and not exposed to other recipients                 | P0       |

### 1.4 Dependency Security

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-1.24| Python and npm dependencies shall be audited for known vulnerabilities before each release        | P1       |
| NFR-1.25| Dependency lock files (`uv.lock`, `package-lock.json`) shall be committed to version control      | P0       |
| NFR-1.26| Base Docker images shall use specific version tags (not `latest`)                                 | P1       |

---

## 2. Performance

### 2.1 Response Time

| ID      | Requirement                                                              | Target         |
|---------|--------------------------------------------------------------------------|----------------|
| NFR-2.1 | Web portal page load (initial)                                           | < 2 seconds    |
| NFR-2.2 | Dashboard API response (`GET /api/dashboard/`)                           | < 500ms        |
| NFR-2.3 | Trends API response (`GET /api/dashboard/trends/`)                       | < 1 second     |
| NFR-2.4 | Login API response                                                       | < 1 second     |
| NFR-2.5 | Daily SMS delivery (from scheduled time)                                 | < 60 seconds   |
| NFR-2.6 | On-demand SMS response (from inbound to outbound)                        | < 30 seconds   |

### 2.2 Throughput

| ID      | Requirement                                                              | Target         |
|---------|--------------------------------------------------------------------------|----------------|
| NFR-2.7 | Concurrent web portal users                                              | Up to 10       |
| NFR-2.8 | Daily SMS recipients per dispatch cycle                                   | Up to 50       |
| NFR-2.9 | YNAB API calls per sync cycle                                            | < 5            |

### 2.3 YNAB API Efficiency

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-2.10| YNAB data shall be cached locally; the web portal and SMS shall read from cache, not the YNAB API | P0      |
| NFR-2.11| Delta sync (`server_knowledge`) shall be used for all category syncs after the initial full sync  | P1       |
| NFR-2.12| Total YNAB API usage shall stay well below the 200 requests/hour rate limit                       | P0       |
| NFR-2.13| Estimated API usage: ~6 calls/hour (4 syncs × ~1-2 calls each)                                   | P0       |

### 2.4 Frontend Performance

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-2.14| React production build shall be code-split by route                                               | P1       |
| NFR-2.15| Initial JavaScript bundle shall be < 200KB gzipped                                                | P1       |
| NFR-2.16| Images shall be optimized and lazy-loaded                                                         | P2       |
| NFR-2.17| Lighthouse mobile performance score shall be > 80                                                 | P1       |

---

## 3. Availability & Reliability

### 3.1 Uptime

| ID      | Requirement                                                              | Target         |
|---------|--------------------------------------------------------------------------|----------------|
| NFR-3.1 | System uptime (self-hosted)                                              | > 99% monthly  |
| NFR-3.2 | System uptime (cloud-hosted, if migrated)                                | > 99.9% monthly|
| NFR-3.3 | Planned maintenance windows                                              | < 30 min/month |

### 3.2 Fault Tolerance

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-3.4 | YNAB API outage shall not prevent the web portal from functioning (serve from cache)              | P0       |
| NFR-3.5 | YNAB API outage shall not prevent daily SMS (send with last-cached data, note staleness)          | P0       |
| NFR-3.6 | Twilio outage shall be logged; failed SMS shall be retried up to 3 times with exponential backoff | P0       |
| NFR-3.7 | Celery worker crash shall not lose tasks (`acks_late=True`)                                       | P1       |
| NFR-3.8 | Docker containers shall restart automatically on failure (`restart: unless-stopped`)               | P0       |
| NFR-3.9 | PostgreSQL data shall be stored on external SSD (not SD card) for reliability                      | P0       |

### 3.3 Graceful Degradation

```
Scenario: YNAB API is down
  → Web portal shows cached data with "Last updated: X minutes ago" banner
  → Daily SMS sends with cached data, appends "(data may be stale)"
  → Sync retries on next cycle

Scenario: Twilio is down
  → SMS send fails, logged to NotificationLog with error
  → Retried 3 times with backoff
  → Admin alerted after 3 consecutive failures for a recipient
  → Web portal is unaffected

Scenario: Redis is down
  → Celery tasks cannot be dispatched (no SMS, no sync)
  → Web portal still serves cached data from PostgreSQL
  → Docker restarts Redis automatically
  → Tasks resume when Redis recovers

Scenario: Power outage (self-hosted)
  → UPS provides time for graceful shutdown
  → Docker containers restart on boot
  → Celery Beat resumes scheduled tasks
  → Any missed notifications are NOT retroactively sent (avoids spam)
```

---

## 4. Monitoring & Observability

### 4.1 Health Checks

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-4.1 | Django shall expose a `/health/` endpoint returning `200 OK` if the app and database are healthy  | P0       |
| NFR-4.2 | The health endpoint shall verify database connectivity and Redis connectivity                      | P1       |
| NFR-4.3 | External uptime monitor shall check the health endpoint every 5 minutes                           | P1       |

### 4.2 Logging

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-4.4 | All application logs shall go to stdout (captured by Docker)                                      | P0       |
| NFR-4.5 | Log format shall be structured: `[timestamp] [level] [component] [message] [context]`            | P1       |
| NFR-4.6 | All SMS send attempts shall be logged to `NotificationLog` in the database                        | P0       |
| NFR-4.7 | YNAB sync results shall be logged (categories synced, errors, duration)                           | P1       |
| NFR-4.8 | Authentication events (login, logout, failed attempt) shall be logged                             | P0       |
| NFR-4.9 | Docker log rotation shall be configured to prevent disk exhaustion                                 | P1       |

### 4.3 Alerting

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-4.10| Admin shall be alerted (SMS or email) if YNAB sync fails 3 consecutive times                     | P1       |
| NFR-4.11| Admin shall be alerted if SMS delivery fails for a recipient 3 consecutive times                  | P1       |
| NFR-4.12| Admin shall be alerted if the health check fails for > 5 minutes                                 | P1       |

---

## 5. Backup & Recovery

### 5.1 Backup Strategy

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-5.1 | PostgreSQL shall be backed up daily via `pg_dump`                                                 | P0       |
| NFR-5.2 | Backups shall be stored off-site (S3-compatible storage, e.g., Backblaze B2 free tier)            | P1       |
| NFR-5.3 | At least 7 daily backups shall be retained (7-day rolling window)                                 | P1       |
| NFR-5.4 | Backup restoration shall be tested at least once before production deployment                      | P0       |
| NFR-5.5 | Docker Compose file and environment configuration shall be version-controlled (secrets excluded)   | P0       |

### 5.2 Recovery Targets

| Metric                             | Target                                       |
|-------------------------------------|----------------------------------------------|
| **RPO** (Recovery Point Objective)  | < 24 hours (daily backups)                   |
| **RTO** (Recovery Time Objective)   | < 1 hour (restore from backup + redeploy)    |

### 5.3 Recovery Procedure (High-Level)

```
1. Restore PostgreSQL from latest backup:
   pg_restore -d ynab_notifier < backup_YYYY-MM-DD.dump

2. Rebuild Docker containers:
   docker compose up -d --build

3. Run migrations (if needed):
   docker compose exec django python manage.py migrate

4. Verify health endpoint:
   curl https://budget.yourdomain.com/health/

5. Verify YNAB sync runs:
   Check Django logs for successful sync

6. Verify SMS delivery:
   Send a test notification via Django Admin
```

---

## 6. Scalability

### 6.1 Current Scale

This application is designed for household use. Expected scale:

| Dimension                | Expected Load           |
|--------------------------|-------------------------|
| Recipients               | 1-10                    |
| Categories per recipient | 3-15                    |
| Daily SMS messages       | 1-10                    |
| Concurrent portal users  | 1-3                     |
| YNAB API calls/hour      | < 10                    |
| Database size             | < 100MB                 |

### 6.2 Scalability Considerations

The architecture is designed so that scaling up is possible but not over-engineered for current needs:

| Component       | Current                  | If Scaling Needed                          |
|-----------------|--------------------------|---------------------------------------------|
| Django          | 1 Gunicorn instance      | Add workers, or horizontal with load balancer|
| Celery          | 1 worker                 | Add workers                                  |
| PostgreSQL      | Single instance           | Managed RDS, read replicas                   |
| Redis           | Single instance           | Managed ElastiCache                          |
| Frontend        | Static files via Caddy    | CDN (Cloudflare already provides this)       |

---

## 7. Compatibility

### 7.1 Browser Support

| Browser            | Version     | Support Level |
|--------------------|-------------|---------------|
| Chrome (Mobile)    | Last 2      | Full          |
| Safari (iOS)       | Last 2      | Full          |
| Chrome (Desktop)   | Last 2      | Full          |
| Firefox (Desktop)  | Last 2      | Full          |
| Safari (Desktop)   | Last 2      | Full          |
| Edge               | Last 2      | Full          |
| IE 11              | -           | Not supported |

### 7.2 Mobile Device Support

| Aspect             | Requirement                                          |
|--------------------|------------------------------------------------------|
| Minimum width      | 320px (iPhone SE)                                    |
| Touch targets      | Minimum 44x44px per Apple HIG                        |
| Orientation        | Portrait primary, landscape supported                |
| Offline            | Show "offline" indicator, no offline functionality    |

---

## 8. Development & Operations

### 8.1 Development Environment

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-8.1 | Local development shall use Docker Compose to match production                                    | P0       |
| NFR-8.2 | Hot-reload shall work for both Django (runserver) and React (Vite HMR)                            | P0       |
| NFR-8.3 | A `.env.example` file shall document all required environment variables                           | P0       |
| NFR-8.4 | Python code shall follow PEP 8 (enforced via linter)                                             | P1       |
| NFR-8.5 | Frontend code shall follow ESLint recommended rules                                               | P1       |

### 8.2 Testing

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-8.6 | Backend shall have unit tests for: forecasting engine, message formatting, YNAB data parsing      | P1       |
| NFR-8.7 | Backend shall have integration tests for: API endpoints, authentication flow                      | P1       |
| NFR-8.8 | Celery tasks shall be testable with `CELERY_TASK_ALWAYS_EAGER=True`                               | P1       |
| NFR-8.9 | Frontend shall have component tests for: dashboard, category card, progress bar                   | P2       |
| NFR-8.10| Tests shall run in CI before merge (future, when CI is set up)                                    | P2       |

### 8.3 Version Control

| ID      | Requirement                                                                                      | Priority |
|---------|--------------------------------------------------------------------------------------------------|----------|
| NFR-8.11| All code shall be in a single Git repository (monorepo: backend + frontend)                       | P0       |
| NFR-8.12| Main branch shall always be deployable                                                            | P0       |
| NFR-8.13| Feature branches for non-trivial changes                                                          | P1       |
| NFR-8.14| Meaningful commit messages                                                                        | P0       |
