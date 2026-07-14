# Rights and visibility vocabulary mapping

This reference prevents the legacy strict-live cache contract, canonical
Toolkit v1 dossiers, and synthesis export envelopes from silently assigning
different meanings to the same source.

Rights and visibility are independent. `visibility` describes who can reach a
source; `rights_status` describes what may be reused or redistributed. Neither
source authority nor public URL reachability supplies reuse permission.

## Conservative cache invariant

A strict-live cache entry may set `restricted: false` only when both of these
statements are explicit:

- `rights_status: public`
- `visibility: public`

Every other combination—including a missing field—requires
`restricted: true`. This flag governs the cached body, not whether identifiers,
hashes, citations, and semantic research metadata may be exported.

## Legacy cache to canonical Toolkit v1

| Strict-live cache v2 | Canonical Toolkit v1 | Meaning |
|---|---|---|
| `rights_status: public` | `rights_status: public` | Explicit permission represented as public |
| `rights_status: private_use` | `rights_status: private-use` | Local/private research use only |
| `rights_status: restricted` | `rights_status: restricted` | Reuse or redistribution is restricted |
| `rights_status: unknown` | `rights_status: unknown` | Permission has not been established |
| `rights_status: cache_only` | `rights_status: restricted` | Body stays in the local cache; preserve the narrower legacy value in provenance |
| `visibility: public` | `visibility: public` | Publicly reachable |
| `visibility: authenticated` | `visibility: restricted` | Authentication or entitlement required |
| `visibility: private` | `visibility: private` | Private/local source |
| missing visibility | `visibility: unknown` | Access state was not recorded |

The underscore-to-hyphen change for `private_use` / `private-use` is a schema
mapping, not a rights upgrade. Importers must never map an unrecognized value to
`public`.

## Synthesis export behavior

`synthesis_export.jsonl` is a metadata envelope. It may carry cache IDs,
SHA-256 digests, source citations, and semantic claim text for any rights state,
but it must not carry cached bodies, raw paths, extracted excerpts, or bulk
quotes. Each exported `cache_blob` payload includes a `rights_policy` object in
the `strict-live-cache-v2` vocabulary and always declares
`body_exported: false`.

Restricted, private-use, cache-only, and unknown entries therefore do not block
metadata-only export. A contradictory cache policy, an unresolved cache ID, or
a body-bearing cache record does block export.

## Canonical release boundary

Canonical dossiers may retain restricted, private-use, or unknown evidence for
local research and review. A release is a different boundary: every source must
have explicit public rights and public visibility, and every body-bearing
evidence excerpt must have explicit public rights. Non-public material must be
removed or replaced with permitted metadata before generating a release; a
waiver string does not silently upgrade its rights.
