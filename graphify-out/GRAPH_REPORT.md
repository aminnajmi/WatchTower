# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 49 files · ~34,794 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 501 nodes · 1309 edges · 48 communities (19 shown, 29 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bd8bb62b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_telegram.py
- main.py
- Release
- app.js
- principal_for_username
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- FakeAsyncClient
- schemas.py
- get
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- Principal
- deployment-health-check.sh
- Notification
- create_access_token
- playwright_async_api
- shutil
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
- auth.py
- DeploymentWorkflowSafetyTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `create_access_token()` - 28 edges
6. `WebDashboardTests` - 22 edges
7. `Base` - 19 edges
8. `User` - 19 edges
9. `TelegramSendResult` - 19 edges
10. `ReleaseEvent` - 17 edges

## Surprising Connections (you probably didn't know these)
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `TelegramTestEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (48 total, 29 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.09
Nodes (45): Base, _configure_sqlite_connection(), ensure_sqlite_directory(), OSRelease, ReleaseEvent, ReleaseHistory, send(), notify() (+37 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (24): get_os(), lifespan(), list_os(), releases(), releases_for_os(), sanitized_validation_error(), security_headers(), serialize_os() (+16 more)

### Community 2 - "Release"
Cohesion: 0.14
Nodes (21): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+13 more)

### Community 3 - "app.js"
Cohesion: 0.15
Nodes (38): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+30 more)

### Community 4 - "principal_for_username"
Cohesion: 0.29
Nodes (7): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), create_web_session(), NotificationDenyRequest, BaseModel, WebSessionRequest

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "FakeAsyncClient"
Cohesion: 0.19
Nodes (3): FakeAsyncClient, FakeResponse, SupportSalesTelegramTests

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "get"
Cohesion: 0.23
Nodes (21): account_page(), dashboard_page(), events(), events_page(), health(), home(), login_page(), notification_center_page() (+13 more)

### Community 15 - "scheduler.py"
Cohesion: 0.16
Nodes (13): status(), _add_check_job(), get_scheduler(), Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event(), scheduled_check(), apscheduler_events (+5 more)

### Community 16 - "Principal"
Cohesion: 0.19
Nodes (20): hash_user_password(), Principal, require_admin(), change_own_password(), create_user(), delete_user(), disable_user(), enable_user() (+12 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Notification"
Cohesion: 0.13
Nodes (23): Any, _approval_action_id(), approve_notification(), create_openclaw_notification(), deny_notification(), get_notification(), get_openclaw_approval_decision(), list_notifications() (+15 more)

### Community 19 - "create_access_token"
Cohesion: 0.08
Nodes (7): create_access_token(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 50 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 51 - "post"
Cohesion: 0.17
Nodes (13): _hash_password(), verify_password(), _authenticate_login(), check(), login(), login_form(), logout(), DB user credentials first; retain the configured admin as bootstrap fallback. (+5 more)

### Community 52 - "auth.py"
Cohesion: 0.06
Nodes (18): authenticate_token(), configure_session_factory_provider(), generate_password_hash(), Request, Allow the app's configured DB session factory to be injected in tests., _request_origin(), verify_user_password(), fastapi_security (+10 more)

## Knowledge Gaps
- **41 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 136 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `auth.py`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `test_telegram.py`, `main.py`, `SchedulerExecutionTests`, `Principal`, `post`, `auth.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `auth.py` to `test_telegram.py`, `Release`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._