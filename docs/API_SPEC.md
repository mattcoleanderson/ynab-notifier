# API Specification Document

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |
| **Base URL**       | `https://budget.yourdomain.com/api` |

---

## 1. Overview

This document specifies the REST API served by the Django/DRF backend, consumed by the React frontend. All endpoints return JSON. Authentication uses JWT bearer tokens.

### 1.1 Common Headers

**Request:**
```
Content-Type: application/json
Authorization: Bearer <access_token>     # Required for protected endpoints
```

**Response:**
```
Content-Type: application/json
```

### 1.2 Common Error Response Format

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "The username or password is incorrect.",
    "details": {}
  }
}
```

### 1.3 Standard Error Codes

| HTTP Status | Code                     | Description                              |
|-------------|--------------------------|------------------------------------------|
| 400         | `VALIDATION_ERROR`       | Request body failed validation           |
| 401         | `AUTHENTICATION_REQUIRED`| Missing or invalid access token          |
| 401         | `TOKEN_EXPIRED`          | Access token has expired                 |
| 401         | `INVALID_CREDENTIALS`    | Bad username/password                    |
| 403         | `PERMISSION_DENIED`      | Authenticated but not authorized         |
| 404         | `NOT_FOUND`              | Resource not found                       |
| 429         | `RATE_LIMITED`            | Too many requests                        |
| 500         | `INTERNAL_ERROR`         | Unexpected server error                  |

---

## 2. Authentication Endpoints

### 2.1 Login

Authenticate a recipient and receive JWT tokens.

```
POST /api/auth/login/
```

**Request Body:**
```json
{
  "username": "sarah",
  "password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "sarah",
    "first_name": "Sarah",
    "last_name": "Anderson"
  }
}
```

**Notes:**
- The `refresh_token` is set as an `httpOnly`, `Secure`, `SameSite=Strict` cookie (not in the response body)
- Access token expires in 15 minutes
- Rate limited: 5 attempts per minute per IP

**Error Responses:**
- `401 INVALID_CREDENTIALS` - Bad username or password
- `429 RATE_LIMITED` - Too many login attempts

---

### 2.2 Token Refresh

Refresh an expired access token using the refresh token cookie.

```
POST /api/auth/refresh/
```

**Request Body:** None (refresh token is read from httpOnly cookie)

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses:**
- `401 TOKEN_EXPIRED` - Refresh token has expired (7-day lifetime). User must re-login.

---

### 2.3 Logout

Invalidate the current session and clear the refresh token cookie.

```
POST /api/auth/logout/
```

**Request Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "message": "Logged out successfully."
}
```

**Notes:**
- Clears the refresh token cookie
- Optionally blacklists the refresh token server-side

---

## 3. Dashboard Endpoints

### 3.1 Get Dashboard Data

Returns the authenticated recipient's assigned categories with remaining amounts, goal progress, and totals.

```
GET /api/dashboard/
```

