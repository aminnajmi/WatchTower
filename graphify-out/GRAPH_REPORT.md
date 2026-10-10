# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~36,985 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 528 nodes · 1364 edges · 48 communities (17 shown, 31 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `828dcb24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- UserManagementTests
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- NotificationCenterTests
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- User
- deployment-health-check.sh
- create_access_token
- playwright_async_api
- shutil
- OpenClaw task approval contract
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
- _authenticate_login
- WebDashboardTests
- DeploymentWorkflowSafetyTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `create_access_token()` - 28 edges
6. `WebDashboardTests` - 22 edges
7. `NotificationCenterTests` - 21 edges
8. `Base` - 19 edges
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

## Communities (48 total, 31 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.10
Nodes (41): generate_password_hash(), Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, check_all(), compare_releases() (+33 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (90): Any, authenticate_token(), configure_session_factory_provider(), principal_for_username(), Request, Allow the app's configured DB session factory to be injected in tests., Resolve every request against current DB state so disable takes effect…, _request_origin() (+82 more)

### Community 2 - "Release"
Cohesion: 0.18
Nodes (15): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+7 more)

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

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (20): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+12 more)

### Community 10 - "schemas.py"
Cohesion: 0.09
Nodes (19): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, ReleaseInfo, UserCreate (+11 more)

### Community 15 - "scheduler.py"
Cohesion: 0.15
Nodes (16): status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event(), scheduled_check() (+8 more)

### Community 16 - "User"
Cohesion: 0.21
Nodes (16): create_user(), delete_user(), disable_user(), enable_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user() (+8 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 19 - "create_access_token"
Cohesion: 0.16
Nodes (6): create_access_token(), Principal, require_admin(), ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests

### Community 22 - "OpenClaw task approval contract"
Cohesion: 0.29
Nodes (6): Canonical JSON and digest, Create a request, Deployment and rollback, Network safety for the executor, OpenClaw task approval contract, Task specification v1

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.19
Nodes (4): FakeProvider, SchedulerExecutionTests, latest(), _done()

### Community 50 - "ProductionConfigTests"
Cohesion: 0.17
Nodes (8): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., BaseSettings, ProductionConfigTests

### Community 51 - "_authenticate_login"
Cohesion: 0.40
Nodes (5): _hash_password(), verify_password(), _authenticate_login(), login(), DB user credentials first; retain the configured admin as bootstrap fallback.

## Knowledge Gaps
- **46 isolated node(s):** `Create a request`, `Task specification v1`, `Canonical JSON and digest`, `Network safety for the executor`, `Deployment and rollback` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 149 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `UserManagementTests`, `NotificationCenterTests`, `SchedulerExecutionTests`, `_authenticate_login`, `WebDashboardTests`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `main.py`, `UserManagementTests`, `ProductionConfigTests`, `create_access_token`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create a request`, `Task specification v1`, `Canonical JSON and digest` to the rest of the system?**
  _46 weakly-connected nodes found - possible documentation gaps or missing edges._