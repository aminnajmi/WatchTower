# Graph Report - WatchTower  (2026-10-03)

## Corpus Check
- 44 files · ~23,901 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 312 nodes · 831 edges · 15 communities (12 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 54 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8347a6f1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_telegram.py
- main.py
- Release
- app.js
- auth.py
- Graphify Instructions
- ProductionConfigTests
- Dashboard Templates and Docs
- TelegramClientTests
- API Response Schemas
- create_access_token
- Compose Configuration
- Container Deployment
- Python Dependencies
- scheduler.py

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `get()` - 31 edges
3. `OSRelease` - 26 edges
4. `WebDashboardTests` - 21 edges
5. `create_access_token()` - 17 edges
6. `ReleaseEvent` - 17 edges
7. `Provider` - 17 edges
8. `Base` - 15 edges
9. `TelegramClientTests` - 14 edges
10. `check_all()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `SchedulerExecutionTests` --uses--> `Base`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `Base`  [INFERRED]
  tests/test_telegram.py → app/models.py
- `WebDashboardTests` --uses--> `Base`  [INFERRED]
  tests/test_web.py → app/models.py
- `SchedulerExecutionTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_scheduler.py → app/models.py
- `TelegramClientTests` --uses--> `OSRelease`  [INFERRED]
  tests/test_telegram.py → app/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build Pipeline** — _codex_skills_graphify_skill_graphify, _codex_skills_graphify_references_extraction_spec_graphify, _codex_skills_graphify_references_github_and_merge_graphify [EXTRACTED 1.00]

## Communities (15 total, 3 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.13
Nodes (34): Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, notify(), Deliver to configured channels independently; report aggregate success., check_all() (+26 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (40): verify_access_token(), check(), create_web_session(), dashboard_page(), events(), events_page(), get_os(), health() (+32 more)

### Community 2 - "Release"
Cohesion: 0.19
Nodes (16): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+8 more)

### Community 3 - "app.js"
Cohesion: 0.21
Nodes (25): api(), dateText(), escapeHtml(), fillOsFilter(), initializeEvents(), initializeLogin(), initializeReleases(), initializeSettings() (+17 more)

### Community 4 - "auth.py"
Cohesion: 0.09
Nodes (15): authenticate_token(), generate_password_hash(), _hash_password(), Request, _request_origin(), verify_password(), fastapi_security, getpass (+7 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "ProductionConfigTests"
Cohesion: 0.33
Nodes (4): Fail startup on missing/unsafe credentials in production mode., Settings, BaseSettings, ProductionConfigTests

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramClientTests"
Cohesion: 0.09
Nodes (14): send(), _failure(), Send a Telegram message without exposing credentials in errors or logs., send(), send_test(), TelegramSendResult, httpx, logging (+6 more)

### Community 10 - "API Response Schemas"
Cohesion: 0.50
Nodes (4): CheckResult, BaseModel, ReleaseInfo, pydantic

### Community 11 - "create_access_token"
Cohesion: 0.10
Nodes (7): create_access_token(), FakeProvider, SchedulerExecutionTests, ApplicationStartupTests, TelegramTestEndpointTests, latest(), _done()

### Community 15 - "scheduler.py"
Cohesion: 0.11
Nodes (21): lifespan(), ensure_sqlite_directory(), init_db(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop., Stop and discard the scheduler for the current application lifecycle., Run the shared check service without taking down APScheduler. (+13 more)

## Knowledge Gaps
- **22 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `Incremental Graph Update`, `Graphify Knowledge Graph` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 83 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `TelegramClientTests`, `create_access_token`, `auth.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `auth.py` to `test_telegram.py`, `Release`, `create_access_token`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `OSRelease` connect `test_telegram.py` to `main.py`, `create_access_token`, `auth.py`, `TelegramClientTests`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `WebDashboardTests` (e.g. with `Base` and `OSRelease`) actually correct?**
  _`WebDashboardTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._