**Request Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "data": {
    "recipient": {
      "id": 1,
      "first_name": "Sarah"
    },
    "month": "2026-02",
    "expected_income": 6000.00,
    "income_source": "scheduled_transactions",
    "last_synced": "2026-02-14T06:45:00Z",
    "total_remaining": 403.80,
    "categories": [
      {
        "id": "2ef6a02f-7207-4b7e-8c92-474a8f35c737",
        "name": "Groceries",
        "group_name": "Household",
        "goal_target": 500.00,
        "activity": -247.50,
        "remaining": 252.50,
        "percentage_spent": 49.5,
        "has_goal": true
      },
      {
        "id": "a1b2c3d4-...",
        "name": "Gas",
        "group_name": "Transportation",
        "goal_target": 120.00,
        "activity": -31.00,
        "remaining": 89.00,
        "percentage_spent": 25.8,
        "has_goal": true
      },
      {
        "id": "e5f6g7h8-...",
        "name": "Dining Out",
        "group_name": "Fun",
        "goal_target": 200.00,
        "activity": -137.70,
        "remaining": 62.30,
        "percentage_spent": 68.9,
        "has_goal": true
      }
    ]
  }
}
```

**Field Descriptions:**

| Field                          | Type    | Description                                                    |
|--------------------------------|---------|----------------------------------------------------------------|
| `month`                        | string  | Current budget month (YYYY-MM)                                 |
| `expected_income`              | float   | Expected monthly income (dollars)                              |
| `income_source`                | string  | `"scheduled_transactions"` or `"manual_override"`              |
| `last_synced`                  | string  | ISO 8601 timestamp of last YNAB sync                           |
| `total_remaining`              | float   | Sum of all category remaining amounts                          |
| `categories[].goal_target`     | float   | Monthly goal amount (dollars). `null` if no goal set.          |
| `categories[].activity`        | float   | Total spending this month (negative value, dollars)            |
| `categories[].remaining`       | float   | Projected remaining: `goal_target + activity` (dollars)        |
| `categories[].percentage_spent`| float   | Percentage of goal spent: `abs(activity) / goal_target * 100`  |
| `categories[].has_goal`        | boolean | Whether this category has a YNAB goal configured               |

**Notes:**
- All monetary amounts are in dollars (converted from YNAB milliunits server-side)
- Categories are ordered by the admin's configured display order
- Only categories assigned to the authenticated recipient are returned

---

### 3.2 Get Spending Trends

Returns historical spending data for the authenticated recipient's assigned categories.

```
GET /api/dashboard/trends/
```

**Query Parameters:**

| Parameter   | Type   | Required | Default | Description                              |
|-------------|--------|----------|---------|------------------------------------------|
| `months`    | int    | No       | 3       | Number of months of history to return    |
| `category`  | string | No       | all     | Specific category ID, or "all"           |

**Request Headers:** `Authorization: Bearer <access_token>`

**Success Response (200):**
```json
{
  "data": {
    "period": {
      "start": "2025-12",
      "end": "2026-02",
      "months_requested": 3,
      "months_allowed": 6
    },
    "categories": [
      {
        "id": "2ef6a02f-...",
        "name": "Groceries",
        "months": [
          {
            "month": "2025-12",
            "goal_target": 500.00,
            "activity": -487.20,
            "remaining": 12.80
          },
          {
            "month": "2026-01",
            "goal_target": 500.00,
            "activity": -512.30,
            "remaining": -12.30
          },
          {
            "month": "2026-02",
            "goal_target": 500.00,
            "activity": -247.50,
            "remaining": 252.50
          }
        ]
      }
    ]
  }
}
```

**Field Descriptions:**

| Field                     | Type   | Description                                              |
|---------------------------|--------|----------------------------------------------------------|
| `period.months_allowed`   | int    | Max months the admin allows for this recipient           |
| `categories[].months[]`   | array  | Monthly data points, chronologically ordered             |

**Notes:**
- The `months` parameter is capped by the admin-configured limit per recipient
- If `months` exceeds the allowed limit, the allowed limit is used silently
- The current month (in progress) is always included as the last entry
- Only categories assigned to the authenticated recipient are returned

---

## 4. Webhook Endpoints

### 4.1 Twilio Inbound SMS Webhook

Receives inbound SMS messages from Twilio. Not consumed by the frontend.

```
POST /api/webhooks/twilio/inbound/
```

**Request Body** (Twilio form-encoded):
```
From=+15558675309
To=+15017250604
Body=UPDATE
MessageSid=SM1234567890
```

**Validation:**
- Twilio request signature validation is performed on every request
- Requests failing signature validation receive `403 Forbidden`

**Success Response (200):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Notes:**
- The response SMS is sent asynchronously via Celery, not as TwiML in the response
- This ensures the webhook returns quickly (Twilio has a 15-second timeout)
- Unrecognized phone numbers are logged and ignored
- Unrecognized keywords are logged and ignored (no error SMS sent)

---

### 4.2 Twilio Delivery Status Webhook

Receives SMS delivery status updates from Twilio.

```
POST /api/webhooks/twilio/status/
```

**Request Body** (Twilio form-encoded):
```
MessageSid=SM1234567890
MessageStatus=delivered
To=+15558675309
```

**Success Response (200):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Notes:**
- Updates the `NotificationLog` record with delivery status
- Statuses: `queued`, `sent`, `delivered`, `failed`, `undelivered`
- Failed/undelivered statuses trigger a warning log

---

## 5. Rate Limiting

| Endpoint Group         | Limit                    | Window    |
|------------------------|--------------------------|-----------|
| `/api/auth/login/`     | 5 requests               | 1 minute  |
| `/api/auth/refresh/`   | 10 requests              | 1 minute  |
| `/api/dashboard/*`     | 60 requests              | 1 minute  |
| `/api/webhooks/*`      | No limit (Twilio-signed) | -         |

---

## 6. CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "https://budget.yourdomain.com",  # Production frontend
    "http://localhost:5173",           # Vite dev server
]
CORS_ALLOW_CREDENTIALS = True  # Required for httpOnly cookie refresh token
```
