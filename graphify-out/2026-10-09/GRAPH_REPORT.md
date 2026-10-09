# Graph Report - WatchTower  (2026-10-09)

## Corpus Check
- 51 files · ~37,594 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 576 nodes · 1546 edges · 26 communities (16 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 115 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d8a19f01`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- auth.py
- telegram.py
- app.js
- Release
- scheduler.py
- TidioMonitor
- schemas.py
- SchedulerExecutionTests
- Shared Dashboard Layout
- Graphify Skill
- DeploymentHealthCheckTests
- ._attach_browser_diagnostics
- deployment-health-check.sh
- DeploymentWorkflowSafetyTests
- Persistent Tracker Data Volume
- test_tidio.py
- Python Runtime Dependencies
- WatchTower Logo
- shutil
- WebDashboardTests
- TidioSnapshot
- test_tidio_manual_verification_keeps_live_browser
- test_tidio_pending_or_expired_challenge_can_be_checked_again
- test_tidio_disconnect_disables_monitoring_and_removes_saved_credentials
- test_tidio_reconnect_uses_bounded_backoff

## God Nodes (most connected - your core abstractions)
1. `TidioMonitor` - 54 edges
2. `Release` - 45 edges
3. `Principal` - 33 edges
4. `OSRelease` - 29 edges
5. `TidioSnapshot` - 24 edges
6. `create_access_token()` - 23 edges
7. `WebDashboardTests` - 21 edges
8. `Base` - 20 edges
9. `User` - 19 edges
10. `api()` - 18 edges

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

## Communities (26 total, 10 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.05
Nodes (101): authenticate_token(), Principal, principal_for_username(), Request, Resolve every request against current DB state so disable takes effect…, _request_origin(), require_admin(), verify_access_token() (+93 more)

### Community 1 - "auth.py"
Cohesion: 0.06
Nodes (48): configure_session_factory_provider(), create_access_token(), generate_password_hash(), _hash_password(), hash_user_password(), Allow the app's configured DB session factory to be injected in tests., verify_password(), Base (+40 more)

### Community 2 - "telegram.py"
Cohesion: 0.10
Nodes (18): Any, Notification, send(), notify(), Deliver to configured channels independently; report aggregate success., create_notification(), metadata_for(), datetime (+10 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (44): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+36 more)

### Community 4 - "Release"
Cohesion: 0.16
Nodes (20): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+12 more)

### Community 5 - "scheduler.py"
Cohesion: 0.08
Nodes (26): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), status(), ensure_sqlite_directory(), init_db(), _add_check_job(), get_scheduler() (+18 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.19
Nodes (4): TidioConnection, TidioMonitor, Exception, Fernet

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

### Community 12 - "._attach_browser_diagnostics"
Cohesion: 0.24
Nodes (5): log_console_error(), log_failed_request(), log_script_response(), Page, test_tidio_browser_diagnostics_log_failures_without_query_secrets()

### Community 13 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 16 - "test_tidio.py"
Cohesion: 0.09
Nodes (18): datetime, Tidio needs a human to finish an MFA or CAPTCHA challenge., VerificationRequired, asyncio, cryptography_fernet, playwright_async_api, pytest, RuntimeError (+10 more)

### Community 22 - "TidioSnapshot"
Cohesion: 0.12
Nodes (9): TidioSnapshot, test_tidio_connect_reports_connected_only_after_successful_check(), successful_check(), test_tidio_rejected_verification_updates_status_and_keeps_reconnect_available(), test_tidio_shutdown_cancels_waiter_and_closes_verification_browser(), run(), test_tidio_status_payload_is_safe_and_reports_monitor_state(), test_tidio_verification_resume_opens_inbox_and_restarts_monitor() (+1 more)

### Community 23 - "test_tidio_manual_verification_keeps_live_browser"
Cohesion: 0.22
Nodes (3): test_tidio_manual_verification_keeps_live_browser(), ensure_browser(), test_tidio_open_login_opens_manual_page_without_submitting_credentials()

## Knowledge Gaps
- **24 isolated node(s):** `Incremental Graph Update`, `Graphify Knowledge Graph`, `Graph Query and Explanation`, `Semantic Extraction`, `Add and Watch Reference` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 140 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `._attach_browser_diagnostics`, `test_tidio.py`, `TidioSnapshot`, `test_tidio_manual_verification_keeps_live_browser`, `test_tidio_pending_or_expired_challenge_can_be_checked_again`, `test_tidio_disconnect_disables_monitoring_and_removes_saved_credentials`, `test_tidio_reconnect_uses_bounded_backoff`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `SchedulerExecutionTests`, `auth.py`, `telegram.py`, `WebDashboardTests`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `DeploymentHealthCheckTests` connect `DeploymentHealthCheckTests` to `auth.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `TidioMonitor` (e.g. with `TidioConnection` and `test_tidio_browser_diagnostics_log_failures_without_query_secrets()`) actually correct?**
  _`TidioMonitor` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._