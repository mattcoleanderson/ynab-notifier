# High-Level Design (HLD)

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |

---


## 1. System Overview

The YNAB Budget Notifier & Portal is a three-tier application consisting of a React frontend, Django/DRF backend, and PostgreSQL database. It integrates with the YNAB API (read-only) for budget data and Twilio for SMS delivery.

### 1.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                              │
│                                                                             │
│   ┌──────────────┐                              ┌─────────────────┐         │
│   │   YNAB API   │                              │   Twilio API    │         │
│   │  (REST/HTTPS)│                              │ (SMS Gateway)   │         │
│   └──────┬───────┘                              └────────┬────────┘         │
│          │                                               │                  │
│          │ Scheduled Sync                    Send SMS /  │  Inbound         │
│          │ + On-Demand                       Webhook     │  Webhook         │
│          │                                               │                  │
└──────────┼───────────────────────────────────────────────┼──────────────────┘
           │                                               │
┌──────────┼───────────────────────────────────────────────┼──────────────────┐
│          ▼                                               ▼                  │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                     DJANGO / DRF BACKEND                        │       │
│   │                                                                 │       │
│   │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐     │       │
│   │  │ YNAB Service │  │ Notification │  │   REST API        │     │       │
│   │  │   Layer      │  │   Service    │  │   (DRF Views)     │     │       │
│   │  │              │  │   (Twilio)   │  │                   │     │       │
│   │  │ - Fetch cats │  │ - Send SMS   │  │ - Auth endpoints  │     │       │
│   │  │ - Fetch sched│  │ - Webhook    │  │ - Category data   │     │       │
│   │  │ - Calc remain│  │   handler    │  │ - Dashboard data  │     │       │
│   │  │ - Delta sync │  │ - Format msg │  │ - Trends data     │     │       │
│   │  └──────┬───────┘  └──────────────┘  └─────────┬─────────┘     │       │
│   │         │                                      │               │       │
│   │  ┌──────┴──────────────────────────────────────┴───────┐       │       │
│   │  │              Forecasting Engine                      │       │       │
│   │  │  remaining = goal_target + activity                  │       │       │
│   │  │  expected_income = scheduled_txns OR manual_override │       │       │
│   │  └──────────────────────┬──────────────────────────────┘       │       │
│   │                         │                                      │       │
│   │  ┌──────────────────────┴──────────────────────────────┐       │       │
│   │  │             Celery Task Queue                        │       │       │
│   │  │  - Daily notification dispatch                       │       │       │
│   │  │  - YNAB data sync (periodic)                         │       │       │
│   │  │  - On-demand SMS processing                          │       │       │
│   │  └─────────────────────────────────────────────────────┘       │       │
│   │                                                                 │       │
│   │  ┌──────────────────┐                                          │       │
│   │  │  Django Admin     │  (Budget owner manages recipients,      │       │
│   │  │  (Admin Panel)    │   categories, income overrides)         │       │
│   │  └──────────────────┘                                          │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│          │                            ▲                                     │
│          ▼                            │                                     │
│   ┌──────────────┐             ┌──────┴───────────────────────────┐        │
│   │  PostgreSQL   │             │     React Frontend (Vite)       │        │
│   │  Database     │             │                                 │        │
│   │              │             │  - Login page                   │        │
│   │  - Recipients │             │  - Category dashboard           │        │
│   │  - Categories │             │  - Progress bars                │        │
│   │  - YNAB Cache │             │  - Spending trends              │        │
│   │  - Notif logs │             │  - Mobile-first                 │        │
│   └──────────────┘             └─────────────────────────────────┘        │
│                                                                             │
│   ┌──────────────┐                                                         │
│   │    Redis      │  (Celery message broker)                               │
│   └──────────────┘                                                         │
│                                                                             │
│                           APPLICATION SERVER                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Technology Stack

