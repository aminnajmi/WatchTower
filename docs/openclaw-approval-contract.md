# OpenClaw task approval contract

WatchTower approves and authorizes tasks. It never executes them. The contract
below matches `/opt/watchtower-approval/execution_core.py` supplied for review.

## Create and retrieve an approval

Create through the existing authenticated OpenClaw notification endpoint. The
server ignores display prose and metadata for task-bound requests and builds a
safe human-readable notification from the specification.

```http
POST /api/v1/notifications
Authorization: Bearer <OPENCLAW_NOTIFICATION_API_KEY>
Content-Type: application/json
```

```json
{
  "source": "openclaw",
  "title": "Inspect website",
  "message": "Display-only agent text",
  "requires_approval": true,
  "task_spec": {
    "version": 1,
    "task_type": "public_website_inspection",
    "url": "https://example.org/"
  }
}
```

`task_specification` is accepted as a creation alias. Both notification
serialization and the approval endpoint expose `task_spec` (the name required
by `execution_core.verify_approval`) and `task_specification` (the original
WatchTower proposal's name) with identical stored values. The approval endpoint
is `GET /api/v1/notifications/{notification_id}/approval` and requires the same
OpenClaw API key that created the request.

Task-bound approval responses contain `notification_id`, `action_id`,
`requires_approval`, `approval_status`, `approval_expires_at`, `task_spec`, and
`task_spec_sha256`. The task specification and digest are returned for pending,
approved, and denied decisions, including after the expiry timestamp. The
executor must reject non-approved or expired results. WatchTower rejects
approval decisions after expiry. `action_id` is the specification digest, so a
different specification gets a different action identity. Legacy approvals
remain readable but have no task binding and can never authorize execution.

## Task specification v1

The accepted object has exactly these fields; unknown fields are rejected:

```json
{"version":1,"task_type":"public_website_inspection","url":"https://example.org/"}
```

This is exactly the shape parsed by OpenClaw's `TaskSpec.parse`. Only HTTPS on
port 443/default port is accepted. URLs cannot contain credentials, a non-empty
query or fragment, controls, or a backslash (empty `?`/`#` delimiters are
stripped during normalization). The core also accepts an empty `@` userinfo
delimiter and removes it during normalization; non-empty credentials are
rejected. Hostnames are converted to lowercase IDNA
ASCII, lose a trailing dot, must be fully qualified and label-valid, and cannot
be IP literals. The path is preserved, or becomes `/` when empty. DNS answers,
redirects, and egress safety remain the executor's responsibility.

## Canonical JSON and digest

Canonicalization matches `TaskSpec.canonical_json()` in the supplied execution
core: serialize the three-field object with ASCII escapes enabled, keys sorted
lexicographically, compact `,` and `:` separators, and no extra fields; encode
that string as UTF-8 and calculate lowercase hexadecimal SHA-256. The normalized
URL and all task fields stored by WatchTower are the bytes covered by the hash.

Python reference:

```python
json.dumps(spec, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
```

JavaScript equivalent (including Python-compatible ASCII escaping):

```js
function quoteAscii(value) {
  return JSON.stringify(value).replace(/[^\x00-\x7f]/g, c =>
    `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`);
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(k => `${quoteAscii(k)}:${canonical(value[k])}`).join(',')}}`;
  }
  return typeof value === 'string' ? quoteAscii(value) : JSON.stringify(value);
}
const bytes = new TextEncoder().encode(canonical(taskSpec));
const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(b => b.toString(16).padStart(2, '0')).join('');
```

OpenClaw should pass the returned response to its existing `verify_approval`,
then retain its atomic at-most-once execution claim. WatchTower's action ID,
stored specification, and digest are all bound to the same canonical object.

## Executor network safeguards

Approval-time URL validation does not prevent DNS rebinding or unsafe redirects.
Before each connection, the executor must reject non-public resolved addresses,
connect to the validated address while preserving TLS hostname verification,
revalidate every redirect, limit redirects, and block private, loopback,
link-local, multicast, reserved, and metadata-service ranges at the network
layer. Disable uncontrolled proxies and never fetch URLs from display text.

## Deployment and rollback

1. Back up SQLite before upgrading.
2. Deploy the application; startup adds nullable task-binding columns without
   rebuilding the notifications table or changing historical rows.
3. Verify a newly created task's `task_spec`, action ID, and digest with the
   supplied `TaskSpec.parse`, `canonical_json`, and `verify_approval` code.
   Keep production execution disabled until that independent verification and
   the executor's network controls pass.
4. Roll back by deploying the previous application version. It can ignore the
   nullable columns; do not drop them or restore an old backup over newer
   approvals. Restoring the backup loses approvals created after the backup.

No production deployment or execution enablement was performed.
