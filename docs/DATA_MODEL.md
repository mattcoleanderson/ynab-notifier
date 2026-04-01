# Data Model & Database Design

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |
| **Database**       | PostgreSQL 16+               |

---

## 1. Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│    Django User       │       │   BudgetConfig      │
│  (auth_user)         │       │   (singleton)       │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ username            │       │ ynab_budget_id      │
│ password (hashed)   │       │ manual_income       │
│ email               │       │   _override         │
│ first_name          │       │ default_notification│
│ last_name           │       │   _time             │
│ is_active           │       │ server_knowledge    │
│ is_staff            │       │ last_synced_at      │
│ ...                 │       └─────────────────────┘
└────────┬────────────┘
         │
         │ 1:1
         ▼
┌─────────────────────┐       ┌─────────────────────┐
│    Recipient         │       │  CachedCategoryGroup│
│  (extends User)      │       ├─────────────────────┤
├─────────────────────┤       │ id (PK)             │
│ id (PK)             │       │ ynab_id (unique)    │
│ user (FK → User)    │       │ name                │
│ phone_number        │       │ is_hidden           │
│ notification_time   │  M:N  │ is_deleted          │
│ notification_enabled│◄─────▶└──────────┬──────────┘
│ last_notified_date  │       ┌──────────┴──────────┐
│ history_months_limit│       │                     │
│ is_active           │       │ 1:N                 │
└────────┬────────────┘       ▼
         │           ┌─────────────────────┐
         │           │  CachedCategory      │
         │           ├─────────────────────┤
         │           │ id (PK)             │
         │           │ ynab_id (unique)    │
         │    M:N    │ group (FK)          │
         └──────────▶│ name                │
                     │ budgeted            │
        (through     │ activity            │
     RecipientCategory│ balance            │
        table)       │ goal_type           │
                     │ goal_target         │
                     │ goal_percentage     │
                     │   _complete         │
                     │ is_hidden           │
                     │ is_deleted          │
                     │ month               │
                     └─────────────────────┘

┌─────────────────────┐
│ RecipientCategory    │
│ (junction table)     │
├─────────────────────┤
│ id (PK)             │
│ recipient (FK)      │
│ category (FK)       │
│ display_order       │
│ unique(recipient,   │
│   category)         │
└─────────────────────┘

┌─────────────────────┐
│ CachedScheduled     │
│   Transaction       │
├─────────────────────┤
│ id (PK)             │
│ ynab_id (unique)    │
│ amount              │
│ frequency           │
│ payee_name          │
│ category_name       │
│ next_date           │
│ is_income           │
│ is_deleted          │
└─────────────────────┘

┌─────────────────────┐
│  NotificationLog     │
├─────────────────────┤
│ id (PK)             │
│ recipient (FK)      │
│ message_type        │
│ twilio_sid          │
│ status              │
│ body_preview        │
│ error_message       │
│ sent_at             │
│ delivered_at        │
└─────────────────────┘

