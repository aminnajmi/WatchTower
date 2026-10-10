# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~36,932 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 526 nodes · 1362 edges · 51 communities (21 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `828dcb24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- Notification
- Release
- app.js
- UserManagementTests
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- notify
- schemas.py
- main.py
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- User
- deployment-health-check.sh
- Request
- create_access_token
- playwright_async_api
- shutil
- OpenClaw task approval contract
- authenticate_token
- sanitized_validation_error
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
- User Management Page
- SchedulerExecutionTests
- base64
- ProductionConfigTests
- post
- WebDashboardTests
- DeploymentWorkflowSafetyTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `create_access_token()` - 28 edges
6. `WebDashboardTests` - 22 edges
7. `NotificationCenterTests` - 20 edges
8. `Base` - 19 edges
9. `User` - 19 edges
10. `TelegramSendResult` - 19 edges

## Surprising Connections (you probably didn't know these)
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `UserManagementTests` --uses--> `User`  [INFERRED]
  tests/test_users.py → app/models.py
- `SchedulerExecutionTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_scheduler.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (51 total, 30 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.09
Nodes (46): events(), status(), Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), OSRelease (+38 more)

### Community 1 - "Notification"
Cohesion: 0.09
Nodes (32): Any, _approval_action_id(), approve_notification(), create_openclaw_notification(), get_openclaw_approval_decision(), list_notifications(), _openclaw_authorized(), _openclaw_key_fingerprint() (+24 more)

### Community 2 - "Release"
Cohesion: 0.19
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.15
Nodes (38): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+30 more)

### Community 4 - "UserManagementTests"
Cohesion: 0.18
Nodes (4): hash_user_password(), verify_user_password(), change_own_password(), UserManagementTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "notify"
Cohesion: 0.16
Nodes (5): notify(), Deliver to configured channels independently; report aggregate success., FakeAsyncClient, FakeResponse, SupportSalesTelegramTests

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, ReleaseInfo, UserCreate (+2 more)

### Community 11 - "main.py"
Cohesion: 0.11
Nodes (22): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., deny_notification(), get_os(), health(), list_os(), NotificationDenyRequest, providers() (+14 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+11 more)

### Community 16 - "User"
Cohesion: 0.26
Nodes (13): create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user(), list_users(), reset_user_password() (+5 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Request"
Cohesion: 0.19
Nodes (20): account_page(), dashboard_page(), events_page(), get_notification(), home(), login_page(), notification_center_page(), notifications_legacy_page() (+12 more)

### Community 19 - "create_access_token"
Cohesion: 0.06
Nodes (20): create_access_token(), Principal, require_admin(), send(), _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send() (+12 more)

### Community 22 - "OpenClaw task approval contract"
Cohesion: 0.29
Nodes (6): Canonical JSON and digest, Create a request, Deployment and rollback, Network safety for the executor, OpenClaw task approval contract, Task specification v1

### Community 23 - "authenticate_token"
Cohesion: 0.28
Nodes (9): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), _set_session_cookie() (+1 more)

### Community 24 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 50 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 51 - "post"
Cohesion: 0.15
Nodes (15): _hash_password(), verify_password(), _authenticate_login(), check(), disable_user(), enable_user(), login(), login_form() (+7 more)

## Knowledge Gaps
- **46 isolated node(s):** `Create a request`, `Task specification v1`, `Canonical JSON and digest`, `Network safety for the executor`, `Deployment and rollback` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 147 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `create_access_token`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `UserManagementTests`, `main.py`, `SchedulerExecutionTests`, `post`, `WebDashboardTests`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `WebDashboardTests` to `auth.py`, `Release`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create a request`, `Task specification v1`, `Canonical JSON and digest` to the rest of the system?**
  _46 weakly-connected nodes found - possible documentation gaps or missing edges._