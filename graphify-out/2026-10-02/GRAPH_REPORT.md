# Graph Report - os-release-tracker-updated  (2026-10-02)

## Corpus Check
- 43 files · ~21,498 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .example 1, .css 1)

## Summary
- 281 nodes · 767 edges · 16 communities (12 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- test_telegram.py
- main.py
- Release
- app.js
- auth.py
- Graphify Instructions
- versioning.py
- Dashboard Templates and Docs
- WebDashboardTests
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
4. `ReleaseEvent` - 17 edges
5. `Provider` - 17 edges
6. `WebDashboardTests` - 17 edges
7. `create_access_token()` - 15 edges
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

## Communities (16 total, 4 thin omitted)

### Community 0 - "test_telegram.py"
Cohesion: 0.22
Nodes (21): Settings, Base, OSRelease, ReleaseEvent, ReleaseHistory, BaseSettings, datetime, DeclarativeBase (+13 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (37): verify_access_token(), check(), create_web_session(), dashboard_page(), events(), events_page(), get_os(), health() (+29 more)

### Community 2 - "Release"
Cohesion: 0.21
Nodes (15): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+7 more)

### Community 3 - "app.js"
Cohesion: 0.22
Nodes (23): api(), dateText(), escapeHtml(), fillOsFilter(), initializeEvents(), initializeReleases(), initializeSettings(), loadDashboard() (+15 more)

### Community 4 - "auth.py"
Cohesion: 0.14
Nodes (16): authenticate_token(), generate_password_hash(), _hash_password(), Request, _request_origin(), verify_password(), login(), fastapi (+8 more)

### Community 5 - "Graphify Instructions"
Cohesion: 0.14
Nodes (14): Add and Watch Reference, Exports Reference, Extraction Specification, GitHub and Merge Reference, Hooks Reference, Query Reference, Transcription Reference, Incremental Update Reference (+6 more)

### Community 6 - "versioning.py"
Cohesion: 0.22
Nodes (10): compare_releases(), parse_version(), ParsedVersion, Compare stored and fetched releases; current-version classification is separate., Normalize major version and classify the release for deployment tracking., ReleaseComparison, ReleaseState, dataclasses (+2 more)

### Community 7 - "Dashboard Templates and Docs"
Cohesion: 0.20
Nodes (11): FastAPI Release Tracking Service, OS Release Tracker README, Release Semantics, Web Dashboard, Shared Dashboard Layout, Dashboard and Operating Systems Index, Release Events Page, Login Page (+3 more)

### Community 9 - "TelegramClientTests"
Cohesion: 0.09
Nodes (17): send(), notify(), Deliver to configured channels independently; report aggregate success., _failure(), Send a Telegram message without exposing credentials in errors or logs., send(), send_test(), TelegramSendResult (+9 more)

### Community 10 - "API Response Schemas"
Cohesion: 0.50
Nodes (4): CheckResult, BaseModel, ReleaseInfo, pydantic

### Community 11 - "create_access_token"
Cohesion: 0.11
Nodes (7): create_access_token(), FakeProvider, SchedulerExecutionTests, ApplicationStartupTests, TelegramTestEndpointTests, latest(), _done()

### Community 15 - "scheduler.py"
Cohesion: 0.24
Nodes (9): _add_check_job(), Run the shared check service and log failures without stopping APScheduler., Ensure the single UTC cron job exists on FastAPI's active event loop., scheduled_check(), start_scheduler(), apscheduler_schedulers_asyncio, apscheduler_schedulers_base, apscheduler_triggers_cron (+1 more)

## Knowledge Gaps
- **22 isolated node(s):** `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies`, `Incremental Graph Update`, `Graphify Knowledge Graph` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 73 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Release` connect `Release` to `test_telegram.py`, `versioning.py`, `WebDashboardTests`, `TelegramClientTests`, `create_access_token`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `WebDashboardTests` connect `WebDashboardTests` to `test_telegram.py`, `Release`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `OSRelease` connect `test_telegram.py` to `WebDashboardTests`, `main.py`, `create_access_token`, `TelegramClientTests`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ReleaseEvent` (e.g. with `events()` and `status()`) actually correct?**
  _`ReleaseEvent` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Docker Compose Configuration`, `Docker Deployment`, `Python Dependencies` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._