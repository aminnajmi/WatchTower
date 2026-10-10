# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 52 files · ~39,826 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 603 nodes · 1569 edges · 54 communities (25 shown, 29 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 122 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4b89a555`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- TidioMonitor
- Graphify Instructions
- ._login
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- Request
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- User
- deployment-health-check.sh
- Notification
- create_access_token
- test_tidio.py
- shutil
- .connect
- create_openclaw_notification
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
- SchedulerExecutionTests
- sanitized_validation_error
- tidio.py
- ProductionConfigTests
- _authenticate_login
- authenticate_token
- DeploymentWorkflowSafetyTests

## God Nodes (most connected - your core abstractions)
1. `TidioMonitor` - 57 edges
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
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `SchedulerExecutionTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `UserManagementTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_users.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (54 total, 29 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (47): generate_password_hash(), require_admin(), Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), OSRelease (+39 more)

### Community 1 - "main.py"
Cohesion: 0.09
Nodes (35): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., check(), deny_notification(), disable_user(), enable_user(), get_os(), health() (+27 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (19): ABC, releases(), releases_for_os(), AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (45): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+37 more)

### Community 4 - "TidioMonitor"
Cohesion: 0.16
Nodes (5): Inspect API availability and readiness only; never call execute() or read…, Log page metadata only; never include page text, form values, or URLs with…, TidioMonitor, Page, Path

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.11
Nodes (17): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+9 more)

### Community 10 - "schemas.py"
Cohesion: 0.14
Nodes (10): CheckResult, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate, field_validator (+2 more)

### Community 11 - "Request"
Cohesion: 0.17
Nodes (22): account_page(), dashboard_page(), events(), events_page(), get_notification(), home(), login_page(), notification_center_page() (+14 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job. (+11 more)

### Community 16 - "User"
Cohesion: 0.13
Nodes (17): hash_user_password(), verify_user_password(), change_own_password(), create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user() (+9 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Notification"
Cohesion: 0.23
Nodes (13): Any, approve_notification(), get_openclaw_approval_decision(), list_notifications(), datetime, Return only an OpenClaw request's action-bound approval decision., _serialize_notification(), test_notification() (+5 more)

### Community 19 - "create_access_token"
Cohesion: 0.07
Nodes (8): create_access_token(), Principal, main(), NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests, WebDashboardTests

### Community 20 - "test_tidio.py"
Cohesion: 0.15
Nodes (7): TidioSnapshot, test_tidio_console_diagnostics_redact_error_text(), test_tidio_inbox_render_wait_is_bounded(), test_tidio_password_encryption_round_trip(), test_tidio_recaptcha_response_logs_path_without_query(), test_tidio_session_is_encrypted_and_persisted(), test_tidio_snapshot_defaults()

### Community 22 - ".connect"
Cohesion: 0.16
Nodes (3): TidioConnection, Exception, Fernet

### Community 23 - "create_openclaw_notification"
Cohesion: 0.43
Nodes (7): _approval_action_id(), create_openclaw_notification(), _openclaw_authorized(), _openclaw_key_fingerprint(), Bind approval to a stable hash of the proposed action fields., _validate_notification_payload(), NotificationCreate

### Community 24 - "test_tidio_keeps_browser_open_for_manual_verification"
Cohesion: 0.33
Nodes (4): test_tidio_keeps_browser_open_for_manual_verification(), test_tidio_verification_error_surfaces_authentication_required(), fail_login(), noop()

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 48 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 49 - "tidio.py"
Cohesion: 0.16
Nodes (9): datetime, asyncio, base64, cryptography_fernet, hashlib, json, playwright_async_api, Check reCAPTCHA loading in a fresh Playwright context without signing in. (+1 more)

### Community 50 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 51 - "_authenticate_login"
Cohesion: 0.25
Nodes (8): _hash_password(), verify_password(), _authenticate_login(), login(), login_form(), DB user credentials first; retain the configured admin as bootstrap fallback., POST fallback for browsers when client-side JavaScript is unavailable., _set_session_cookie()

### Community 52 - "authenticate_token"
Cohesion: 0.32
Nodes (8): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), HTTPAuthorizationCredentials

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 159 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `._login`, `test_tidio_waits_for_inbox_client_render`, `tidio.py`, `create_access_token`, `test_tidio.py`, `.connect`, `test_tidio_keeps_browser_open_for_manual_verification`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `create_access_token`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TidioConnection` connect `.connect` to `auth.py`, `main.py`, `TidioMonitor`, `tidio.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._