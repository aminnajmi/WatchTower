# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 54 files · ~37,647 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 549 nodes · 1427 edges · 53 communities (23 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 110 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f6f04096`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- User
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- app/service.py
- schemas.py
- TaskSpecification
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- Request
- create_access_token
- playwright_async_api
- shutil
- OpenClaw task approval contract
- NotificationCenterTests
- UserManagementTests
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
- Notification
- User Management Page
- _authenticate_login
- SchedulerExecutionTests
- authenticate_token
- base64
- ProductionConfigTests
- sanitized_validation_error
- WebDashboardTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `create_access_token()` - 28 edges
6. `NotificationCenterTests` - 22 edges
7. `WebDashboardTests` - 22 edges
8. `Base` - 19 edges
9. `User` - 19 edges
10. `TelegramSendResult` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Canonical JSON and digest` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `Deployment and rollback` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (53 total, 30 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (46): events(), status(), Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, Task specification matching OpenClaw's fail-closed execution core., concurrent_futures (+38 more)

### Community 1 - "main.py"
Cohesion: 0.11
Nodes (25): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., check(), disable_user(), enable_user(), get_os(), health(), list_os() (+17 more)

### Community 2 - "Release"
Cohesion: 0.18
Nodes (18): ABC, releases(), releases_for_os(), AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider (+10 more)

### Community 3 - "app.js"
Cohesion: 0.15
Nodes (38): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+30 more)

### Community 4 - "User"
Cohesion: 0.26
Nodes (13): create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user(), list_users(), reset_user_password() (+5 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "app/service.py"
Cohesion: 0.08
Nodes (29): ReleaseHistory, send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send() (+21 more)

### Community 10 - "schemas.py"
Cohesion: 0.13
Nodes (13): _approval_action_id(), Bind approval to a stable hash of the proposed action fields., CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator (+5 more)

### Community 11 - "TaskSpecification"
Cohesion: 0.15
Nodes (17): approve_notification(), create_openclaw_notification(), get_notification(), get_openclaw_approval_decision(), _openclaw_authorized(), _openclaw_key_fingerprint(), Create approval UI copy from the validated task, never agent prose., Return only an OpenClaw request's action-bound approval decision. (+9 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+11 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Request"
Cohesion: 0.20
Nodes (19): account_page(), dashboard_page(), events_page(), home(), login_page(), notification_center_page(), notifications_legacy_page(), operating_systems_page() (+11 more)

### Community 19 - "create_access_token"
Cohesion: 0.16
Nodes (6): create_access_token(), Principal, require_admin(), ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests

### Community 22 - "OpenClaw task approval contract"
Cohesion: 0.22
Nodes (7): Canonical JSON and digest, Create and retrieve an approval, Deployment and rollback, Executor network safeguards, OpenClaw task approval contract, Task specification v1, CoreTaskSpec

### Community 24 - "UserManagementTests"
Cohesion: 0.18
Nodes (4): hash_user_password(), verify_user_password(), change_own_password(), UserManagementTests

### Community 44 - "Notification"
Cohesion: 0.26
Nodes (11): deny_notification(), list_notifications(), NotificationDenyRequest, datetime, _serialize_notification(), _utc_timestamp(), Notification, create_notification() (+3 more)

### Community 46 - "_authenticate_login"
Cohesion: 0.20
Nodes (10): verify_access_token(), _authenticate_login(), create_web_session(), login(), login_form(), BaseModel, DB user credentials first; retain the configured admin as bootstrap fallback., POST fallback for browsers when client-side JavaScript is unavailable. (+2 more)

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 48 - "authenticate_token"
Cohesion: 0.40
Nodes (6): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), HTTPAuthorizationCredentials

### Community 50 - "ProductionConfigTests"
Cohesion: 0.17
Nodes (8): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., BaseSettings, ProductionConfigTests

### Community 51 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 52 - "WebDashboardTests"
Cohesion: 0.13
Nodes (4): generate_password_hash(), _hash_password(), verify_password(), WebDashboardTests

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 153 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `app/service.py`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `_authenticate_login`, `SchedulerExecutionTests`, `WebDashboardTests`, `NotificationCenterTests`, `UserManagementTests`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `Notification`, `ProductionConfigTests`, `create_access_token`, `UserManagementTests`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._