┌─────────────────────┐
│ CategoryMonthHistory │
│ (for trends)         │
├─────────────────────┤
│ id (PK)             │
│ category_ynab_id    │
│ month               │
│ goal_target         │
│ activity            │
│ balance             │
│ unique(category     │
│   _ynab_id, month)  │
└─────────────────────┘
```

## 2. Table Definitions

### 2.1 `Recipient` (accounts app)

Extends Django's built-in User model via a OneToOneField. The User model handles authentication (username, password, email). The Recipient model adds budget-notification-specific fields.

| Column                  | Type         | Constraints                   | Description                                     |
|-------------------------|--------------|-------------------------------|-------------------------------------------------|
| `id`                    | BigAutoField | PK                            | Auto-generated primary key                       |
| `user`                  | ForeignKey   | OneToOne → auth_user, CASCADE | Link to Django User for auth                     |
| `phone_number`          | CharField    | max_length=20, unique         | E.164 format (e.g., +15558675309)               |
| `notification_time`     | TimeField    | nullable                      | Daily SMS time (null = use global default)       |
| `notification_enabled`  | BooleanField | default=True                  | Whether to send daily SMS                        |
| `last_notified_date`    | DateField    | nullable                      | Date of last daily SMS (prevents duplicates)     |
| `history_months_limit`  | PositiveIntegerField | default=3              | Max months of trend data visible to recipient    |
| `is_active`             | BooleanField | default=True                  | Soft delete / disable                            |
| `created_at`            | DateTimeField| auto_now_add                  | Record creation timestamp                        |
| `updated_at`            | DateTimeField| auto_now                      | Record update timestamp                          |

**Indexes:**
- `phone_number` (unique) - for inbound SMS lookup
- `notification_enabled, is_active, last_notified_date` (composite) - for daily dispatch query

---

### 2.2 `BudgetConfig` (budgets app)

Singleton model for global budget configuration. Only one row should exist.

| Column                    | Type              | Constraints         | Description                                        |
|---------------------------|-------------------|---------------------|----------------------------------------------------|
| `id`                      | BigAutoField      | PK                  | Auto-generated primary key                          |
| `ynab_budget_id`          | CharField         | max_length=100      | YNAB budget UUID                                    |
| `manual_income_override`  | BigIntegerField   | nullable            | Manual expected income in milliunits (null = use scheduled txns) |
| `default_notification_time`| TimeField        | default="07:00"     | Global default notification time                    |
| `server_knowledge`        | BigIntegerField   | default=0           | YNAB delta sync cursor                              |
| `last_synced_at`          | DateTimeField     | nullable            | Last successful YNAB sync timestamp                 |
| `updated_at`              | DateTimeField     | auto_now            | Record update timestamp                             |

---

### 2.3 `CachedCategoryGroup` (budgets app)

Local cache of YNAB category groups.

| Column       | Type         | Constraints              | Description                      |
|--------------|--------------|--------------------------|----------------------------------|
| `id`         | BigAutoField | PK                       | Auto-generated primary key       |
| `ynab_id`    | CharField    | max_length=100, unique   | YNAB category group UUID         |
| `name`       | CharField    | max_length=255           | Group name (e.g., "Household")   |
| `is_hidden`  | BooleanField | default=False            | Hidden in YNAB                   |
| `is_deleted` | BooleanField | default=False            | Deleted in YNAB                  |

---

### 2.4 `CachedCategory` (budgets app)

Local cache of YNAB categories with current-month data. This is the primary data source for the dashboard and notifications.

| Column                  | Type            | Constraints                      | Description                                |
|-------------------------|-----------------|----------------------------------|--------------------------------------------|
| `id`                    | BigAutoField    | PK                               | Auto-generated primary key                 |
| `ynab_id`               | CharField       | max_length=100, unique           | YNAB category UUID                         |
| `group`                 | ForeignKey      | → CachedCategoryGroup, CASCADE   | Parent category group                      |
| `name`                  | CharField       | max_length=255                   | Category name (e.g., "Groceries")          |
| `budgeted`              | BigIntegerField | default=0                        | Amount budgeted this month (milliunits)    |
| `activity`              | BigIntegerField | default=0                        | Spending this month (negative, milliunits) |
| `balance`               | BigIntegerField | default=0                        | YNAB balance (milliunits)                  |
| `goal_type`             | CharField       | max_length=50, nullable          | YNAB goal type (TB, TBD, MF, NEED, DEBT)  |
| `goal_target`           | BigIntegerField | nullable                         | Goal target amount (milliunits)            |
| `goal_percentage_complete` | IntegerField | nullable                         | YNAB-reported goal completion %            |
| `is_hidden`             | BooleanField    | default=False                    | Hidden in YNAB                             |
| `is_deleted`            | BooleanField    | default=False                    | Deleted in YNAB                            |
| `month`                 | DateField       | default=current month            | Budget month this data represents          |
| `updated_at`            | DateTimeField   | auto_now                         | Last cache update                          |

**Indexes:**
- `ynab_id` (unique)
- `is_hidden, is_deleted` (composite) - for filtering active categories

**Notes:**
- All amounts are stored in milliunits (YNAB's native format)
- Conversion to display currency happens at the serializer level
- The `month` field tracks which budget month this cached data represents

---

### 2.5 `RecipientCategory` (accounts app)

Junction table linking recipients to their assigned categories.

| Column          | Type         | Constraints                                    | Description                      |
|-----------------|--------------|------------------------------------------------|----------------------------------|
| `id`            | BigAutoField | PK                                             | Auto-generated primary key       |
| `recipient`     | ForeignKey   | → Recipient, CASCADE                           | The recipient                    |
| `category`      | ForeignKey   | → CachedCategory, CASCADE                      | The assigned category            |
| `display_order` | PositiveIntegerField | default=0                              | Order in dashboard and SMS       |

**Constraints:**
- `unique_together: (recipient, category)` - Prevent duplicate assignments

**Indexes:**
- `recipient, display_order` (composite) - for ordered category retrieval

---

### 2.6 `CachedScheduledTransaction` (budgets app)

Local cache of YNAB scheduled transactions, used primarily for income calculation.

| Column          | Type            | Constraints              | Description                                    |
|-----------------|-----------------|--------------------------|------------------------------------------------|
| `id`            | BigAutoField    | PK                       | Auto-generated primary key                     |
| `ynab_id`       | CharField       | max_length=100, unique   | YNAB scheduled transaction UUID                |
| `amount`        | BigIntegerField |                          | Amount in milliunits (positive = income)       |
| `frequency`     | CharField       | max_length=50            | Recurrence (weekly, monthly, etc.)             |
| `payee_name`    | CharField       | max_length=255, nullable | Payee (e.g., employer name)                    |
| `category_name` | CharField       | max_length=255, nullable | Category assigned to                           |
| `next_date`     | DateField       |                          | Next scheduled occurrence                      |
| `is_income`     | BooleanField    | default=False            | Whether this is an income transaction          |
| `is_deleted`    | BooleanField    | default=False            | Deleted in YNAB                                |
| `updated_at`    | DateTimeField   | auto_now                 | Last cache update                              |

**Notes:**
- `is_income` is derived from `amount > 0` (inflows are positive in YNAB)
- Used to calculate expected monthly income when no manual override is set

---

### 2.7 `NotificationLog` (notifications app)

Audit trail of all SMS notifications sent.

| Column          | Type         | Constraints                  | Description                              |
|-----------------|--------------|------------------------------|------------------------------------------|
| `id`            | BigAutoField | PK                           | Auto-generated primary key               |
| `recipient`     | ForeignKey   | → Recipient, CASCADE         | Who the SMS was sent to                  |
| `message_type`  | CharField    | max_length=20                | `"daily"` or `"on_demand"`              |
| `twilio_sid`    | CharField    | max_length=50, nullable      | Twilio Message SID                       |
| `status`        | CharField    | max_length=20                | `queued/sent/delivered/failed/undelivered`|
| `body_preview`  | TextField    |                              | First 160 chars of SMS body              |
| `error_message` | TextField    | nullable                     | Error details if failed                  |
| `sent_at`       | DateTimeField| auto_now_add                 | When the send was attempted              |
| `delivered_at`  | DateTimeField| nullable                     | When Twilio confirmed delivery           |

**Indexes:**
- `recipient, sent_at` (composite) - for delivery history queries
- `status` - for monitoring failed notifications
- `message_type, sent_at` (composite) - for audit filtering

---

### 2.8 `CategoryMonthHistory` (budgets app)

Stores historical monthly category data for spending trends. Populated during YNAB sync.

| Column            | Type            | Constraints                           | Description                          |
|-------------------|-----------------|---------------------------------------|--------------------------------------|
| `id`              | BigAutoField    | PK                                    | Auto-generated primary key           |
| `category_ynab_id`| CharField       | max_length=100                        | YNAB category UUID                   |
| `category_name`   | CharField       | max_length=255                        | Category name (denormalized)         |
| `month`           | DateField       |                                       | Budget month (first of month)        |
| `goal_target`     | BigIntegerField | nullable                              | Goal target for that month           |
| `activity`        | BigIntegerField | default=0                             | Total spending for that month        |
| `balance`         | BigIntegerField | default=0                             | YNAB balance for that month          |

**Constraints:**
- `unique_together: (category_ynab_id, month)` - One record per category per month

**Indexes:**
- `category_ynab_id, month` (composite unique)

---

## 3. Django Model Relationships Summary

```
auth.User  ──── 1:1 ────  Recipient
                              │
                              │ M:N (through RecipientCategory)
                              │
                           CachedCategory  ──── N:1 ────  CachedCategoryGroup
                              │
                              │ (via ynab_id)
                              │
                           CategoryMonthHistory

