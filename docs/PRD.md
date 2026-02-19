# Product Requirements Document (PRD)

## YNAB Budget Notifier & Portal

| Field              | Value                        |
|--------------------|------------------------------|
| **Document Owner** | Matt Anderson                |
| **Version**        | 1.0                          |
| **Status**         | Draft                        |
| **Last Updated**   | 2026-02-14                   |

---

## 1. Problem Statement

YNAB (You Need A Budget) is a powerful personal budgeting tool, but it has two key limitations for households where only one person manages the budget:

1. **Non-YNAB users are blind to the budget.** Household members who do spending (e.g., groceries, gas) have no visibility into how much remains in their relevant categories without logging into YNAB.

2. **YNAB only shows balances based on money currently on hand.** It does not forecast remaining amounts based on expected income for the month. For example, if a paycheck hasn't arrived yet but is scheduled, YNAB won't show the full month's available amount in each category.

This creates a daily friction: the non-budgeting spouse must ask "how much can I spend on groceries?" and the budgeting spouse must manually look it up and relay the information.

## 2. Product Vision

A lightweight application that bridges the gap between YNAB and non-YNAB household members by:

- **Sending daily SMS notifications** with remaining budget amounts for categories the recipient cares about
- **Providing a mobile-first web portal** where recipients can check real-time category balances, goal progress, and spending trends
- **Forecasting remaining amounts** based on expected monthly income (from YNAB scheduled transactions), not just current money on hand

## 3. Target Users

### 3.1 Budget Owner (Admin)
- The person who manages the YNAB budget
- Configures the system: which recipients exist, which categories they see, notification preferences
- Technically comfortable (developer)
- Single user in this role

### 3.2 Budget Recipient
- Household members who spend money but don't use YNAB
- Needs quick, at-a-glance budget visibility for their relevant categories
- Primary interaction: receiving daily texts, occasionally checking the web portal
- Not technical - the experience must be simple and frictionless
- The system should support N recipients, each with their own category list

### 3.3 Typical User Story: "The Grocery Run"
> Sarah receives a text every morning at 7:00 AM showing her remaining amounts for Groceries, Gas, and Dining Out. Before heading to the store, she glances at her text: "$252.50 remaining in Groceries." While at the store, she opens the web portal to double-check and sees she's 50% through her grocery goal for the month. She shops confidently within budget.

## 4. Functional Requirements

### 4.1 YNAB Integration

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-1.1 | System shall authenticate with the YNAB API using a personal access token                        | P0       |
| FR-1.2 | System shall retrieve all budget categories with balances, goals, and activity                    | P0       |
| FR-1.3 | System shall retrieve scheduled transactions to determine expected monthly income                 | P0       |
| FR-1.4 | System shall support a manual override for expected monthly income                                | P0       |
| FR-1.5 | System shall support a single YNAB budget                                                        | P0       |
| FR-1.6 | System shall use delta requests (server_knowledge) for efficient data synchronization             | P1       |
| FR-1.7 | System shall cache YNAB data locally to minimize API calls                                       | P1       |

### 4.2 Forecasting Engine

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-2.1 | Remaining amount per category shall be calculated as: `goal_target + activity` (activity is negative for spending) | P0 |
| FR-2.2 | Expected income shall be the sum of all scheduled income transactions for the current month       | P0       |
| FR-2.3 | Manual income override, if set, shall take precedence over scheduled transaction sum               | P0       |
| FR-2.4 | The forecast shall assume the full month's expected income regardless of current date              | P0       |
| FR-2.5 | Categories without a goal_target shall display the YNAB balance field as a fallback               | P1       |

### 4.3 Recipient Management

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-3.1 | Admin shall be able to create, update, and delete recipients                                      | P0       |
| FR-3.2 | Each recipient shall have: name, phone number, email, login credentials                           | P0       |
| FR-3.3 | Admin shall assign specific YNAB categories to each recipient (category-level, not group-level)   | P0       |
| FR-3.4 | Admin shall configure notification time per recipient, with a system-wide default                  | P0       |
| FR-3.5 | Admin shall configure how far back historical data is available per recipient (for spending trends)| P1       |

### 4.4 SMS Notifications

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-4.1 | System shall send a daily SMS to each recipient at their configured time                          | P0       |
| FR-4.2 | SMS shall list remaining amount for each of the recipient's assigned categories                   | P0       |
| FR-4.3 | SMS shall include a "Total Remaining" line summing all filtered category remaining amounts         | P0       |
| FR-4.4 | SMS shall be sent via Twilio                                                                      | P0       |
| FR-4.5 | Recipients shall be able to text a keyword (e.g., "UPDATE") to receive a fresh summary on demand  | P1       |
| FR-4.6 | SMS format shall follow the template defined in Section 5.1                                       | P0       |

