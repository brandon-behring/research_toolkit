# URL freshness check protocol

Detailed protocol for `/url-freshness-check`. Deterministic HEAD-checking with GET retry; bot-blocked allowlist; categorized output.

> Historical compatibility reference: `/url-freshness-check` is not one of the
> six current plugin skills, and its raw `curl` examples are not the approved
> source-capture boundary. Current dossier refreshes use
> `/research-toolkit:freshness` and the public-only raw cache path. Browser
> execution is disabled pending a verified process sandbox and default-deny
> network boundary.

## When to use this vs. `/freshness-audit`

This protocol covers **HTTP liveness** on any markdown folder: 2xx / 3xx / 4xx / 5xx / timeout categorization, with retries and bot-blocked allowlist handling. It works on `docs/`, blog folders, or any place URLs are embedded.

For **strict-live v2 projects** (those with `evidence_ledger.yml`, `cache_manifest.yml`, and `claim_graph.jsonl`), the corresponding tool is `/freshness-audit`. That skill validates *evidence integrity* — stale entries past their `stale_after_days` window, missing evidence_id references, hash mismatches between cache_manifest entries and on-disk blobs, weak claims (confidence < 0.8), and conflicts. It also re-fetches stale primary sources and rebuilds the dashboard.

The two are orthogonal and often run together on v2 projects:
- `/url-freshness-check` on the rendered agent-index markdown → catches dead URLs in synthesis prose.
- `/freshness-audit` on the project root → catches evidence rot in ledgers.

Both stay in scope; neither subsumes the other.

## The cache is content-addressed: one URL can have multiple valid cache_ids

`scripts/cache_source.py` keys the cache by **content hash, not URL**. The same
URL can return different raw bytes at different dates or after a redirect, so
different bytes produce different `sha256` and `cache_id` values. Historical
material may also contain `playwright_rendered` captures from the retired
browser path. Move those records and bytes to a separately labelled, read-only
quarantine: the current manifest validator rejects that method. Do not create
new browser captures or interpret the legacy method as a current safety approval.

Practical consequences when reasoning about a cache:

- Do **not** treat two cache entries that share a `source_url` as a bug or a
  dedup target; each byte snapshot may anchor different excerpts.
- An excerpt anchored against one render verifies only against *that* render's
  cached bytes; the offsets are not portable between the two captures.
- A current `cache_manifest.yml` may record only the static `urllib` method.
  Legacy browser records belong in quarantine, not a validated current manifest.

The cache command records sanitized requested provenance in `source_url` and a
sanitized `final_url` whenever its effective URL changes. A liveness report's
curl `url_effective` belongs to a separate request and does not retroactively
establish cache provenance. Keep requested, canonical, and final identity
decisions distinct.

(Surfaced as `ctxasm-3` in the context-assembly pilot.)

## Bash chunking pattern

The check should run in parallel chunks for efficiency. ~50 URLs per chunk, ~10 chunks in parallel:

```bash
#!/usr/bin/env bash
set -uo pipefail

mkdir -p .url_check_tmp
# Step 1: extract all unique URLs from the target folder.
# Use the positive char-class form; the negative char-class version returns
# 0 matches on some macOS grep builds.
grep -hroE 'https?://[a-zA-Z0-9./?=&_~%#:+-]+' "$TARGET_FOLDER" \
  | sort -u \
  | sed 's/[\.,:;]\+$//' \
  > .url_check_tmp/urls.txt

# Step 2: split into chunks.
split -l 50 .url_check_tmp/urls.txt .url_check_tmp/chunk_

# Step 3: HEAD-check each chunk in parallel.
# Output columns: status<TAB>effective_url<TAB>requested_url.
for chunk in .url_check_tmp/chunk_*; do
  (
    while IFS= read -r url; do
      result=$(curl -s -o /dev/null -w $'%{http_code}\t%{url_effective}' \
                    -L -m 15 -A "Mozilla/5.0 research_toolkit/2.0" \
                    -I "$url" 2>/dev/null)
      if [[ $? -ne 0 || -z "$result" ]]; then
        result=$'000\t'"$url"
      fi
      printf '%s\t%s\n' "$result" "$url"
    done < "$chunk" > "$chunk.results"
  ) &
done
wait

# Step 4: collect all results.
cat .url_check_tmp/chunk_*.results | sort -u > .url_check_tmp/results.txt
```

