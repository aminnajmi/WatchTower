# Graph Report - WatchTower  (2026-10-04)

## Corpus Check
- 45 files · ~28,374 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 377 nodes · 1051 edges · 16 communities (13 shown, 3 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 82 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4afde365`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_telegram.py
- main.py
- Release
- app.js
- WebDashboardTests
- Graphify Instructions
- ProductionConfigTests
- Dashboard Templates and Docs
- auth.py
- TelegramClientTests
- schemas.py
- SchedulerExecutionTests
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 36 edges
3. `OSRelease` - 29 edges
4. `Principal` - 21 edges
5. `WebDashboardTests` - 21 edges
6. `create_access_token()` - 19 edges
7. `User` - 19 edges
8. `Base` - 18 edges
9. `ReleaseEvent` - 17 edges
10. `Provider` - 17 edges

## Surprising Connections (you probably didn't know these)
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `UserManagementTests` --uses--> `Base`  [INFERRED]
  tests/test_users.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `SchedulerExecutionTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_scheduler.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (16 total, 3 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.13
Nodes (32): Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, check_all(), compare_releases(), parse_version() (+24 more)

### Community 1 - "main.py"
Cohesion: 0.08
Nodes (48): configure_session_factory_provider(), Allow the app's configured DB session factory to be injected in tests., verify_access_token(), account_page(), create_web_session(), dashboard_page(), events(), events_page() (+40 more)

### Community 2 - "Release"
Cohesion: 0.18
Nodes (17): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+9 more)

### Community 3 - "app.js"
Cohesion: 0.20
Nodes (29): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+21 more)

### Community 4 - "WebDashboardTests"
Cohesion: 0.14
Nodes (3): generate_password_hash(), getpass, WebDashboardTests

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "ProductionConfigTests"
Cohesion: 0.23
Nodes (6): Fail startup on missing/unsafe credentials in production mode., Settings, ensure_sqlite_directory(), init_db(), BaseSettings, ProductionConfigTests

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 8 - "auth.py"
Cohesion: 0.06
Nodes (46): authenticate_token(), create_access_token(), _hash_password(), hash_user_password(), Principal, principal_for_username(), Request, Resolve every request against current DB state so disable takes effect… (+38 more)

### Community 9 - "TelegramClientTests"
Cohesion: 0.09
Nodes (15): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., send(), send_test(), TelegramSendResult (+7 more)

### Community 10 - "schemas.py"
Cohesion: 0.16
Nodes (10): CheckResult, PasswordChange, PasswordReset, BaseModel, ReleaseInfo, UserCreate, UserUpdate, field_validator (+2 more)

### Community 11 - "SchedulerExecutionTests"
Cohesion: 0.19
Nodes (4): FakeProvider, SchedulerExecutionTests, latest(), _done()

### Community 15 - "scheduler.py"
Cohesion: 0.15
Nodes (16): _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Run the shared check service without taking down APScheduler., Record real APScheduler lifecycle events for the tracked job., _record_job_event(), scheduled_check(), start_scheduler() (+8 more)

## Knowledge Gaps
- **22 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `Incremental Graph Update`, `Graphify Knowledge Graph` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 96 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `TelegramClientTests`, `SchedulerExecutionTests`, `WebDashboardTests`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `OSRelease` connect `test_telegram.py` to `main.py`, `Release`, `WebDashboardTests`, `auth.py`, `TelegramClientTests`, `SchedulerExecutionTests`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `WebDashboardTests` to `test_telegram.py`, `Release`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Principal` (e.g. with `change_own_password()` and `create_user()`) actually correct?**
  _`Principal` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `WebDashboardTests` (e.g. with `Base` and `OSRelease`) actually correct?**
  _`WebDashboardTests` has 5 INFERRED edges - model-reasoned connections that need verification._