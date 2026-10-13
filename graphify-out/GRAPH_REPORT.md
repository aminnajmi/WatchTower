# Graph Report - WatchTower  (2026-10-13)

## Corpus Check
- 56 files · ~42,926 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 623 nodes · 1644 edges · 57 communities (25 shown, 32 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 132 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0c2bebcd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- DeploymentWorkflowSafetyTests
- get
- app.js
- NotificationCenterTests
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- Principal
- schemas.py
- Request
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- User
- todos.py
- playwright_async_api
- shutil
- task_spec.py
- FakeAsyncClient
- ProductionConfigTests
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
- main.py
- User Management Page
- Notification
- SchedulerExecutionTests
- authenticate_token
- base64
- post
- TelegramClientTests
- WebDashboardTests
- TelegramSendResult
- create_openclaw_notification
- notifications/__init__.py
- sanitized_validation_error

## God Nodes (most connected - your core abstractions)
1. `get()` - 46 edges
2. `Release` - 45 edges
3. `Principal` - 36 edges
4. `create_access_token()` - 31 edges
5. `OSRelease` - 29 edges
6. `User` - 28 edges
7. `NotificationCenterTests` - 26 edges
8. `WebDashboardTests` - 23 edges
9. `Base` - 22 edges
10. `api()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Canonical JSON and digest` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `Deployment and rollback` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `TodoTests` --uses--> `Base`  [INFERRED]
  tests/test_todos.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (57 total, 32 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.10
Nodes (45): generate_password_hash(), _hash_password(), hash_user_password(), verify_password(), events(), status(), Base, _configure_sqlite_connection() (+37 more)

### Community 2 - "get"
Cohesion: 0.18
Nodes (18): ABC, releases(), releases_for_os(), AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider (+10 more)

### Community 3 - "app.js"
Cohesion: 0.10
Nodes (59): api(), dateText(), escapeHtml(), expireBrowserSession(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents() (+51 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "Principal"
Cohesion: 0.14
Nodes (6): create_access_token(), Principal, require_admin(), ApplicationStartupTests, SupportSalesTelegramEndpointTests, TelegramTestEndpointTests

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+2 more)

### Community 11 - "Request"
Cohesion: 0.22
Nodes (19): account_page(), dashboard_page(), events_page(), get_notification(), home(), login_page(), notification_center_page(), notifications_legacy_page() (+11 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+11 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "User"
Cohesion: 0.09
Nodes (20): verify_user_password(), change_own_password(), create_user(), delete_user(), _ensure_another_active_admin(), get_account(), _get_managed_user(), get_user() (+12 more)

### Community 19 - "todos.py"
Cohesion: 0.11
Nodes (25): Todo, create_todo(), delete_todo(), get_todo(), list_assignees(), list_todos(), BaseModel, delete (+17 more)

### Community 22 - "task_spec.py"
Cohesion: 0.08
Nodes (29): BusinessActionTask, PublicWebsiteInspectionTask, BaseModel, field_validator, model_validator, Validated, immutable task specifications used by OpenClaw approvals., Compatibility facade for existing callers; parsing returns the concrete spec…, _TaskBase (+21 more)

### Community 23 - "FakeAsyncClient"
Cohesion: 0.19
Nodes (3): FakeAsyncClient, FakeResponse, SupportSalesTelegramTests

### Community 24 - "ProductionConfigTests"
Cohesion: 0.31
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 44 - "main.py"
Cohesion: 0.10
Nodes (21): access_token_expiration(), configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., Return the validated JWT expiration for the browser's logout timer., get_os(), health(), list_os(), providers() (+13 more)

### Community 46 - "Notification"
Cohesion: 0.18
Nodes (17): approve_notification(), get_openclaw_approval_decision(), list_notifications(), datetime, Return only an OpenClaw request's action-bound approval decision., _serialize_notification(), _task_binding_is_valid(), test_notification() (+9 more)

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.19
Nodes (4): FakeProvider, SchedulerExecutionTests, latest(), _done()

### Community 48 - "authenticate_token"
Cohesion: 0.18
Nodes (13): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), deny_notification() (+5 more)

### Community 50 - "post"
Cohesion: 0.18
Nodes (13): _authenticate_login(), check(), disable_user(), enable_user(), login(), login_form(), logout(), post (+5 more)

### Community 51 - "TelegramClientTests"
Cohesion: 0.18
Nodes (4): TelegramClientTests, latest(), latest(), latest()

### Community 53 - "TelegramSendResult"
Cohesion: 0.40
Nodes (9): _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales(), send_support_sales_test(), send_test(), TelegramSendResult (+1 more)

### Community 54 - "create_openclaw_notification"
Cohesion: 0.29
Nodes (8): _approval_action_id(), create_openclaw_notification(), _openclaw_authorized(), _openclaw_key_fingerprint(), Return a fresh 256-bit approval identity for each request., Create approval UI copy from the validated task, never agent prose., _task_notification_copy(), _validate_notification_payload()

### Community 55 - "notifications/__init__.py"
Cohesion: 0.38
Nodes (4): send(), notify(), Deliver to configured channels independently; report aggregate success., httpx

### Community 56 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 164 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `get` to `auth.py`, `TelegramClientTests`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `Principal`, `Notification`, `User`, `task_spec.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `Principal` to `auth.py`, `main.py`, `SchedulerExecutionTests`, `post`, `todos.py`, `User`, `WebDashboardTests`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._