# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~36,854 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 549 nodes · 1444 edges · 45 communities (19 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc874e23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_telegram.py
- main.py
- Release
- app.js
- WebDashboardTests
- Graphify Instructions
- TidioMonitor
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- Notification
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- auth.py
- deployment-health-check.sh
- User
- Principal
- post
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
- Tidio Integration Page
- User Management Page
- ProductionConfigTests
- create_access_token

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 43 edges
3. `TidioMonitor` - 31 edges
4. `OSRelease` - 29 edges
5. `Principal` - 28 edges
6. `create_access_token()` - 28 edges
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

## Communities (45 total, 26 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.11
Nodes (38): Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), OSRelease, Add nullable approval-binding fields without granting legacy rows access., ReleaseEvent (+30 more)

### Community 1 - "main.py"
Cohesion: 0.11
Nodes (29): _approval_action_id(), create_openclaw_notification(), get_openclaw_approval_decision(), get_os(), health(), list_os(), NotificationDenyRequest, _openclaw_authorized() (+21 more)

### Community 2 - "Release"
Cohesion: 0.09
Nodes (44): ABC, account_page(), dashboard_page(), events(), events_page(), get_notification(), home(), login_page() (+36 more)

### Community 3 - "app.js"
Cohesion: 0.14
Nodes (41): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+33 more)

### Community 4 - "WebDashboardTests"
Cohesion: 0.13
Nodes (3): generate_password_hash(), getpass, WebDashboardTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.09
Nodes (16): TidioConnection, datetime, TidioMonitor, TidioSnapshot, asyncio, cryptography_fernet, dataclasses, Exception (+8 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (19): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+11 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "Notification"
Cohesion: 0.27
Nodes (11): Any, approve_notification(), deny_notification(), list_notifications(), _serialize_notification(), test_notification(), Notification, create_notification() (+3 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job. (+11 more)

### Community 16 - "auth.py"
Cohesion: 0.13
Nodes (19): authenticate_token(), configure_session_factory_provider(), _hash_password(), principal_for_username(), Request, Allow the app's configured DB session factory to be injected in tests., Resolve every request against current DB state so disable takes effect…, _request_origin() (+11 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "User"
Cohesion: 0.15
Nodes (15): hash_user_password(), create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user(), list_users() (+7 more)

### Community 19 - "Principal"
Cohesion: 0.36
Nodes (5): Principal, disable_user(), enable_user(), _set_user_active(), TelegramTestEndpointTests

### Community 20 - "post"
Cohesion: 0.16
Nodes (13): verify_user_password(), _authenticate_login(), change_own_password(), check(), login(), login_form(), logout(), DB user credentials first; retain the configured admin as bootstrap fallback. (+5 more)

### Community 46 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 47 - "create_access_token"
Cohesion: 0.07
Nodes (8): create_access_token(), NotificationCenterTests, FakeProvider, SchedulerExecutionTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests, latest(), _done()

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 139 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `TelegramSendResult`, `WebDashboardTests`, `create_access_token`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `test_telegram.py`, `main.py`, `WebDashboardTests`, `auth.py`, `User`, `Principal`, `post`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_telegram.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10840824960338445 - nodes in this community are weakly interconnected._