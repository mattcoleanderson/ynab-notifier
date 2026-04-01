# Phasing & Roadmap

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |

---

## Overview

The project is divided into 4 phases, each delivering a usable increment of functionality. Each phase builds on the previous and can be deployed independently.

```
Phase 1          Phase 2          Phase 3          Phase 4
──────────       ──────────       ──────────       ──────────
Core Backend  →  Web Portal    →  Enhanced UX   →  Polish &
& SMS Notifs     (React)          & Features       Operations
```

---

## Phase 1: Core Backend & SMS Notifications (MVP)

> **Goal:** A working system that sends daily budget texts to recipients.

### Deliverables

| #   | Deliverable                                      | Details                                              |
|-----|--------------------------------------------------|------------------------------------------------------|
| 1.1 | Django project scaffolding                       | Project structure, settings (dev/prod), Docker setup  |
| 1.2 | PostgreSQL database setup                        | Docker container, initial migrations                  |
| 1.3 | YNAB API integration                             | `ynab_client.py` - fetch categories, scheduled txns  |
| 1.4 | Data models & migrations                         | All models from DATA_MODEL.md (Phase 1 subset)       |
| 1.5 | YNAB data sync service                           | Full sync + delta sync with `server_knowledge`        |
| 1.6 | Forecasting engine                               | `remaining = goal_target + activity` calculation      |
| 1.7 | Expected income calculation                      | From scheduled transactions + manual override         |
| 1.8 | Recipient & category management (Django Admin)   | Admin CRUD for recipients, category assignments       |
| 1.9 | SMS notification service (Twilio)                | Send formatted SMS via Twilio Python SDK              |
| 1.10| Celery + Redis setup                             | Worker, Beat, periodic tasks                          |
| 1.11| Daily notification dispatch                      | Celery Beat task, per-recipient timing                |
| 1.12| Docker Compose (dev)                             | Django + Postgres + Redis + Celery                    |
| 1.13| Basic deployment                                 | Docker Compose on RPi5 or local dev                   |
| 1.14| BudgetConfig singleton                           | Django Admin managed global config                    |

### Models Required
- `BudgetConfig`
- `CachedCategoryGroup`
- `CachedCategory`
- `CachedScheduledTransaction`
- `Recipient`
- `RecipientCategory`
- `NotificationLog`

### Definition of Done
- [ ] Admin can create a recipient with phone number and assigned categories via Django Admin
- [ ] System fetches YNAB categories and scheduled transactions on a 15-minute schedule
- [ ] Daily SMS is sent to each active recipient at their configured time
- [ ] SMS contains filtered category remaining amounts and total
- [ ] SMS format matches the template in the PRD
- [ ] Notification attempts are logged in `NotificationLog`
- [ ] Manual income override works when configured
- [ ] All services run via Docker Compose

### Key Risks
- YNAB API rate limiting (200 req/hr) - mitigated by caching + delta sync
- Twilio phone number provisioning and verification

---

## Phase 2: Web Portal (React Frontend)

> **Goal:** Recipients can log into a web dashboard to see their budget categories.

### Deliverables

| #   | Deliverable                                      | Details                                              |
|-----|--------------------------------------------------|------------------------------------------------------|
| 2.1 | React + Vite project scaffolding                 | No TypeScript, CSS Modules, project structure         |
| 2.2 | JWT authentication (backend)                     | Login, logout, refresh endpoints in DRF              |
| 2.3 | Login page (frontend)                            | Username/password form, error handling                |
| 2.4 | Auth context & hooks (frontend)                  | Token storage, auto-refresh, protected routes         |
| 2.5 | Dashboard API endpoint                           | `GET /api/dashboard/` - filtered categories          |
| 2.6 | Dashboard page (frontend)                        | Category cards, remaining amounts, total              |
| 2.7 | Progress bars                                    | Visual goal completion per category                   |
| 2.8 | Mobile-first responsive layout                   | Single-column mobile, 2-column desktop                |
| 2.9 | CORS configuration                               | Allow frontend origin                                 |
| 2.10| Caddy reverse proxy setup                        | Serve frontend static files + proxy API               |
| 2.11| Cloudflare Tunnel setup                          | External access with free SSL                         |
| 2.12| Production Docker Compose                        | All services including Caddy, static files            |

### Models Required (additions)
- No new models. Phase 1 models are sufficient.
- Minor addition: `Recipient.user` populated with Django User for auth

### Definition of Done
- [ ] Recipient can log in with username/password
- [ ] Dashboard shows only the recipient's assigned categories
- [ ] Each category shows: name, remaining amount, goal target, amount spent, progress bar
- [ ] Total remaining is displayed at top of dashboard
- [ ] Layout is mobile-first and responsive
- [ ] Access tokens auto-refresh without user intervention
- [ ] Application is accessible via HTTPS at a custom domain
- [ ] Unauthorized users are redirected to login
- [ ] A recipient cannot see another recipient's categories

### Key Risks
- CORS misconfiguration between frontend and backend
- JWT token refresh flow complexity
- Responsive CSS across various mobile devices

---

## Phase 3: Enhanced UX & Features

> **Goal:** Add on-demand SMS, spending trends, and polish the experience.

### Deliverables

