# Graph Report - WatchTower  (2026-10-06)

## Corpus Check
- 51 files · ~32,667 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 5, .css 2, .example 1)

## Summary
- 454 nodes · 1236 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 94 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8a18ad9b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- OSRelease
- main.py
- Release
- app.js
- WebDashboardTests
- Graphify Instructions
- ProductionConfigTests
- Dashboard Templates and Docs
- DeploymentHealthCheckTests
- NotificationCenterTests
- schemas.py
- create_access_token
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py
- notifications-center.js
- deployment-health-check.sh

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 39 edges
3. `OSRelease` - 32 edges
4. `User` - 23 edges
5. `create_access_token()` - 22 edges
6. `Principal` - 21 edges
7. `Base` - 21 edges
8. `NotificationCenterTests` - 21 edges
9. `WebDashboardTests` - 21 edges
10. `ReleaseEvent` - 17 edges

## Surprising Connections (you probably didn't know these)
- `TelegramTestEndpointTests` --uses--> `Principal`  [INFERRED]
  tests/test_telegram.py → app/auth.py
- `NotificationCenterTests` --uses--> `Base`  [INFERRED]
  tests/test_notifications.py → app/models.py
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

## Communities (19 total, 5 thin omitted)

### Community 0 - "OSRelease"
Cohesion: 0.08
Nodes (45): Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, send(), notify(), Deliver to configured channels independently; report aggregate success. (+37 more)

### Community 1 - "main.py"
Cohesion: 0.05
Nodes (96): authenticate_token(), configure_session_factory_provider(), _hash_password(), hash_user_password(), Principal, principal_for_username(), HTTPAuthorizationCredentials, Request (+88 more)

### Community 2 - "Release"
Cohesion: 0.17
Nodes (17): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+9 more)

### Community 3 - "app.js"
Cohesion: 0.20
Nodes (29): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+21 more)

### Community 4 - "WebDashboardTests"
Cohesion: 0.09
Nodes (5): generate_password_hash(), verify_user_password(), getpass, UserManagementTests, WebDashboardTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "ProductionConfigTests"
Cohesion: 0.22
Nodes (6): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), BaseSettings, ProductionConfigTests

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 8 - "DeploymentHealthCheckTests"
Cohesion: 0.15
Nodes (4): os, subprocess, DeploymentHealthCheckTests, DeploymentWorkflowSafetyTests

### Community 10 - "schemas.py"
Cohesion: 0.09
Nodes (21): Any, create_notification(), _database_datetime(), Persist every WatchTower, Human Agent, and OpenClaw notification here., CheckResult, NotificationCreate, inspect(), NotificationResponse (+13 more)

### Community 11 - "create_access_token"
Cohesion: 0.09
Nodes (8): create_access_token(), FakeProvider, SchedulerExecutionTests, ApplicationStartupTests, latest(), TelegramTestEndpointTests, latest(), _done()

### Community 15 - "scheduler.py"
Cohesion: 0.13
Nodes (18): lifespan(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event() (+10 more)

### Community 16 - "notifications-center.js"
Cohesion: 0.50
Nodes (7): loadPage(), poll(), queryUrl(), render(), renderCard(), requestItems(), updatePagination()

### Community 17 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

## Knowledge Gaps
- **22 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `Incremental Graph Update`, `Graphify Knowledge Graph` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `OSRelease`, `create_access_token`, `WebDashboardTests`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `OSRelease` connect `OSRelease` to `main.py`, `WebDashboardTests`, `NotificationCenterTests`, `schemas.py`, `create_access_token`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `NotificationCenterTests` connect `NotificationCenterTests` to `OSRelease`, `main.py`, `WebDashboardTests`, `schemas.py`, `create_access_token`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `User` (e.g. with `principal_for_username()` and `_authenticate_login()`) actually correct?**
  _`User` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._