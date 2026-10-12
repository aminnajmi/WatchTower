# Graph Report - WatchTower  (2026-10-12)

## Corpus Check
- 54 files · ~39,117 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 571 nodes · 1472 edges · 50 communities (20 shown, 30 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `531a6ba3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- get
- Release
- app.js
- User
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- main.py
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- post
- authenticate_token
- playwright_async_api
- shutil
- task_spec.py
- create_access_token
- Principal
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
- _authenticate_login
- User Management Page
- sanitized_validation_error
- SchedulerExecutionTests
- base64
- WebDashboardTests

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 41 edges
3. `create_access_token()` - 29 edges
4. `OSRelease` - 29 edges
5. `Principal` - 28 edges
6. `NotificationCenterTests` - 26 edges
7. `WebDashboardTests` - 23 edges
8. `Base` - 19 edges
9. `User` - 19 edges
10. `TelegramSendResult` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Canonical JSON and digest` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `Deployment and rollback` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (50 total, 30 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (45): configure_session_factory_provider(), generate_password_hash(), _hash_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), Base, _configure_sqlite_connection(), OSRelease (+37 more)

### Community 1 - "get"
Cohesion: 0.23
Nodes (21): account_page(), dashboard_page(), events(), events_page(), health(), home(), login_page(), notification_center_page() (+13 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (45): api(), dateText(), escapeHtml(), expireBrowserSession(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents() (+37 more)

### Community 4 - "User"
Cohesion: 0.12
Nodes (17): hash_user_password(), verify_user_password(), change_own_password(), create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user() (+9 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (20): send(), notify(), Deliver to configured channels independently; report aggregate success., create_notification(), metadata_for(), Any, datetime, _failure() (+12 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+3 more)

### Community 11 - "main.py"
Cohesion: 0.11
Nodes (22): access_token_expiration(), Return the validated JWT expiration for the browser's logout timer., get_os(), list_os(), datetime, releases(), releases_for_os(), security_headers() (+14 more)

### Community 15 - "scheduler.py"
Cohesion: 0.07
Nodes (27): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., _add_check_job() (+19 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "post"
Cohesion: 0.26
Nodes (12): approve_notification(), check(), deny_notification(), get_notification(), list_notifications(), logout(), _serialize_notification(), test_notification() (+4 more)

### Community 19 - "authenticate_token"
Cohesion: 0.22
Nodes (11): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), NotificationDenyRequest (+3 more)

### Community 22 - "task_spec.py"
Cohesion: 0.06
Nodes (44): _approval_action_id(), create_openclaw_notification(), get_openclaw_approval_decision(), _openclaw_authorized(), _openclaw_key_fingerprint(), Return a fresh 256-bit approval identity for each request., Create approval UI copy from the validated task, never agent prose., Return only an OpenClaw request's action-bound approval decision. (+36 more)

### Community 23 - "create_access_token"
Cohesion: 0.07
Nodes (4): create_access_token(), NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests

### Community 24 - "Principal"
Cohesion: 0.31
Nodes (6): Principal, require_admin(), disable_user(), enable_user(), _set_user_active(), TelegramTestEndpointTests

### Community 44 - "_authenticate_login"
Cohesion: 0.33
Nodes (6): _authenticate_login(), login(), login_form(), DB user credentials first; retain the configured admin as bootstrap fallback., POST fallback for browsers when client-side JavaScript is unavailable., _set_session_cookie()

### Community 46 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 158 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `create_access_token` to `auth.py`, `User`, `TelegramSendResult`, `scheduler.py`, `task_spec.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `User`, `main.py`, `_authenticate_login`, `SchedulerExecutionTests`, `Principal`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._