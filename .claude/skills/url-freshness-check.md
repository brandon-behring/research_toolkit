---
name: url-freshness-check
description: HEAD-check every URL in a markdown collection. Categorizes results (2xx / 3xx redirect / 4xx broken / 5xx / timeout); maintains a bot-blocked allowlist; writes a categorized report. Optional --inline mode annotates hard-404 URLs in-place. Invokable on any markdown folder, not just research dossiers.
allowed-tools: Read, Bash, Edit
---

# /url-freshness-check — HEAD-check URLs in a markdown collection

## Usage

```
/url-freshness-check <target_folder> [--inline] [--report <path>]
```

**Examples:**
```
/url-freshness-check ~/some_project/docs/timeseries_research/
/url-freshness-check ~/some_project/docs/jailbreak_research/ --inline
/url-freshness-check ~/Claude/research_toolkit/tests/fixtures/prompt_injection_snapshot/real/agent_index/ --report /tmp/url_check.md
```

**Default report path**: `<target_folder>/../url_check_report.md` (outside the
target synthesis folder so the report does not become an agent-index artifact).

## When to use

- Before publishing a research synthesis externally.
- After a long gap (≥6 months) where URLs may have drifted to 404.
- As a one-time check on any markdown folder — not specific to research_toolkit artifacts. Use it on `docs/`, blog posts, anywhere with embedded URLs.

**Upstream:** any markdown collection. Most commonly invoked on `/agent-index` output.
**Downstream:** the user reviews the report; optionally re-runs with `--inline` to annotate the source files.

## Workflow

### Phase 1: load reference

Read `~/Claude/research_toolkit/references/url_check_protocol.md` — covers the bash chunking pattern, HEAD-vs-GET retry, bot-blocked allowlist, and report format.

### Phase 2: extract URLs

Walk the target folder; extract all unique URLs from every `*.md` file. **Use the positive char-class regex** — the negative char-class form silently returns 0 URLs on macOS grep (high-priority BURN_IN finding from eval-methodology):

```bash
mkdir -p .url_check_tmp
grep -hroE 'https?://[a-zA-Z0-9./?=&_~%#:+-]+' "$TARGET_FOLDER" \
  | sort -u \
  | sed 's/[\.,:;]\+$//' \
  > .url_check_tmp/urls.txt
```

**Do NOT use** the negative char-class form `[^[:space:]\)\]"\<]+` — on macOS `grep -E`, the bracketed escape sequences silently produce 0 matches (no error). eval-methodology lost an entire URL-check run to this. The positive form `[a-zA-Z0-9./?=&_~%#:+-]+` works on both macOS and Linux grep.

Trailing punctuation cleanup matters — Markdown often appends `.`, `,`, or `:` to URL boundaries.

#### Sanity check

Before continuing, verify URL extraction returned a sensible count:

```bash
N=$(wc -l < .url_check_tmp/urls.txt)
test "$N" -gt 0 || { echo "FATAL: extracted 0 URLs — regex bug?" >&2; exit 1; }
echo "Extracted $N unique URLs"
```

A well-rendered agent_index typically has ~1.5–2 URLs per entry. If `$N` is below ~50% of that estimate, the regex is broken — investigate before proceeding.

### Phase 3: HEAD-check (inline curl when N>50)

**Performance note (PEFT BURN_IN):** when running this skill via a subagent on a 100+ URL artifact, the WebFetch tool path can rate-limit / time out. For artifacts with N ≥ 50 URLs, use the inline `curl -L -G` bulk-check below, which completes in ~60 seconds for 100+ URLs without hitting WebFetch quotas. Use the WebFetch path only when N < 50 OR when you specifically need WebFetch's robots.txt / allowlist behavior.

#### Fast path (recommended, N ≥ 50)

```bash
while IFS= read -r url; do
  status=$(curl -sS -o /dev/null -w "%{http_code}" -L --max-time 8 \
                -A "Mozilla/5.0" "$url" 2>/dev/null || echo "000")
  echo "$status $url"
done < .url_check_tmp/urls.txt > .url_check_tmp/results.txt
```

`-L` follows redirects (200/301/302 all map to "ok"); `--max-time 8` keeps any single hung URL from blocking the run. ~80–100 ms per URL on typical residential bandwidth.

