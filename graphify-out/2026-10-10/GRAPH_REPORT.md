# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~38,742 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 590 nodes · 1522 edges · 46 communities (20 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 106 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `98d79d0d`
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
- get
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- User
- deployment-health-check.sh
- Notification
- create_access_token
- auth.py
- shutil
- create_openclaw_notification
- _utc_timestamp
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
- SchedulerExecutionTests

## God Nodes (most connected - your core abstractions)
1. `TidioMonitor` - 47 edges
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
- `UserManagementTests` --uses--> `User`  [INFERRED]
  tests/test_users.py → app/models.py
- `SchedulerExecutionTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_scheduler.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (46 total, 26 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.11
Nodes (35): Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, check_all(), compare_releases(), parse_version() (+27 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (37): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), verify_user_password(), _authenticate_login(), change_own_password(), check(), create_web_session() (+29 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (45): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+37 more)

### Community 4 - "WebDashboardTests"
Cohesion: 0.09
Nodes (4): generate_password_hash(), getpass, UserManagementTests, WebDashboardTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.06
Nodes (19): TidioConnection, Allow Tidio's client-side inbox to hydrate without waiting for analytics idle., Log page metadata only; never include page text, form values, or URLs with…, TidioMonitor, TidioSnapshot, asyncio, Exception, Fernet (+11 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.11
Nodes (16): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+8 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "get"
Cohesion: 0.14
Nodes (31): account_page(), dashboard_page(), events(), events_page(), get_notification(), health(), home(), login_page() (+23 more)

### Community 15 - "scheduler.py"
Cohesion: 0.07
Nodes (26): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., _add_check_job() (+18 more)

### Community 16 - "User"
Cohesion: 0.21
Nodes (15): hash_user_password(), create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user(), list_users() (+7 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Notification"
Cohesion: 0.24
Nodes (12): Any, approve_notification(), deny_notification(), list_notifications(), _serialize_notification(), test_notification(), Notification, create_notification() (+4 more)

### Community 19 - "create_access_token"
Cohesion: 0.10
Nodes (6): create_access_token(), Principal, NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests

### Community 20 - "auth.py"
Cohesion: 0.11
Nodes (21): authenticate_token(), configure_session_factory_provider(), _hash_password(), Request, Allow the app's configured DB session factory to be injected in tests., _request_origin(), require_admin(), verify_password() (+13 more)

### Community 22 - "create_openclaw_notification"
Cohesion: 0.29
Nodes (8): _approval_action_id(), create_openclaw_notification(), get_openclaw_approval_decision(), _openclaw_authorized(), _openclaw_key_fingerprint(), Bind approval to a stable hash of the proposed action fields., Return only an OpenClaw request's action-bound approval decision., _validate_notification_payload()

### Community 23 - "_utc_timestamp"
Cohesion: 0.33
Nodes (6): get_os(), list_os(), datetime, serialize_os(), status(), _utc_timestamp()

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 157 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `auth.py`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `test_telegram.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TidioConnection` connect `TidioMonitor` to `test_telegram.py`, `main.py`, `auth.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._