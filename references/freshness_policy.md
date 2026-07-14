# Living freshness policy

Assign cadence from consequence and volatility, not source age alone:

| Class | Default | Examples |
|---|---:|---|
| volatile | 7 days + event feeds | security, model behavior, pricing, policy, certification |
| active | 30 days | product documentation, APIs, repositories, releases |
| stable | 180 days | standards, mature methods, enduring empirical work |
| archival | 365 days + events | historical records and superseded releases |

Replay the full discovery query set quarterly and before a book or dataset
release. A successful HTTP response or unchanged content hash is not a semantic
review. Classify refreshes as `unchanged`, `cosmetic`, `material`, `breaking`,
`unreachable`, or `retracted`, then run impact analysis for every class except
unchanged.

Scheduled polling is read-only. It may retrieve, hash, classify, and report; it
must not edit canonical records, accept semantic changes, publish, push, or
release. A human-reviewed run applies accepted changes.