| Layer              | Technology                 | Version   | Justification                                       |
|--------------------|----------------------------|-----------|------------------------------------------------------|
| **Frontend**       | React (JavaScript, no TS)  | 19.x      | Familiar component model, large ecosystem            |
| **Build Tool**     | Vite                       | 6.x       | Fast dev server, HMR, optimized builds               |
| **Backend**        | Django                     | 5.x       | Mature, batteries-included, great admin panel        |
| **API Framework**  | Django REST Framework      | 3.x       | Industry standard for Django REST APIs               |
| **Database**       | PostgreSQL                 | 16+       | Robust, production-grade, JSON support               |
| **Task Queue**     | Celery                     | 5.x       | Distributed task queue, cron-like scheduling          |
| **Message Broker** | Redis                      | 7.x       | Fast, lightweight broker for Celery                  |
| **SMS Provider**   | Twilio                     | -         | Industry standard SMS API, Python SDK                |
| **YNAB SDK**       | ynab (Python)              | 1.9+      | Official YNAB Python SDK                             |
| **Reverse Proxy**  | Caddy                      | 2.x       | Automatic HTTPS, simple config, HTTP/2               |
| **Containerization**| Docker + Docker Compose   | -         | Reproducible deployments, easy orchestration         |

## 3. Component Descriptions

### 3.1 YNAB Service Layer

**Responsibility:** All communication with the YNAB API.

- Authenticates with YNAB personal access token
- Fetches categories with balances, goals, and activity for the current month
- Fetches scheduled transactions to calculate expected income
- Implements delta sync using `server_knowledge` to minimize API calls
- Caches all YNAB data in PostgreSQL
- Exposes internal Python API consumed by the Forecasting Engine and REST API

**YNAB API Endpoints Used:**
| Endpoint                                            | Purpose                              |
|-----------------------------------------------------|--------------------------------------|
| `GET /budgets/{id}/categories`                      | All categories with current balances |
| `GET /budgets/{id}/months/{month}`                  | Monthly category details             |
| `GET /budgets/{id}/months/{month}/categories/{id}`  | Single category for a month          |
| `GET /budgets/{id}/scheduled_transactions`          | Expected income sources              |

### 3.2 Forecasting Engine

**Responsibility:** Calculate "remaining" amounts based on expected income, not just current balance.

**Core Calculation:**
```
For each category assigned to a recipient:
    if category.goal_target exists:
        remaining = (goal_target + activity) / 1000   # milliunits to dollars
    else:
        remaining = balance / 1000                      # fallback to YNAB balance

Expected Monthly Income:
    if manual_override is set:
        expected_income = manual_override
    else:
        expected_income = sum(scheduled_income_transactions for current month)
```

**Key Difference from YNAB:**
- YNAB `balance` = `budgeted + activity` (only money already assigned)
- This app's `remaining` = `goal_target + activity` (assumes full month funding will happen)

### 3.3 Notification Service

**Responsibility:** Format and deliver SMS messages via Twilio.

- Formats category remaining amounts into the SMS template
- Sends daily scheduled notifications per recipient at their configured time
- Handles inbound SMS webhooks for on-demand requests
- Logs all notification attempts and delivery status
- Uses Celery for async dispatch and scheduling

### 3.4 REST API (DRF)

**Responsibility:** Serve the React frontend with budget data.

- Authentication endpoints (login, logout, token refresh)
- Dashboard data endpoint (filtered categories for the authenticated recipient)
- Spending trends endpoint (historical data with admin-configured depth limit)
- All responses are JSON, CORS-enabled for the frontend origin

### 3.5 React Frontend

**Responsibility:** Mobile-first web portal for recipients.

- Single-page application built with Vite
- Login page with username/password
- Dashboard view with category cards, progress bars, and total remaining
- Spending trends view with charts
- Responsive design, optimized for mobile viewports
- Communicates exclusively with the DRF backend API

### 3.6 Django Admin

**Responsibility:** Admin interface for the budget owner.

- Manage recipients (CRUD)
- Assign/unassign categories per recipient
- Configure notification times (per-recipient and global default)
- Set manual income override
- View notification delivery logs
- No custom admin panel needed - Django Admin with customized ModelAdmin classes

### 3.7 Celery + Redis

**Responsibility:** Background task execution and scheduling.

