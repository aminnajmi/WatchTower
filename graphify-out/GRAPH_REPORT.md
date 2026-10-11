# Graph Report - WatchTower  (2026-10-11)

## Corpus Check
- 54 files · ~38,826 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 566 nodes · 1461 edges · 44 communities (14 shown, 30 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a02b2eae`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- DeploymentWorkflowSafetyTests
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- playwright_async_api
- shutil
- task_spec.py
- create_access_token
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
- WebDashboardTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `OSRelease` - 29 edges
4. `Principal` - 28 edges
5. `create_access_token()` - 28 edges
6. `NotificationCenterTests` - 26 edges
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
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (44 total, 30 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (48): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., Fail startup on missing/unsafe credentials in production mode., Settings, status(), Base, _configure_sqlite_connection(), ensure_sqlite_directory() (+40 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (95): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), account_page(), _approval_action_id(), approve_notification(), _authenticate_login(), check() (+87 more)

### Community 2 - "Release"
Cohesion: 0.15
Nodes (19): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (43): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+35 more)

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
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+3 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (18): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+10 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 22 - "task_spec.py"
Cohesion: 0.07
Nodes (35): get_openclaw_approval_decision(), Return only an OpenClaw request's action-bound approval decision., _task_binding_is_valid(), BusinessActionTask, canonical_task_json(), PublicWebsiteInspectionTask, BaseModel, field_validator (+27 more)

### Community 23 - "create_access_token"
Cohesion: 0.06
Nodes (11): authenticate_token(), create_access_token(), Principal, Request, _request_origin(), require_admin(), HTTPAuthorizationCredentials, NotificationCenterTests (+3 more)

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 52 - "WebDashboardTests"
Cohesion: 0.08
Nodes (9): generate_password_hash(), _hash_password(), hash_user_password(), verify_password(), verify_user_password(), change_own_password(), reset_user_password(), UserManagementTests (+1 more)

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 158 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `create_access_token` to `auth.py`, `main.py`, `WebDashboardTests`, `task_spec.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._