## HEAD vs GET retry

Some sites (OpenAI, Microsoft Learn, Cloudflare-fronted) reject HEAD requests but accept GET. After the initial HEAD pass, retry every 4xx URL with GET (range header to avoid downloading the body):

```bash
while IFS= read -r line; do
  IFS=$'\t' read -r status effective_url requested_url <<< "$line"
  if [[ "$status" =~ ^4 ]]; then
    retry=$(curl -s -o /dev/null -w $'%{http_code}\t%{url_effective}' \
                 -L -m 15 -A "Mozilla/5.0 research_toolkit/2.0" \
                 -H "Range: bytes=0-1024" "$requested_url" 2>/dev/null)
    if [[ $? -ne 0 || -z "$retry" ]]; then
      retry=$'000\t'"$requested_url"
    fi
    printf '%s\t%s\n' "$retry" "$requested_url"
  else
    printf '%s\t%s\t%s\n' "$status" "$effective_url" "$requested_url"
  fi
done < .url_check_tmp/results.txt > .url_check_tmp/results_retry.txt
```

This liveness-only compatibility report now captures curl's effective URL. It
must not copy query credentials into a committed report: inspect or remove
query-bearing URLs before the check. The effective URL is evidence about this
specific liveness request only and is not interchangeable with a cache
capture's missing final-URL provenance.

## Bot-blocked allowlist

Known sites that legitimately reject HEAD/GET from non-browser User-Agents. URLs matching these domains are flagged "bot-blocked, not broken" rather than failed:

| Domain pattern | Reason |
|---|---|
| `openai.com/*` | OpenAI blocks generic UAs aggressively |
| `learn.microsoft.com/*` | Anti-scraping rate-limiting |
| `azure.microsoft.com/*` | Same |
| `app.grayswan.ai/*` | Auth-walled product pages |
| `gandalf.lakera.ai/*` | Same |
| `aivillage.org/*` | Cloudflare challenge |
| `simonwillison.net/*` | Sometimes returns 403 to non-browser UAs |
| `*.gov.uk/*` | UK gov sites have strict UA rules |

Maintain this allowlist in the skill body. Add new entries as they're discovered during real-world use; the BURN_IN_NOTES.md tracks which sites needed allowlisting.

## Output report format

The skill writes a report to `<target>/../url_check_report.md` by default (or a user-specified path). Keeping the report outside the target folder prevents it from being counted as a synthesis artifact:

```markdown
# URL Freshness Report

Generated: 2026-05-06
Target: docs/prompt_injection_research/

## Summary

- total: 674
- ok: 595
- broken: 7
- bot-blocked: 32
- redirected: 40

## Broken URLs (hard 404s)

### docs/prompt_injection_research/05_datasets_and_benchmarks.md
- https://example.com/blog/that-was-renamed-or-deleted

### docs/prompt_injection_research/06_tools_and_vendors.md
- https://another-broken-link.example.com/

## Bot-blocked URLs (flagged for manual review)

- https://openai.com/blog/some-post (allowlisted: openai.com)
- ...

## Redirected URLs (effective liveness URL recorded)

- https://example.com/old → https://example.com/new
- ...
```

The validator (`validators/url_check_report.py`) checks the report has the required H1, Summary section with stats, and Generated date.

## Optional `--inline` mode

When `--inline` flag is passed, the skill ALSO annotates hard-404 URLs in-place in the source markdown files:

```markdown
- **Source:** https://broken-url.example.com/ (broken-link as of 2026-05-06)
```

The user can then run `/dossier-audit` to decide whether to fix each broken link (rename, generalize, drop the entry).

`--inline` modifies source files; default mode does not. Use `--inline` only when comfortable with in-place edits.

## False-positive sources

Common reasons URLs report broken when they're actually fine:
1. **HTTPS cert errors on .gov sites** — usually transient; retry.
2. **DNS issues on the user's network** — rerun later.
3. **Rate limiting from the user's IP** — wait 10 minutes; rerun.
4. **GitHub raw URLs (`raw.githubusercontent.com`)** — rate-limit aggressively; allowlist for high-volume runs.

If a URL fails repeatedly across multiple runs at different times, treat it as actually broken.
