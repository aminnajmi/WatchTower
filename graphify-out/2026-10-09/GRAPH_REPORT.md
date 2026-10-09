# Graph Report - WatchTower  (2026-10-09)

## Corpus Check
- 51 files · ~36,723 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .example 1, .db-shm 1)

## Summary
- 558 nodes · 1493 edges · 31 communities (21 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b23be6c2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- test_telegram.py
- Principal
- app.js
- Release
- scheduler.py
- TidioMonitor
- schemas.py
- SchedulerExecutionTests
- Shared Dashboard Layout
- Graphify Skill
- DeploymentHealthCheckTests
- get
- deployment-health-check.sh
- DeploymentWorkflowSafetyTests
- Persistent Tracker Data Volume
- test_tidio.py
- Notification
- Python Runtime Dependencies
- WatchTower Logo
- shutil
- auth.py
- TidioSnapshot
- test_tidio_manual_verification_keeps_live_browser
- NotificationCenterTests
- principal_for_username
- tidio.py
- test_tidio_disconnect_disables_monitoring_and_removes_saved_credentials
- test_tidio_reconnect_uses_bounded_backoff
- test_tidio_rejected_verification_updates_status_and_keeps_reconnect_available
- sanitized_validation_error

## God Nodes (most connected - your core abstractions)
1. `Release` - 45 edges
2. `TidioMonitor` - 45 edges
3. `OSRelease` - 29 edges
4. `Principal` - 25 edges
5. `create_access_token()` - 23 edges
6. `TidioSnapshot` - 23 edges
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

## Communities (31 total, 10 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.12
Nodes (30): check(), deny_notification(), disable_user(), enable_user(), get_os(), list_os(), logout(), NotificationDenyRequest (+22 more)

### Community 1 - "test_telegram.py"
Cohesion: 0.08
Nodes (44): create_access_token(), Base, _configure_sqlite_connection(), OSRelease, ReleaseEvent, ReleaseHistory, send(), notify() (+36 more)

### Community 2 - "Principal"
Cohesion: 0.13
Nodes (23): hash_user_password(), Principal, require_admin(), verify_user_password(), _authenticate_login(), change_own_password(), create_user(), delete_user() (+15 more)

### Community 3 - "app.js"
Cohesion: 0.13
Nodes (44): api(), dateText(), escapeHtml(), fillOsFilter(), handleUserAction(), initializeAccount(), initializeEvents(), initializeLogin() (+36 more)

### Community 4 - "Release"
Cohesion: 0.15
Nodes (22): ABC, AlmaLinuxProvider, ArchLinuxProvider, Provider, Release, CentOSProvider, DebianProvider, FedoraProvider (+14 more)

### Community 5 - "scheduler.py"
Cohesion: 0.08
Nodes (24): Fail startup on missing/unsafe credentials in production mode., Settings, lifespan(), ensure_sqlite_directory(), init_db(), _add_check_job(), get_scheduler(), Create and start one scheduler on FastAPI's currently running loop. (+16 more)

### Community 6 - "TidioMonitor"
Cohesion: 0.20
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

### Community 12 - "get"
Cohesion: 0.18
Nodes (26): account_page(), dashboard_page(), events(), events_page(), get_notification(), health(), home(), login_page() (+18 more)

### Community 13 - "deployment-health-check.sh"
Cohesion: 1.00
Nodes (3): diagnose(), run_docker(), deployment-health-check.sh script

### Community 16 - "test_tidio.py"
Cohesion: 0.10
Nodes (9): pytest, test_tidio_browser_startup_failure_is_logged_and_cleaned_up(), test_tidio_encryption_requires_dedicated_stable_key(), test_tidio_mfa_stops_automatic_reconnect(), test_tidio_monitor_does_not_retry_before_backoff_deadline(), test_tidio_password_encryption_round_trip(), test_tidio_pending_or_expired_challenge_can_be_checked_again(), test_tidio_snapshot_defaults() (+1 more)

### Community 17 - "Notification"
Cohesion: 0.20
Nodes (15): Any, approve_notification(), create_openclaw_notification(), list_notifications(), _openclaw_authorized(), datetime, _serialize_notification(), test_notification() (+7 more)

### Community 21 - "auth.py"
Cohesion: 0.06
Nodes (18): authenticate_token(), configure_session_factory_provider(), generate_password_hash(), _hash_password(), Request, Allow the app's configured DB session factory to be injected in tests., _request_origin(), verify_password() (+10 more)

### Community 22 - "TidioSnapshot"
Cohesion: 0.19
Nodes (7): TidioSnapshot, test_tidio_connect_reports_connected_only_after_successful_check(), successful_check(), test_tidio_shutdown_cancels_waiter_and_closes_verification_browser(), run(), test_tidio_verification_resume_opens_inbox_and_restarts_monitor(), check_once()

### Community 23 - "test_tidio_manual_verification_keeps_live_browser"
Cohesion: 0.20
Nodes (4): Tidio needs a human to finish an MFA or CAPTCHA challenge., VerificationRequired, RuntimeError, test_tidio_manual_verification_keeps_live_browser()

### Community 25 - "principal_for_username"
Cohesion: 0.25
Nodes (8): principal_for_username(), Resolve every request against current DB state so disable takes effect…, verify_access_token(), create_web_session(), login_form(), POST fallback for browsers when client-side JavaScript is unavailable., _set_session_cookie(), WebSessionRequest

### Community 26 - "tidio.py"
Cohesion: 0.29
Nodes (5): datetime, cryptography_fernet, playwright_async_api, time, urllib_parse

### Community 30 - "sanitized_validation_error"
Cohesion: 0.67
Nodes (3): sanitized_validation_error(), exception_handler, RequestValidationError

## Knowledge Gaps
- **24 isolated node(s):** `Incremental Graph Update`, `Graphify Knowledge Graph`, `Graph Query and Explanation`, `Semantic Extraction`, `Add and Watch Reference` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 137 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TidioMonitor` connect `TidioMonitor` to `test_tidio.py`, `TidioSnapshot`, `test_tidio_manual_verification_keeps_live_browser`, `tidio.py`, `test_tidio_disconnect_disables_monitoring_and_removes_saved_credentials`, `test_tidio_reconnect_uses_bounded_backoff`, `test_tidio_rejected_verification_updates_status_and_keeps_reconnect_available`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `Release` connect `Release` to `SchedulerExecutionTests`, `test_telegram.py`, `auth.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `DeploymentHealthCheckTests` connect `DeploymentHealthCheckTests` to `test_telegram.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Release` (e.g. with `AlmaLinuxProvider` and `ArchLinuxProvider`) actually correct?**
  _`Release` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OSRelease` (e.g. with `events()` and `get_os()`) actually correct?**
  _`OSRelease` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Principal` (e.g. with `approve_notification()` and `change_own_password()`) actually correct?**
  _`Principal` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Incremental Graph Update`, `Graphify Knowledge Graph`, `Graph Query and Explanation` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._