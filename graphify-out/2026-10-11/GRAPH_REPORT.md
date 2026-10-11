# Graph Report - WatchTower  (2026-10-11)

## Corpus Check
- 54 files · ~38,471 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 561 nodes · 1448 edges · 47 communities (16 shown, 31 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 109 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5ddd6750`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- Principal
- Graphify Instructions
- cryptography_fernet
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- authenticate_token
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- ipaddress
- deployment-health-check.sh
- create_access_token
- playwright_async_api
- shutil
- task_spec.py
- NotificationCenterTests
- UserManagementTests
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
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (47 total, 31 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.09
Nodes (41): configure_session_factory_provider(), generate_password_hash(), _hash_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), Base, _configure_sqlite_connection(), OSRelease (+33 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (97): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), account_page(), _approval_action_id(), approve_notification(), _authenticate_login(), check() (+89 more)

### Community 2 - "Release"
Cohesion: 0.15
Nodes (19): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+11 more)

### Community 3 - "app.js"
Cohesion: 0.15
Nodes (38): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+30 more)

### Community 4 - "Principal"
Cohesion: 0.43
Nodes (3): Principal, require_admin(), TelegramTestEndpointTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.09
Nodes (20): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., Send only to the independently configured Support-Sales group., send(), send_support_sales() (+12 more)

### Community 10 - "schemas.py"
Cohesion: 0.14
Nodes (10): CheckResult, PasswordChange, PasswordReset, BaseModel, field_validator, model_validator, ReleaseInfo, UserCreate (+2 more)

### Community 11 - "authenticate_token"
Cohesion: 0.67
Nodes (4): authenticate_token(), Request, _request_origin(), HTTPAuthorizationCredentials

### Community 15 - "scheduler.py"
Cohesion: 0.07
Nodes (26): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., _add_check_job() (+18 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 19 - "create_access_token"
Cohesion: 0.16
Nodes (3): create_access_token(), ApplicationStartupTests, SupportSalesTelegramEndpointTests

### Community 22 - "task_spec.py"
Cohesion: 0.07
Nodes (35): get_openclaw_approval_decision(), Return only an OpenClaw request's action-bound approval decision., _task_binding_is_valid(), BusinessActionTask, canonical_task_json(), PublicWebsiteInspectionTask, BaseModel, field_validator (+27 more)

### Community 24 - "UserManagementTests"
Cohesion: 0.16
Nodes (5): hash_user_password(), verify_user_password(), change_own_password(), reset_user_password(), UserManagementTests

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.19
Nodes (4): FakeProvider, SchedulerExecutionTests, latest(), _done()

## Knowledge Gaps
- **44 isolated node(s):** `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards`, `Docker Compose Configuration`, `Docker Deployment` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 158 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `auth.py`, `main.py`, `scheduler.py`, `create_access_token`, `task_spec.py`, `UserManagementTests`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `create_access_token()` connect `create_access_token` to `auth.py`, `main.py`, `Principal`, `SchedulerExecutionTests`, `UserManagementTests`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and retrieve an approval`, `Task specification v1`, `Executor network safeguards` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._