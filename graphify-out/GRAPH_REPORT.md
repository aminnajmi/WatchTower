# Graph Report - WatchTower  (2026-10-19)

## Corpus Check
- 60 files · ~45,891 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 662 nodes · 1747 edges · 57 communities (22 shown, 35 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 139 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4c34ca41`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- DeploymentWorkflowSafetyTests
- Release
- app.js
- To-Dos and private attachments
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- NotificationCenterTests
- schemas.py
- get
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- post
- Principal
- playwright_async_api
- shutil
- task_spec.py
- TelegramSendResult
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
- principal_for_username
- AttachmentTests
- _authenticate_login
- create_access_token
- WebDashboardTests
- hash_user_password
- TodoTests
- SupportSalesTelegramEndpointTests
- sanitized_validation_error

## God Nodes (most connected - your core abstractions)
1. `get()` - 46 edges
2. `Release` - 45 edges
3. `Principal` - 38 edges
4. `create_access_token()` - 31 edges
5. `User` - 30 edges
6. `OSRelease` - 29 edges
7. `NotificationCenterTests` - 26 edges
8. `Base` - 23 edges
9. `WebDashboardTests` - 23 edges
10. `api()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Canonical JSON and digest` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `Deployment and rollback` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `TelegramTestEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (57 total, 35 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.09
Nodes (48): generate_password_hash(), _hash_password(), verify_password(), verify_user_password(), Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db() (+40 more)

### Community 2 - "Release"
Cohesion: 0.15
Nodes (19): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.09
Nodes (62): api(), dateText(), escapeHtml(), expireBrowserSession(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents() (+54 more)

### Community 4 - "To-Dos and private attachments"
Cohesion: 0.40
Nodes (4): API, Storage and deployment, To-Dos and private attachments, Verification

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+2 more)

### Community 11 - "get"
Cohesion: 0.23
Nodes (22): account_page(), dashboard_page(), events(), events_page(), health(), home(), login_page(), notification_center_page() (+14 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (18): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+10 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "post"
Cohesion: 0.15
Nodes (19): check(), create_user(), delete_user(), disable_user(), enable_user(), _ensure_another_active_admin(), get_account(), _get_managed_user() (+11 more)

### Community 19 - "Principal"
Cohesion: 0.09
Nodes (47): authenticate_token(), Principal, Request, _request_origin(), require_admin(), change_own_password(), Todo, TodoAttachment (+39 more)

### Community 22 - "task_spec.py"
Cohesion: 0.07
Nodes (35): get_openclaw_approval_decision(), Return only an OpenClaw request's action-bound approval decision., _task_binding_is_valid(), BusinessActionTask, canonical_task_json(), PublicWebsiteInspectionTask, BaseModel, field_validator (+27 more)

### Community 23 - "TelegramSendResult"
Cohesion: 0.09
Nodes (20): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+12 more)

### Community 24 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 44 - "main.py"
Cohesion: 0.10
Nodes (25): access_token_expiration(), configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., Return the validated JWT expiration for the browser's logout timer., get_os(), list_notifications(), list_os(), datetime (+17 more)

### Community 46 - "Notification"
Cohesion: 0.18
Nodes (17): _approval_action_id(), approve_notification(), create_openclaw_notification(), get_notification(), _openclaw_authorized(), _openclaw_key_fingerprint(), Return a fresh 256-bit approval identity for each request., Create approval UI copy from the validated task, never agent prose. (+9 more)

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.19
Nodes (4): FakeProvider, SchedulerExecutionTests, latest(), _done()

### Community 48 - "principal_for_username"
Cohesion: 0.25
Nodes (8): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), create_web_session(), deny_notification(), NotificationDenyRequest, BaseModel, WebSessionRequest

### Community 50 - "_authenticate_login"
Cohesion: 0.33
Nodes (6): _authenticate_login(), login(), login_form(), DB user credentials first; retain the configured admin as bootstrap fallback., POST fallback for browsers when client-side JavaScript is unavailable., _set_session_cookie()

### Community 51 - "create_access_token"
Cohesion: 0.16
Nodes (3): create_access_token(), ApplicationStartupTests, TelegramTestEndpointTests

### Community 56 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

## Knowledge Gaps
- **47 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Storage and deployment`, `API` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 178 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `create_access_token`, `hash_user_password`, `task_spec.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `SchedulerExecutionTests`, `_authenticate_login`, `hash_user_password`, `SupportSalesTelegramEndpointTests`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `User` (e.g. with `principal_for_username()` and `_authenticate_login()`) actually correct?**
  _`User` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._