# Graph Report - WatchTower  (2026-10-09)

## Corpus Check
- 51 files · ~35,489 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 530 nodes · 1402 edges · 48 communities (20 shown, 28 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `09e3111c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- Request
- Release
- app.js
- WebDashboardTests
- Graphify Instructions
- TidioMonitor
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- SchedulerExecutionTests
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- main.py
- deployment-health-check.sh
- Principal
- UserManagementTests
- Notification
- post
- authenticate_token
- sanitized_validation_error
- DeploymentWorkflowSafetyTests
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
- ProductionConfigTests
- NotificationCenterTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 42 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `TidioMonitor` - 27 edges
6. `create_access_token()` - 26 edges
7. `WebDashboardTests` - 22 edges
8. `Base` - 20 edges
9. `User` - 19 edges
10. `TelegramSendResult` - 19 edges

## Surprising Connections (you probably didn't know these)
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (48 total, 28 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.11
Nodes (40): create_access_token(), Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, check_all(), compare_releases() (+32 more)

### Community 1 - "Request"
Cohesion: 0.18
Nodes (21): account_page(), dashboard_page(), events(), events_page(), home(), login_page(), notification_center_page(), notifications_legacy_page() (+13 more)

### Community 2 - "Release"
Cohesion: 0.16
Nodes (19): ABC, releases(), releases_for_os(), AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.14
Nodes (42): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+34 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.11
Nodes (14): TidioConnection, datetime, TidioMonitor, TidioSnapshot, asyncio, cryptography_fernet, dataclasses, Exception (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.08
Nodes (19): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+11 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 15 - "scheduler.py"
Cohesion: 0.16
Nodes (15): status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event(), scheduled_check() (+7 more)

### Community 16 - "main.py"
Cohesion: 0.10
Nodes (27): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., get_os(), health(), lifespan(), list_os(), NotificationDenyRequest, providers() (+19 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Principal"
Cohesion: 0.17
Nodes (19): Principal, require_admin(), create_user(), delete_user(), disable_user(), enable_user(), _ensure_another_active_admin(), get_account() (+11 more)

### Community 19 - "UserManagementTests"
Cohesion: 0.15
Nodes (6): _hash_password(), hash_user_password(), verify_password(), verify_user_password(), change_own_password(), UserManagementTests

### Community 20 - "Notification"
Cohesion: 0.20
Nodes (17): Any, approve_notification(), create_openclaw_notification(), deny_notification(), get_notification(), list_notifications(), _openclaw_authorized(), datetime (+9 more)

### Community 21 - "post"
Cohesion: 0.20
Nodes (11): _authenticate_login(), check(), login(), login_form(), logout(), DB user credentials first; retain the configured admin as bootstrap fallback., POST fallback for browsers when client-side JavaScript is unavailable., _set_session_cookie() (+3 more)

### Community 22 - "authenticate_token"
Cohesion: 0.28
Nodes (9): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), WebSessionRequest (+1 more)

### Community 23 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 46 - "ProductionConfigTests"
Cohesion: 0.22
Nodes (6): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), BaseSettings, ProductionConfigTests

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 131 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `SchedulerExecutionTests`, `WebDashboardTests`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `WebDashboardTests` to `auth.py`, `Release`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1076923076923077 - nodes in this community are weakly interconnected._