### 4.5 Web Portal

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-5.1 | Recipients shall log in with username and password                                                | P0       |
| FR-5.2 | Dashboard shall display only the recipient's assigned categories                                  | P0       |
| FR-5.3 | Each category shall show: name, remaining amount, goal target, amount spent                       | P0       |
| FR-5.4 | Each category shall include a progress bar showing percentage of goal spent                        | P0       |
| FR-5.5 | Dashboard shall show a total remaining amount across all assigned categories                       | P0       |
| FR-5.6 | Portal shall display spending trends/charts for assigned categories                                | P1       |
| FR-5.7 | Historical data shown in trends shall respect the admin-configured limit per recipient             | P1       |
| FR-5.8 | Portal shall be mobile-first and responsive                                                       | P0       |
| FR-5.9 | Future: Magic link authentication as a security upgrade to replace username/password               | P2       |

### 4.6 Admin Interface

| ID     | Requirement                                                                                      | Priority |
|--------|--------------------------------------------------------------------------------------------------|----------|
| FR-6.1 | Admin shall manage all configuration through Django Admin                                          | P0       |
| FR-6.2 | Admin shall be able to manage recipients and their category assignments                            | P0       |
| FR-6.3 | Admin shall be able to set the manual income override amount                                       | P0       |
| FR-6.4 | Admin shall be able to set the default notification time                                           | P0       |
| FR-6.5 | Admin shall be able to view notification delivery history/status                                   | P1       |

## 5. UX Specifications

### 5.1 SMS Template

```
Daily Budget Update (Mon, Feb 14):

Groceries:   $252.50 remaining
Gas:          $89.00 remaining
Dining Out:   $62.30 remaining
─────────────────────
Total:       $403.80 remaining
```

### 5.2 On-Demand SMS Response

Same format as daily SMS, with a header indicating it's an on-demand update:

```
Budget Update (Feb 14, 2:35 PM):

Groceries:   $247.20 remaining
Gas:          $73.00 remaining
Dining Out:   $58.10 remaining
─────────────────────
Total:       $378.30 remaining
```

### 5.3 Web Portal Dashboard (Wireframe Description)

```
┌─────────────────────────────────────┐
│  YNAB Budget Portal     [Logout]    │
├─────────────────────────────────────┤
│                                     │
│  Total Remaining: $403.80           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Groceries          $252.50  │    │
│  │ ████████████░░░░░░░  50.5%  │    │
│  │ Goal: $500 | Spent: $247.50 │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Gas                  $89.00 │    │
│  │ ██████░░░░░░░░░░░░░  25.5%  │    │
│  │ Goal: $120 | Spent: $31.00  │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Dining Out           $62.30 │    │
│  │ ██████████████░░░░░  68.9%  │    │
│  │ Goal: $200 | Spent: $137.70 │    │
│  └─────────────────────────────┘    │
│                                     │
│  [Spending Trends]                  │
│  ┌─────────────────────────────┐    │
│  │  📊 Groceries - Last 3 Mo   │    │
│  │  Dec: $487  Jan: $512        │    │
│  │  Feb: $247 (in progress)     │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

## 6. Assumptions & Constraints

| # | Assumption/Constraint                                                                  |
|---|----------------------------------------------------------------------------------------|
| 1 | The YNAB personal access token is long-lived and managed by the admin                  |
| 2 | YNAB API rate limit is 200 requests/hour per access token                              |
| 3 | All monetary amounts in YNAB are in "milliunits" (divide by 1000 for display)          |
| 4 | A single YNAB budget is used                                                           |
| 5 | The admin is the only user with YNAB access; recipients never interact with YNAB       |
| 6 | Twilio is the sole SMS provider                                                        |
| 7 | The application is for a small household (< 10 recipients)                             |
| 8 | Expected income is determined from YNAB scheduled transactions with manual override    |

## 7. Out of Scope (v1)

- Multiple YNAB budgets
- YNAB OAuth (using personal access token instead)
- Push notifications (app-based)
- Email notifications
- Recipient self-service category selection
- Transaction-level detail in SMS
- Multi-currency support
- YNAB write operations (read-only integration)
- Native mobile app

## 8. Success Metrics

| Metric                              | Target                                           |
|--------------------------------------|--------------------------------------------------|
| Daily SMS delivery success rate      | > 99%                                            |
| SMS delivery time (from scheduled)   | < 60 seconds                                     |
| Web portal page load time            | < 2 seconds on mobile                            |
| YNAB data freshness (cached)         | < 30 minutes stale                               |
| System uptime                        | > 99% (self-hosted) / > 99.9% (cloud)            |
| User adoption                        | Recipient checks portal or reads SMS daily        |

## 9. Glossary

| Term                  | Definition                                                                     |
|-----------------------|--------------------------------------------------------------------------------|
| **Budget Owner/Admin**| The person who manages the YNAB budget and administers this application         |
| **Recipient**         | A household member who receives budget notifications and uses the web portal    |
| **Category**          | A YNAB budget category (e.g., Groceries, Gas, Dining Out)                      |
| **Goal Target**       | The YNAB goal amount set for a category for the month                          |
| **Activity**          | The total spending (negative) in a category for the current month              |
| **Remaining**         | `goal_target + activity` - the projected amount left to spend                  |
| **Expected Income**   | Total income expected for the month, from scheduled transactions or override    |
| **Milliunits**        | YNAB's internal currency format (1 dollar = 1000 milliunits)                   |
| **Delta Request**     | A YNAB API feature to fetch only data changed since last request               |