| #   | Deliverable                                      | Details                                              |
|-----|--------------------------------------------------|------------------------------------------------------|
| 3.1 | On-demand SMS (inbound webhook)                  | Twilio webhook, keyword detection, fresh data fetch  |
| 3.2 | Spending trends API endpoint                     | `GET /api/dashboard/trends/` with month history      |
| 3.3 | Spending trends page (frontend)                  | Charts using Recharts, per-category history           |
| 3.4 | Admin-configurable history depth                 | `history_months_limit` per recipient, enforced        |
| 3.5 | `CategoryMonthHistory` population                | Sync historical month data from YNAB                  |
| 3.6 | Twilio webhook signature validation              | Security hardening on inbound endpoints               |
| 3.7 | Notification delivery status tracking            | Twilio status webhook, update `NotificationLog`       |
| 3.8 | Auto-refresh dashboard data                      | Poll every 5 minutes while tab is active              |
| 3.9 | Improved error handling (frontend)               | Loading states, error messages, offline indicator      |
| 3.10| Notification history in Django Admin             | List view with filters for delivery status            |

### Models Required (additions)
- `CategoryMonthHistory` (new)

### Definition of Done
- [ ] Recipient can text "UPDATE" and receive a fresh budget summary within 30 seconds
- [ ] Unrecognized phone numbers and keywords are silently ignored (no error SMS)
- [ ] Spending trends page shows historical data for assigned categories
- [ ] Trends respect the admin-configured history depth per recipient
- [ ] Charts are responsive and readable on mobile
- [ ] Dashboard auto-refreshes without manual page reload
- [ ] Twilio webhook requests are validated via signature
- [ ] Notification delivery status is tracked and visible in Django Admin
- [ ] Loading and error states are handled gracefully in the frontend

### Key Risks
- Twilio webhook reliability and timeout constraints (15-second limit)
- Historical YNAB data availability (API may not have unlimited history)
- Chart performance on mobile with large datasets

---

## Phase 4: Polish & Operations

> **Goal:** Production hardening, monitoring, backups, and security upgrades.

### Deliverables

| #   | Deliverable                                      | Details                                              |
|-----|--------------------------------------------------|------------------------------------------------------|
| 4.1 | Magic link authentication                        | SMS-based passwordless login as upgrade option         |
| 4.2 | Automated PostgreSQL backups                     | Cron job to backup to S3-compatible storage            |
| 4.3 | Uptime monitoring                                | Self-hosted Uptime Kuma or external monitor            |
| 4.4 | Log aggregation                                  | Structured logging, Docker log management              |
| 4.5 | Admin alerting                                   | SMS/email alert on sync failures, SMS delivery issues  |
| 4.6 | NotificationLog auto-purge                       | Celery task to clean logs older than 90 days           |
| 4.7 | Rate limiting on auth endpoints                  | django-ratelimit or DRF throttling                     |
| 4.8 | Account lockout                                  | Lock after N failed login attempts                     |
| 4.9 | Security audit                                   | OWASP checklist, dependency vulnerability scan          |
| 4.10| Performance optimization                         | Database query optimization, frontend bundle size      |
| 4.11| Documentation                                    | README, setup guide, runbook                           |
| 4.12| UPS integration (self-hosted)                    | Graceful shutdown on power loss                        |

### Definition of Done
- [ ] Magic link login works as an alternative to username/password
- [ ] PostgreSQL backups run daily to off-site storage
- [ ] Uptime monitoring alerts admin when the service is down
- [ ] Notification logs older than 90 days are automatically purged
- [ ] Auth endpoints have rate limiting and account lockout
- [ ] All dependencies are scanned for known vulnerabilities
- [ ] A setup guide exists for fresh deployment
- [ ] System has been running stable for 2+ weeks in production

### Key Risks
- Magic link SMS delivery reliability (circular dependency if Twilio is also the auth channel)
- Backup restoration testing

---

## Phase Dependency Graph

```
Phase 1 (MVP)
  │
  ├── All backend infrastructure
  ├── YNAB integration
  ├── SMS notifications
  └── Django Admin
        │
        ▼
Phase 2 (Web Portal)
  │
  ├── React frontend
  ├── JWT authentication
  ├── Dashboard
  └── Production deployment
        │
        ▼
Phase 3 (Enhanced Features)
  │
  ├── On-demand SMS
  ├── Spending trends
  └── Status tracking
        │
        ▼
Phase 4 (Operations)
  │
  ├── Magic link auth
  ├── Monitoring & backups
  └── Security hardening
```

---

## Priority Matrix

| Feature                     | Impact | Effort | Phase |
|-----------------------------|--------|--------|-------|
| Daily SMS notifications     | High   | Medium | 1     |
| YNAB data sync              | High   | Medium | 1     |
| Forecasting engine          | High   | Low    | 1     |
| Django Admin management     | High   | Low    | 1     |
| Web portal (dashboard)      | High   | Medium | 2     |
| JWT authentication          | High   | Medium | 2     |
| Progress bars               | Medium | Low    | 2     |
| On-demand SMS               | Medium | Medium | 3     |
| Spending trends/charts      | Medium | Medium | 3     |
| Magic link auth             | Low    | Medium | 4     |
| Automated backups           | Medium | Low    | 4     |
| Uptime monitoring           | Medium | Low    | 4     |
