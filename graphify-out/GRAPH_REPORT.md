# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~36,960 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 554 nodes · 1452 edges · 41 communities (14 shown, 27 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.94)
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
- create_access_token
- schemas.py
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- deployment-health-check.sh
- auth.py
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
- SchedulerExecutionTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 43 edges
3. `TidioMonitor` - 33 edges
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

## Communities (41 total, 27 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.09
Nodes (40): Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), OSRelease, Add nullable approval-binding fields without granting legacy rows access., ReleaseEvent (+32 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (83): Any, verify_access_token(), account_page(), _approval_action_id(), approve_notification(), _authenticate_login(), check(), create_openclaw_notification() (+75 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (19): ABC, releases(), releases_for_os(), AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.14
Nodes (41): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+33 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.09
Nodes (17): TidioConnection, datetime, TidioMonitor, TidioSnapshot, asyncio, cryptography_fernet, Exception, Fernet (+9 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "create_access_token"
Cohesion: 0.05
Nodes (24): create_access_token(), Principal, require_admin(), send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs. (+16 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (18): lifespan(), status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job. (+10 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "auth.py"
Cohesion: 0.07
Nodes (34): authenticate_token(), configure_session_factory_provider(), generate_password_hash(), _hash_password(), hash_user_password(), principal_for_username(), Request, Allow the app's configured DB session factory to be injected in tests. (+26 more)

### Community 46 - "ProductionConfigTests"
Cohesion: 0.31
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 142 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `create_access_token`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `test_telegram.py`, `main.py`, `WebDashboardTests`, `SchedulerExecutionTests`, `auth.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_telegram.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09292412617220801 - nodes in this community are weakly interconnected._