Recipient  ──── 1:N ────  NotificationLog

BudgetConfig  (standalone singleton)
CachedScheduledTransaction  (standalone, related by YNAB budget context)
```

## 4. Migration Strategy

### Initial Setup
1. `python manage.py migrate` - Creates Django auth tables
2. App migrations create all custom tables
3. `python manage.py createsuperuser` - Creates the admin user
4. First YNAB sync populates `CachedCategoryGroup`, `CachedCategory`, and `CachedScheduledTransaction`
5. Admin creates `BudgetConfig` singleton via Django Admin
6. Admin creates recipients and assigns categories via Django Admin

### Ongoing
- Django's migration framework handles all schema changes
- `makemigrations` → `migrate` workflow
- Data migrations for any required data transformations
- Backward-compatible migrations preferred (add nullable columns, then backfill, then add constraints)

## 5. Data Retention

| Data                         | Retention Policy                                        |
|------------------------------|---------------------------------------------------------|
| `CachedCategory`            | Overwritten on each sync (current month only)           |
| `CategoryMonthHistory`      | Retained indefinitely (small footprint, valuable trends)|
| `NotificationLog`           | Retained 90 days, then auto-purged via Celery task      |
| `CachedScheduledTransaction`| Overwritten on each sync                                |
| `BudgetConfig`              | Permanent (singleton)                                   |
| Recipients & assignments    | Permanent until admin deletes                           |
