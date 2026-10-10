# OpenClaw task approval contract

WatchTower approves and authorizes tasks. It never runs them. OpenClaw remains
responsible for fetching, verifying, and executing an approved task.

## Create a request

Use the existing authenticated OpenClaw notification endpoint. The API key is
sent as a bearer token; do not send a client-computed digest or decision fields.

```http
POST /api/v1/notifications
Authorization: Bearer <OPENCLAW_NOTIFICATION_API_KEY>
Content-Type: application/json
```

```json
{
  "source": "openclaw",
  "title": "Inspect the public website",
  "message": "Review the public pages within the requested scope.",
  "severity": "warning",
  "requires_approval": true,
  "task_specification": {
    "schema_version": 1,
    "task_type": "public_website_inspection",
    "target": "https://operavps.com",
    "parameters": {"scope": "public_pages", "max_pages": 5}
  }
}
```

Successful task-bound responses contain the stored specification,
`task_schema_version`, `task_spec_sha256`, and a stable `action_id`. The
approval endpoint remains `GET /api/v1/notifications/{id}/approval`; it returns
the approval state and, for bound tasks, the exact specification and digest.
The endpoint is authenticated with the same OpenClaw key that created the
request (credential fingerprint ownership).

Legacy approval requests keep their prior response shape. Missing task binding
means the response cannot authorize execution. A task-bound request is pending
until an authenticated human approves or denies it. Decisions are one-way and
atomic; expired requests cannot be approved. Human identity is derived from
WatchTower JWT authentication and is never accepted from the request body.

## Task specification v1

Only `public_website_inspection` is supported. Fields are strict and unknown
fields are rejected:

- `schema_version`: integer `1`
- `task_type`: string `public_website_inspection`
- `target`: public HTTP or HTTPS URL; credentials, query strings, fragments,
  localhost/internal names, private/reserved IP literals, invalid or ambiguous
  path encodings, credential-like path components, and unsupported schemes are rejected
- `parameters.scope`: exactly `public_pages`
- `parameters.max_pages`: integer from 1 through 20 (default 5)

The server lowercases the scheme and hostname, converts internationalized
hostnames to IDNA ASCII, removes a trailing hostname dot and default port,
ensures an empty path becomes `/`, and uppercases valid percent-escape hex
digits in the path. The response contains this normalized target.

## Canonical JSON and digest

The digest is lowercase hexadecimal SHA-256 of the UTF-8 encoding of canonical
JSON for the complete normalized specification (including defaulted fields).
Canonical JSON uses lexicographically sorted object keys, no insignificant
whitespace, UTF-8 characters without ASCII escaping, and no NaN/Infinity values.
Arrays retain order. V1 contains only fixed ASCII keys, fixed ASCII enum values,
one normalized URL string, and integer parameters, avoiding cross-language
number formatting ambiguity.

Python reference:

```python
json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
```

JavaScript reference for this fixed v1 shape (sorting keys recursively):

```js
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
const bytes = new TextEncoder().encode(canonical(spec));
const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(b => b.toString(16).padStart(2, '0')).join('');
```

OpenClaw must independently validate the schema, canonicalize the returned
specification, compare the computed digest with `task_spec_sha256`, require
`approval_status === "approved"`, and enforce the returned expiry before
execution. Treat title, message, metadata, and other agent-authored descriptive
text as display-only; only the versioned specification defines the operation.
Keep OpenClaw's existing atomic at-most-once claim behavior.

The OpenClaw `execution_core.py` mentioned in the task was not available in this
workspace, so byte-for-byte compatibility with that implementation is
unverified. Compare its validator and canonicalizer against this contract
before enabling execution.

## Network safety for the executor

URL validation at approval time cannot protect a later connection from DNS
rebinding, a changed DNS answer, redirects, proxies, or a compromised public
host. OpenClaw must resolve immediately before each connection, reject every
non-global resolved address (including IPv4-mapped IPv6), connect only to the
validated address while preserving TLS hostname verification, revalidate each
redirect and limit redirect count, and block private, loopback, link-local,
multicast, reserved, and metadata-service ranges at the network layer. Disable
environment-provided proxies unless explicitly controlled. Do not fetch URLs
from descriptive fields.

## Deployment and rollback

1. Back up the SQLite database before upgrading.
2. Deploy the application build; startup applies additive nullable columns to
   `notifications`, preserving all existing rows.
3. Confirm the approval API returns a digest for a newly created request and
   no task binding for legacy rows. Keep OpenClaw execution disabled until its
   canonicalizer and network controls are verified.
4. Roll back by deploying the prior application version. The added columns are
   nullable and are safe for the prior version to ignore; do not drop them or
   restore an old database over newer approvals. Restore the backup only if the
   database itself must be recovered, accepting that approvals created after
   the backup will be lost.

Example request and response details are covered above. Production deployment
is intentionally not performed by this change.
