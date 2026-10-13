# Graph Report - WatchTower  (2026-10-13)

## Corpus Check
- 56 files · ~42,103 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 628 nodes · 1696 edges · 46 communities (15 shown, 31 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 146 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1f734ea3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- ProductionConfigTests
- get
- app.js
- TaskManagementTests
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
- tasks.py
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
1. `get()` - 46 edges
2. `Release` - 45 edges
3. `Principal` - 39 edges
4. `create_access_token()` - 31 edges
5. `User` - 30 edges
6. `OSRelease` - 29 edges
7. `Base` - 26 edges
8. `NotificationCenterTests` - 26 edges
9. `WebDashboardTests` - 23 edges
10. `api()` - 20 edges

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

## Communities (46 total, 31 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (49): generate_password_hash(), _hash_password(), verify_password(), verify_user_password(), Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db() (+41 more)

### Community 1 - "ProductionConfigTests"
Cohesion: 0.27
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 2 - "get"
Cohesion: 0.09
Nodes (43): ABC, access_token_expiration(), Return the validated JWT expiration for the browser's logout timer., account_page(), dashboard_page(), events(), events_page(), home() (+35 more)

### Community 3 - "app.js"
Cohesion: 0.11
Nodes (52): api(), dateText(), escapeHtml(), expireBrowserSession(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents() (+44 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (18): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+10 more)

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+2 more)

### Community 11 - "main.py"
Cohesion: 0.05
Nodes (75): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., require_admin(), verify_access_token(), _approval_action_id(), approve_notification(), _authenticate_login(), check() (+67 more)

### Community 15 - "scheduler.py"
Cohesion: 0.16
Nodes (15): status(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event(), scheduled_check() (+7 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 19 - "tasks.py"
Cohesion: 0.12
Nodes (46): authenticate_token(), Principal, principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), change_own_password(), get_account() (+38 more)

### Community 22 - "task_spec.py"
Cohesion: 0.07
Nodes (37): get_openclaw_approval_decision(), Return only an OpenClaw request's action-bound approval decision., _task_binding_is_valid(), BusinessActionTask, canonical_task_json(), PublicWebsiteInspectionTask, BaseModel, field_validator (+29 more)

### Community 23 - "create_access_token"
Cohesion: 0.05
Nodes (6): create_access_token(), hash_user_password(), NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests, UserManagementTests

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 166 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `get` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `create_access_token` to `auth.py`, `task_spec.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `TelegramSendResult`, `main.py`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `User` (e.g. with `principal_for_username()` and `_authenticate_login()`) actually correct?**
  _`User` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._