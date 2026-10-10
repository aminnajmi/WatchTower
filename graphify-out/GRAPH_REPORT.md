# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~38,869 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 592 nodes · 1526 edges · 52 communities (20 shown, 32 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ea609c0d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- .connect
- Graphify Instructions
- TidioMonitor
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- get
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- User
- deployment-health-check.sh
- Notification
- create_access_token
- tidio.py
- shutil
- ._reconnect
- _utc_timestamp
- test_tidio_keeps_browser_open_for_manual_verification
- WatchTower CI/CD Deployment Workflow
- WatchTower Compose Service
- Role-based Authentication
- SQLite Backup and Restore
- Production Deployment on Ubuntu Server
- Operating System Release Tracking
- Single-process UTC Scheduler
- WatchTower Release Monitoring Service
- Python Application Dependencies
- WatchTower Logo
- My Account Page
- Shared Application Layout
- Release Monitoring Dashboard
- Release Events Page
- Sign-in Page
- Notification Center
- Operating System Detail Page
- Release History Page
- Settings Page
- Tidio Integration Page
- User Management Page
- test_tidio_waits_for_inbox_client_render
- WebDashboardTests
- sanitized_validation_error
- ._check_once
- ._diagnose_page
- test_tidio_inbox_render_wait_is_bounded

## God Nodes (most connected - your core abstractions)
1. `TidioMonitor` - 49 edges
2. `Release` - 45 edges
3. `get()` - 44 edges
4. `OSRelease` - 29 edges
5. `Principal` - 28 edges
6. `create_access_token()` - 28 edges
7. `WebDashboardTests` - 22 edges
8. `Base` - 20 edges
9. `User` - 19 edges
10. `TelegramSendResult` - 19 edges

## Surprising Connections (you probably didn't know these)
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `UserManagementTests` --uses--> `User`  [INFERRED]
  tests/test_users.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (52 total, 32 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.09
Nodes (44): configure_session_factory_provider(), generate_password_hash(), _hash_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), Base, _configure_sqlite_connection(), OSRelease (+36 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (35): verify_access_token(), _authenticate_login(), check(), create_web_session(), disable_user(), enable_user(), login(), login_form() (+27 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (45): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+37 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.17
Nodes (5): Allow Tidio's client-side inbox to hydrate without waiting for analytics idle., Log page metadata only; never include page text, form values, or URLs with…, TidioMonitor, Path, test_tidio_console_diagnostics_redact_error_text()

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (18): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+10 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "get"
Cohesion: 0.19
Nodes (25): account_page(), dashboard_page(), events(), events_page(), health(), home(), login_page(), notification_center_page() (+17 more)

### Community 15 - "scheduler.py"
Cohesion: 0.07
Nodes (26): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., _add_check_job() (+18 more)

### Community 16 - "User"
Cohesion: 0.23
Nodes (15): principal_for_username(), Resolve every request against current DB state so disable takes effect…, create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user() (+7 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Notification"
Cohesion: 0.14
Nodes (21): Any, _approval_action_id(), approve_notification(), create_openclaw_notification(), deny_notification(), get_notification(), get_openclaw_approval_decision(), list_notifications() (+13 more)

### Community 19 - "create_access_token"
Cohesion: 0.06
Nodes (16): authenticate_token(), create_access_token(), hash_user_password(), Principal, Request, _request_origin(), require_admin(), verify_user_password() (+8 more)

### Community 20 - "tidio.py"
Cohesion: 0.16
Nodes (10): TidioSnapshot, asyncio, base64, cryptography_fernet, dataclasses, playwright_async_api, test_tidio_password_encryption_round_trip(), test_tidio_session_is_encrypted_and_persisted() (+2 more)

### Community 23 - "_utc_timestamp"
Cohesion: 0.33
Nodes (6): get_os(), list_os(), datetime, serialize_os(), status(), _utc_timestamp()

### Community 24 - "test_tidio_keeps_browser_open_for_manual_verification"
Cohesion: 0.33
Nodes (4): test_tidio_keeps_browser_open_for_manual_verification(), test_tidio_verification_error_surfaces_authentication_required(), fail_login(), noop()

### Community 47 - "WebDashboardTests"
Cohesion: 0.09
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), _done(), WebDashboardTests

### Community 48 - "sanitized_validation_error"
Cohesion: 0.30
Nodes (5): sanitized_validation_error(), security_headers(), exception_handler, middleware, RequestValidationError

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 157 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `.connect`, `test_tidio_waits_for_inbox_client_render`, `._check_once`, `._diagnose_page`, `test_tidio_inbox_render_wait_is_bounded`, `tidio.py`, `._reconnect`, `test_tidio_keeps_browser_open_for_manual_verification`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TidioConnection` connect `._reconnect` to `auth.py`, `main.py`, `tidio.py`, `TidioMonitor`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `TidioMonitor` (e.g. with `TidioConnection` and `test_tidio_console_diagnostics_redact_error_text()`) actually correct?**
  _`TidioMonitor` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._