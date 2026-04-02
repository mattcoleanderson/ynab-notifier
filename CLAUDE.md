# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YNAB Budget Notifier — a Django/DRF backend that fetches YNAB budget categories via the YNAB API and sends daily spending summaries to Discord (and optionally SMS via Twilio). Celery Beat triggers the daily notification on a configurable schedule.

## Common Commands

All commands run from the repo root unless noted. The project uses [uv](https://docs.astral.sh/uv/) for Python dependency management and [Taskfile](https://taskfile.dev/) as a task runner.

```bash
# Install/sync dependencies
cd backend && uv sync

# Run tests (from backend/)
cd backend && uv run pytest

# Run a single test file or test
cd backend && uv run pytest apps/notifications/tests/test_discord.py
cd backend && uv run pytest apps/notifications/tests/test_discord.py::test_name

# Watch tests
cd backend && uv run ptw

# Dev server
task backend-runserver

# Django manage.py (any command)
task backend-manage -- <command>

# Migrations
task backend-makemigrations
task backend-migrate
```

## Architecture

- **`backend/config/`** — Django project config: settings, Celery setup, root URL conf. `app_settings.py` provides a type-checkable `settings` import (uses `django-stubs` in dev, `django.conf.settings` at runtime).
- **`backend/apps/notifications/`** — The single Django app containing all business logic.
  - **`services/base.py`** — `NotificationService` ABC with shared `format_message()` that builds an aligned, fixed-width budget summary. `to_dollars()` converts YNAB milliunits to Decimal. Uses `grapheme` for correct emoji-aware string width.
  - **`services/ynab.py`** — `YNABClient` wrapping the `ynab` Python SDK to fetch categories by ID.
  - **`services/discord.py`** — `DiscordService(NotificationService)` — wraps message in a Discord code block and POSTs to a webhook.
  - **`services/sms.py`** — `SMSService(NotificationService)` — sends via Twilio.
  - **`tasks.py`** — Celery `send_daily_notification` task: fetches categories → formats → sends to Discord.
  - **`views.py`** — Two DRF endpoints under `/v1/`: `category/` (fetch categories) and `send/` (trigger a test notification).
  - **`tests/`** — pytest-django tests. `factories.py` has a `make_category()` helper that builds `ynab.Category` objects with sensible defaults.

## Deployment

Docker Compose runs four services: Redis (broker), web (gunicorn), celery-worker, celery-beat. The image is built from `backend/Dockerfile` and published to `ghcr.io/mattcoleanderson/ynab-notifier`. Runtime binaries are invoked directly from the venv (`/app/.venv/bin/...`).

## Environment Variables

Configured in `backend/.env`, loaded via `django-environ`. Key vars: `YNAB_TOKEN`, `BUDGET_ID`, `CATEGORY_IDS` (comma-separated), `DISCORD_WEBHOOK_URL`, `TWILIO_*`, `CELERY_BROKER_URL`, `NOTIFICATION_HOUR`, `NOTIFICATION_MINUTE`.

## Testing Conventions

- pytest with `pytest-django`, `pytest-mock`, `pytest-cov`
- `DJANGO_SETTINGS_MODULE = "config.settings"` (set in pyproject.toml)
- Test fixtures in `conftest.py`; `make_category()` factory for building YNAB `Category` objects
- YNAB amounts are in **milliunits** (e.g., `500000` = $500.00)
