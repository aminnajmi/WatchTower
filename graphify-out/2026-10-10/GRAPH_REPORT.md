# Graph Report - WatchTower  (2026-10-10)

## Corpus Check
- 51 files · ~38,952 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 593 nodes · 1529 edges · 54 communities (24 shown, 30 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `66a2e1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- auth.py
- main.py
- Release
- app.js
- TidioMonitor
- Graphify Instructions
- .finish_authentication
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- TelegramSendResult
- schemas.py
- get
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- Principal
- deployment-health-check.sh
- Notification
- create_access_token
- test_tidio.py
- shutil
- .connect
- WebDashboardTests
- test_tidio_keeps_browser_open_for_manual_verification
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
- test_tidio_waits_for_inbox_client_render
- SchedulerExecutionTests
- sanitized_validation_error
- tidio.py
- ProductionConfigTests
- post
- authenticate_token
- DeploymentWorkflowSafetyTests

## God Nodes (most connected - your core abstractions)
1. `TidioMonitor` - 50 edges
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
- `SupportSalesTelegramEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `UserManagementTests` --uses--> `User`  [INFERRED]
  tests/test_users.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (54 total, 30 thin omitted)

### Community 0 - "auth.py"
Cohesion: 0.08
Nodes (45): configure_session_factory_provider(), generate_password_hash(), _hash_password(), hash_user_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), Base, _configure_sqlite_connection() (+37 more)

### Community 1 - "main.py"
Cohesion: 0.11
Nodes (25): get_os(), health(), list_os(), NotificationDenyRequest, providers(), BaseModel, serialize_os(), tidio_auth_action() (+17 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (45): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+37 more)

### Community 4 - "TidioMonitor"
Cohesion: 0.18
Nodes (5): TidioMonitor, Page, Path, test_tidio_console_diagnostics_redact_error_text(), test_tidio_recaptcha_response_logs_path_without_query()

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramSendResult"
Cohesion: 0.08
Nodes (22): Any, send(), notify(), Deliver to configured channels independently; report aggregate success., create_notification(), metadata_for(), datetime, _failure() (+14 more)

### Community 10 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 11 - "get"
Cohesion: 0.20
Nodes (24): account_page(), dashboard_page(), events(), events_page(), home(), login_page(), notification_center_page(), notifications_legacy_page() (+16 more)

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (19): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+11 more)

### Community 16 - "Principal"
Cohesion: 0.17
Nodes (19): Principal, require_admin(), create_user(), delete_user(), disable_user(), enable_user(), _ensure_another_active_admin(), get_account() (+11 more)

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 18 - "Notification"
Cohesion: 0.18
Nodes (17): _approval_action_id(), approve_notification(), create_openclaw_notification(), deny_notification(), get_notification(), get_openclaw_approval_decision(), list_notifications(), _openclaw_authorized() (+9 more)

### Community 19 - "create_access_token"
Cohesion: 0.11
Nodes (4): create_access_token(), NotificationCenterTests, ApplicationStartupTests, SupportSalesTelegramEndpointTests

### Community 20 - "test_tidio.py"
Cohesion: 0.18
Nodes (5): TidioSnapshot, test_tidio_inbox_render_wait_is_bounded(), test_tidio_password_encryption_round_trip(), test_tidio_session_is_encrypted_and_persisted(), test_tidio_snapshot_defaults()

### Community 22 - ".connect"
Cohesion: 0.19
Nodes (3): TidioConnection, Exception, Fernet

### Community 24 - "test_tidio_keeps_browser_open_for_manual_verification"
Cohesion: 0.33
Nodes (4): test_tidio_keeps_browser_open_for_manual_verification(), test_tidio_verification_error_surfaces_authentication_required(), fail_login(), noop()

### Community 47 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 48 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

### Community 49 - "tidio.py"
Cohesion: 0.18
Nodes (7): datetime, base64, cryptography_fernet, dataclasses, json, playwright_async_api, urllib_parse

### Community 50 - "ProductionConfigTests"
Cohesion: 0.17
Nodes (8): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), _migrate_notification_approval_fields(), Add nullable approval-binding fields without granting legacy rows access., BaseSettings, ProductionConfigTests

### Community 51 - "post"
Cohesion: 0.15
Nodes (14): verify_user_password(), _authenticate_login(), change_own_password(), check(), login(), login_form(), logout(), DB user credentials first; retain the configured admin as bootstrap fallback. (+6 more)

### Community 52 - "authenticate_token"
Cohesion: 0.28
Nodes (9): authenticate_token(), principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), verify_access_token(), create_web_session(), WebSessionRequest (+1 more)

## Knowledge Gaps
- **42 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `WatchTower CI/CD Deployment Workflow`, `WatchTower Compose Service` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 157 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `.finish_authentication`, `test_tidio_waits_for_inbox_client_render`, `tidio.py`, `test_tidio.py`, `.connect`, `test_tidio_keeps_browser_open_for_manual_verification`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `auth.py`, `TelegramSendResult`, `WebDashboardTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TidioConnection` connect `.connect` to `auth.py`, `main.py`, `TidioMonitor`, `tidio.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `TidioMonitor` (e.g. with `TidioConnection` and `test_tidio_console_diagnostics_redact_error_text()`) actually correct?**
  _`TidioMonitor` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 16 INFERRED edges - model-reasoned connections that need verification._