#### Parallel-chunk path (alternative, fine-grained control)

If you want per-chunk parallelism (helpful on multi-thousand-URL collections), split first:

```bash
split -l 50 .url_check_tmp/urls.txt .url_check_tmp/chunk_

for chunk in .url_check_tmp/chunk_*; do
  (
    while IFS= read -r url; do
      status=$(curl -s -o /dev/null -w "%{http_code}" -L -m 15 \
                    -A "Mozilla/5.0 research_toolkit/2.0" \
                    -I "$url" 2>/dev/null || echo "000")
      echo "$status $url"
    done < "$chunk" > "$chunk.results"
  ) &
done
wait
cat .url_check_tmp/chunk_*.results | sort -u > .url_check_tmp/results.txt
```

### Phase 4: GET retry on 4xx

Some sites reject HEAD but accept GET (OpenAI, Microsoft Learn, etc.). Retry every 4xx with GET (Range header to avoid full body):

```bash
while IFS= read -r line; do
  status="${line%% *}"
  url="${line#* }"
  if [[ "$status" =~ ^4 ]]; then
    retry=$(curl -s -o /dev/null -w "%{http_code}" -L -m 15 \
                 -A "Mozilla/5.0 research_toolkit/2.0" \
                 -H "Range: bytes=0-1024" \
                 "$url" 2>/dev/null || echo "000")
    echo "$retry $url"
  else
    echo "$status $url"
  fi
done < .url_check_tmp/results.txt > .url_check_tmp/results_retry.txt
```

### Phase 5: apply bot-blocked allowlist

Categorize URLs whose domain matches the allowlist as "bot-blocked, not broken":

```
openai.com/*
learn.microsoft.com/*
azure.microsoft.com/*
app.grayswan.ai/*
gandalf.lakera.ai/*
aivillage.org/*
simonwillison.net/*
*.gov.uk/*
```

(Maintained in this skill body; add new entries as discovered during real-world use.)

### Phase 6: categorize

Sort URLs into:
- **OK (2xx)**: working
- **Redirected (3xx)**: working but URL drift; record final URL
- **Broken (4xx after retry)**: hard 404 / 410 / 403 (excluding bot-blocked)
- **Server error (5xx)**: ambiguous; flag for manual recheck
- **Timeout (000)**: ambiguous; flag for manual recheck
- **Bot-blocked (4xx but on allowlist)**: not actually broken

### Phase 7: write report

Write to `<report_path>` (default `<target_folder>/../url_check_report.md`). Format per `references/url_check_protocol.md`:

```markdown
# URL Freshness Report

Generated: <YYYY-MM-DD>
Target: <target_folder>

## Summary

- total: <N>
- ok: <N>
- broken: <N>
- bot-blocked: <N>
- redirected: <N>

## Broken URLs (hard 404s)

### <file>
- <url>

## Bot-blocked URLs (flagged for manual review)

- <url> (allowlisted: <domain>)

## Redirected URLs

- <original> → <final>
```

### Phase 8 (optional): inline annotation

If `--inline` was passed:
- For each hard-404 URL, find the line(s) in the source markdown files where it appears
- Append `(broken-link as of YYYY-MM-DD)` annotation to those lines
- This modifies source files; only do it when the user explicitly requests `--inline`

### Phase 9: cleanup

Delete `.url_check_tmp/` before exit.

## Templates

(none — the report format is defined inline above and validated against the schema.)

## References

- `Read ~/Claude/research_toolkit/references/url_check_protocol.md` — bash chunking, retry semantics, allowlist rationale.

## Validation

```bash
python ~/Claude/research_toolkit/validators/url_check_report.py <report_path>
```

Validator checks: H1 is `# URL Freshness Report`; `## Summary` section present with `total`, `ok`, `broken` stats; `Generated: YYYY-MM-DD` line.

## Output / handoff

**Produces:**
- `<report_path>` (default `<target_folder>/../url_check_report.md`) — categorized URL report
- (with `--inline`) inline `(broken-link as of YYYY-MM-DD)` annotations on hard-404 URLs in source files

**Consumed by:**
- The user, who decides whether to fix each broken URL (rename, generalize, drop the entry)
- `/dossier-audit` (if invoked next) — reads the report to know which URLs need attention