- **Celery Beat** schedules periodic tasks:
  - YNAB data sync (every 15-30 minutes)
  - Daily notification dispatch (checks each recipient's configured time)
- **Celery Workers** execute tasks:
  - Send SMS via Twilio
  - Fetch and cache YNAB data
  - Process inbound SMS webhooks
- **Redis** acts as the message broker between Django and Celery

## 4. Data Flow Diagrams

### 4.1 Daily Notification Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Celery   │     │ Notification │     │ Forecasting  │     │ YNAB     │
│ Beat     │────▶│ Service      │────▶│ Engine       │────▶│ Cache    │
│ (cron)   │     │              │     │              │     │ (DB)     │
└─────────┘     └──────┬───────┘     └──────────────┘     └──────────┘
                       │
                       │ For each recipient whose
                       │ notification time has arrived:
                       ▼
                ┌──────────────┐     ┌──────────────┐
                │ Format SMS   │────▶│ Twilio API   │────▶ Recipient's Phone
                │ Message      │     │ (Send SMS)   │
                └──────────────┘     └──────────────┘
```

### 4.2 Web Portal Data Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ React    │     │ DRF API      │     │ Forecasting  │     │ YNAB     │
│ Frontend │────▶│ View         │────▶│ Engine       │────▶│ Cache    │
│          │◀────│              │◀────│              │     │ (DB)     │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
     │
     │ JWT Token in
     │ Authorization header
     ▼
  User's Browser (mobile)
```

### 4.3 On-Demand SMS Flow

```
Recipient's Phone
     │
     │ Texts "UPDATE"
     ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Twilio   │     │ Django       │     │ Notification │     │ YNAB     │
│ Webhook  │────▶│ Webhook View │────▶│ Service      │────▶│ Service  │
│          │     │              │     │              │     │ (fresh)  │
└──────────┘     └──────────────┘     └──────┬───────┘     └──────────┘
                                             │
                                             │ Fresh data fetch +
                                             │ format + send
                                             ▼
                                      ┌──────────────┐
                                      │ Twilio API   │────▶ Recipient's Phone
                                      │ (Reply SMS)  │
                                      └──────────────┘
```

### 4.4 YNAB Data Sync Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Celery   │     │ YNAB Service │     │ YNAB API     │     │ Postgres │
│ Beat     │────▶│ Layer        │────▶│ (Delta Req)  │     │ Database │
│ (15 min) │     │              │◀────│              │     │          │
└─────────┘     └──────┬───────┘     └──────────────┘     └──────────┘
                       │
                       │ Upsert changed
                       │ categories
                       ▼
                ┌──────────────┐
                │ Update Cache │
                │ + server_    │
                │ knowledge    │
                └──────────────┘
```

## 5. Deployment Architecture

### 5.1 Option A: Self-Hosted (Raspberry Pi 5) - RECOMMENDED

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5 (8GB)                  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Docker Compose                        │  │
│  │                                                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ Caddy    │ │ Django   │ │ Celery Worker    │  │  │
│  │  │ (reverse │ │ (gunicorn│ │ + Celery Beat    │  │  │
│  │  │  proxy)  │ │  :8000)  │ │                  │  │  │
│  │  └────┬─────┘ └──────────┘ └──────────────────┘  │  │
│  │       │                                           │  │
│  │  ┌────┴─────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ React    │ │PostgreSQL│ │ Redis            │  │  │
│  │  │ (static  │ │ :5432    │ │ :6379            │  │  │
│  │  │  files)  │ │          │ │                  │  │  │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  External SSD (USB 3.0) ← PostgreSQL data + backups     │
└─────────────────────────────────────────────────────────┘
           │
           │ Cloudflare Tunnel (no port forwarding needed)
           ▼
┌─────────────────────┐
│   Cloudflare Edge   │ ← Free SSL, DDoS protection, CDN
│   budget.yourdomain │
└─────────────────────┘
```

**Pros:**
- Zero ongoing cost (electricity only)
- Full control over data and infrastructure
- RPi5 has ample power for this workload (8GB RAM, quad-core ARM)
- Great learning experience
- Cloudflare Tunnel eliminates port forwarding and provides free SSL
- Docker Compose makes deployment reproducible

**Cons:**
- Reliability depends on home network/power (mitigated with UPS)
- SD card failure risk (mitigated by booting from external SSD)
- Manual PostgreSQL backup management (automate to cloud storage)
- ISP outages affect availability
- No managed scaling (not needed for < 10 users)

**Mitigations:**
- Use external SSD via USB 3.0 instead of SD card for all data
- Set up automated PostgreSQL backups to S3-compatible storage (Backblaze B2 free tier)
- Use a small UPS for graceful shutdown on power loss
- Cloudflare Tunnel reconnects automatically after network interruptions
- Monitor with Uptime Kuma (self-hosted) or free external monitor

### 5.2 Option B: AWS

```
┌─────────────────────────────────────────────────────────┐
│                        AWS VPC                           │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────────────────┐│
│  │ ALB              │  │ ECS Fargate                   ││
│  │ (Load Balancer)  │  │                               ││
│  │ + ACM (SSL)      │──│  ┌────────┐  ┌────────────┐  ││
│  │                  │  │  │ Django  │  │ Celery     │  ││
│  └──────────────────┘  │  │ + React │  │ Worker +   │  ││
│                        │  │ (static)│  │ Beat       │  ││
│                        │  └────────┘  └────────────┘  ││
│                        └──────────────────────────────┘│
│                                                         │
│  ┌──────────────────┐  ┌──────────────────────────────┐│
│  │ RDS PostgreSQL   │  │ ElastiCache Redis            ││
│  │ (db.t3.micro)    │  │ (cache.t3.micro)             ││
│  └──────────────────┘  └──────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- High reliability (99.9%+ uptime SLAs)
- Managed PostgreSQL (automatic backups, patching, failover)
- Managed Redis (ElastiCache)
- Professional monitoring (CloudWatch)
- Auto-scaling capability (not needed now, but available)
- AWS experience is career-valuable

**Cons:**
- Estimated monthly cost: **$40-80/month**
  - ECS Fargate: ~$15-25 (0.25 vCPU, 0.5GB per container)
  - RDS db.t3.micro: ~$15-20
  - ElastiCache cache.t3.micro: ~$12
  - ALB: ~$16 (fixed + LCU)
  - Data transfer: ~$1-2
- Overkill for a personal project with < 10 users
- More complex infrastructure (IAM, VPC, security groups)
- Potential for billing surprises

**When to Choose AWS:**
- If uptime is critical and you don't want to manage infrastructure
- If you want to practice AWS skills for professional development
- If the project grows beyond personal/household use

### 5.3 Recommendation

**Self-hosted on Raspberry Pi 5** is the recommended deployment target for this project.

The user base is small (< 10 household members), the budget owner is technical, and the RPi5 has more than enough power. The cost savings are significant ($0/month vs $40-80/month), and the learning experience of running your own infrastructure is valuable. Cloudflare Tunnel solves the biggest pain points of self-hosting (SSL, port forwarding, DDoS).

The architecture should be Docker Compose-based so that migrating to AWS (or any cloud) later is straightforward - just change the `docker-compose.yml` and point at managed services.

## 6. Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Security Layers                    │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ 1. Transport: HTTPS everywhere                │  │
│  │    - Caddy auto-TLS (self-hosted)             │  │
│  │    - Cloudflare Tunnel (encrypted)            │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ 2. Authentication                             │  │
│  │    - Recipients: JWT (access + refresh)       │  │
│  │    - Admin: Django session auth               │  │
│  │    - Twilio webhooks: request signature       │  │
│  │      validation                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ 3. Authorization                              │  │
│  │    - Recipients see ONLY their assigned       │  │
│  │      categories (enforced server-side)        │  │
│  │    - Admin has full access via Django Admin    │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ 4. Secrets Management                         │  │
│  │    - All secrets in environment variables     │  │
│  │    - .env file excluded from version control  │  │
│  │    - YNAB token, Twilio creds, Django secret  │  │
│  │      key, DB password                         │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ 5. Data Protection                            │  │
│  │    - Passwords hashed with Django's PBKDF2    │  │
│  │    - CSRF protection on all forms             │  │
│  │    - CORS restricted to frontend origin       │  │
│  │    - SQL injection prevented by ORM           │  │
│  │    - XSS prevented by React's default         │  │
│  │      escaping + DRF serializers               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 7. Integration Points

### 7.1 YNAB API

| Aspect             | Detail                                                   |
|--------------------|----------------------------------------------------------|
| **Protocol**       | REST over HTTPS                                          |
| **Auth**           | Bearer token (personal access token)                     |
| **Base URL**       | `https://api.ynab.com/v1`                                |
| **Rate Limit**     | 200 requests/hour per token                              |
| **Data Format**    | JSON, amounts in milliunits                              |
| **Sync Strategy**  | Delta requests with `server_knowledge`                   |
| **Failure Mode**   | Serve from cache on API failure; retry on next cycle     |

### 7.2 Twilio

| Aspect             | Detail                                                   |
|--------------------|----------------------------------------------------------|
| **Protocol**       | REST over HTTPS                                          |
| **Auth**           | Account SID + Auth Token                                 |
| **Outbound**       | `client.messages.create()` via Python SDK                |
| **Inbound**        | Webhook POST to Django endpoint                          |
| **Validation**     | Twilio request signature validation on webhooks          |
| **Failure Mode**   | Log failure, retry once, alert admin on repeated failure |
