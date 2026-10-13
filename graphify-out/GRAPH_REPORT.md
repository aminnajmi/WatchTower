# Graph Report - WatchTower  (2026-10-13)

## Corpus Check
- 56 files · ~41,847 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 615 nodes · 1625 edges · 49 communities (12 shown, 37 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fe7fee7f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- DeploymentWorkflowSafetyTests
- Release
- app.js
- NotificationCenterTests
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- create_access_token
- schemas.py
- main.py
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- hash_user_password
- todos.py
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
- .test_baseline_and_duplicate_major_events
- User Management Page
- SchedulerExecutionTests
- base64
- WebDashboardTests

## God Nodes (most connected - your core abstractions)
1. `get()` - 46 edges
2. `Release` - 45 edges
3. `Principal` - 36 edges
4. `create_access_token()` - 31 edges
5. `OSRelease` - 29 edges
6. `User` - 27 edges
7. `NotificationCenterTests` - 26 edges
8. `WebDashboardTests` - 23 edges
9. `Base` - 22 edges
10. `api()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Canonical JSON and digest` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `Deployment and rollback` --references--> `verify_approval()`  [INFERRED]
  docs/openclaw-approval-contract.md → tests/openclaw_core_reference.py
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `TelegramTestEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `ProductionConfigTests` --uses--> `Settings`  [INFERRED]
  tests/test_production_config.py → app/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (49 total, 37 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (54): configure_session_factory_provider(), generate_password_hash(), _hash_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), verify_user_password(), Fail startup on missing/unsafe credentials in production mode., Settings (+46 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.11
Nodes (52): api(), dateText(), escapeHtml(), expireBrowserSession(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents() (+44 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo (+2 more)

### Community 11 - "main.py"
Cohesion: 0.05
Nodes (104): access_token_expiration(), authenticate_token(), Principal, principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, Return the validated JWT expiration for the browser's logout timer., _request_origin() (+96 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+11 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 19 - "todos.py"
Cohesion: 0.12
Nodes (25): Todo, create_todo(), delete_todo(), get_todo(), list_assignees(), list_todos(), BaseModel, delete (+17 more)

### Community 22 - "task_spec.py"
Cohesion: 0.07
Nodes (36): get_openclaw_approval_decision(), Return only an OpenClaw request's action-bound approval decision., _task_binding_is_valid(), BusinessActionTask, canonical_task_json(), PublicWebsiteInspectionTask, BaseModel, field_validator (+28 more)

### Community 23 - "TelegramSendResult"
Cohesion: 0.07
Nodes (21): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+13 more)

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 164 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `create_access_token`, `.test_baseline_and_duplicate_major_events`, `SchedulerExecutionTests`, `WebDashboardTests`, `TelegramSendResult`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `create_access_token`, `hash_user_password`, `task_spec.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `SchedulerExecutionTests`, `hash_user_password`, `TelegramSendResult`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._