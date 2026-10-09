# Graph Report - WatchTower  (2026-10-09)

## Corpus Check
- 51 files · ~35,239 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 520 nodes · 1417 edges · 21 communities (15 shown, 6 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de163fdd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- test_telegram.py
- auth.py
- app.js
- Release
- scheduler.py
- TidioMonitor
- schemas.py
- SchedulerExecutionTests
- Shared Dashboard Layout
- Graphify Skill
- DeploymentHealthCheckTests
- ProductionConfigTests
- deployment-health-check.sh
- DeploymentWorkflowSafetyTests
- Persistent Tracker Data Volume
- UserManagementTests
- telegram.py
- Python Runtime Dependencies
- WatchTower Logo
- shutil

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `TidioMonitor` - 35 edges
3. `OSRelease` - 29 edges
4. `Principal` - 25 edges
5. `create_access_token()` - 23 edges
6. `WebDashboardTests` - 21 edges
7. `Base` - 20 edges
8. `User` - 19 edges
9. `ReleaseEvent` - 17 edges
10. `Provider` - 17 edges

## Surprising Connections (you probably didn't know these)
- `WatchTower CI/CD Deployment Workflow` --semantically_similar_to--> `Production Docker Compose Deployment`  [INFERRED] [semantically similar]
  .github/workflows/deploy.yml → README.md
- `Release Monitoring Dashboard` --semantically_similar_to--> `Linux Release Tracking`  [INFERRED] [semantically similar]
  templates/dashboard.html → README.md
- `Operating System Release Detail` --semantically_similar_to--> `Linux Release Tracking`  [INFERRED] [semantically similar]
  templates/os_detail.html → README.md
- `Release History Page` --semantically_similar_to--> `Linux Release Tracking`  [INFERRED] [semantically similar]
  templates/releases.html → README.md
- `Notification Center` --semantically_similar_to--> `WatchTower Deployment and Operations Guide`  [INFERRED] [semantically similar]
  templates/notifications.html → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]
- **WatchTower Dashboard Pages** — templates_account_account_page, templates_dashboard_release_dashboard, templates_events_event_history, templates_notifications_notification_center, templates_os_detail_operating_system_detail, templates_releases_release_history, templates_settings_application_settings, templates_tidio_tidio_integration, templates_users_user_management [EXTRACTED 1.00]

## Communities (21 total, 6 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.05
Nodes (99): Any, Principal, principal_for_username(), Resolve every request against current DB state so disable takes effect…, require_admin(), verify_access_token(), verify_user_password(), account_page() (+91 more)

### Community 1 - "test_telegram.py"
Cohesion: 0.08
Nodes (42): create_access_token(), Base, _configure_sqlite_connection(), ensure_sqlite_directory(), init_db(), OSRelease, ReleaseEvent, ReleaseHistory (+34 more)

### Community 2 - "auth.py"
Cohesion: 0.08
Nodes (17): authenticate_token(), configure_session_factory_provider(), generate_password_hash(), _hash_password(), Request, Allow the app's configured DB session factory to be injected in tests., _request_origin(), verify_password() (+9 more)

### Community 3 - "app.js"
Cohesion: 0.14
Nodes (42): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+34 more)

### Community 4 - "Release"
Cohesion: 0.19
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 5 - "scheduler.py"
Cohesion: 0.13
Nodes (18): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+10 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.07
Nodes (22): TidioConnection, datetime, TidioMonitor, TidioSnapshot, cryptography_fernet, dataclasses, Exception, Fernet (+14 more)

### Community 7 - "schemas.py"
Cohesion: 0.15
Nodes (11): CheckResult, NotificationCreate, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate (+3 more)

### Community 8 - "SchedulerExecutionTests"
Cohesion: 0.15
Nodes (5): FakeProvider, SchedulerExecutionTests, latest(), latest(), _done()

### Community 9 - "Shared Dashboard Layout"
Cohesion: 0.16
Nodes (15): WatchTower CI/CD Deployment Workflow, Production Docker Compose Deployment, Linux Release Tracking, WatchTower Deployment and Operations Guide, Account Page, Shared Dashboard Layout, Release Monitoring Dashboard, Event History Page (+7 more)

### Community 10 - "Graphify Skill"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 12 - "ProductionConfigTests"
Cohesion: 0.29
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 13 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 16 - "UserManagementTests"
Cohesion: 0.11
Nodes (4): hash_user_password(), reset_user_password(), NotificationCenterTests, UserManagementTests

### Community 17 - "telegram.py"
Cohesion: 0.24
Nodes (9): send(), _failure(), Send a Telegram message without exposing credentials in errors or logs., send(), send_test(), TelegramSendResult, httpx, logging (+1 more)

## Knowledge Gaps
- **24 isolated node(s):** `Incremental Graph Update`, `Graphify Knowledge Graph`, `Graph Query and Explanation`, `Semantic Extraction`, `Add and Watch Reference` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 117 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `SchedulerExecutionTests`, `test_telegram.py`, `auth.py`, `telegram.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `DeploymentHealthCheckTests` connect `DeploymentHealthCheckTests` to `test_telegram.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Incremental Graph Update`, `Graphify Knowledge Graph`, `Graph Query and Explanation` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05201465201465202 - nodes in this community are weakly interconnected._