# URL freshness check protocol

Detailed protocol for `/url-freshness-check`. Deterministic HEAD-checking with GET retry; bot-blocked allowlist; categorized output.

## Bash chunking pattern

The check should run in parallel chunks for efficiency. ~50 URLs per chunk, ~10 chunks in parallel:

```bash
#!/usr/bin/env bash
set -uo pipefail

mkdir -p .url_check_tmp
# Step 1: extract all unique URLs from the target folder.
grep -hroE 'https?://[^[:space:]\)\]"\<]+' "$TARGET_FOLDER" \
  | sort -u \
  | sed 's/[\.,:;]\+$//' \
  > .url_check_tmp/urls.txt

# Step 2: split into chunks.
split -l 50 .url_check_tmp/urls.txt .url_check_tmp/chunk_

# Step 3: HEAD-check each chunk in parallel.
for chunk in .url_check_tmp/chunk_*; do
  (
    while IFS= read -r url; do
      status=$(curl -s -o /dev/null -w "%{http_code}" -L -m 15 \
                    -A "Mozilla/5.0 research_toolkit/0.1" \
                    -I "$url" 2>/dev/null || echo "000")
      echo "$status $url"
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
  status="${line%% *}"
  url="${line#* }"
  if [[ "$status" =~ ^4 ]]; then
    retry=$(curl -s -o /dev/null -w "%{http_code}" -L -m 15 \
                 -A "Mozilla/5.0 research_toolkit/0.1" \
                 -H "Range: bytes=0-1024" \
                 "$url" 2>/dev/null || echo "000")
    echo "$retry $url"  # use retry status; if still 4xx → real broken
  else
    echo "$status $url"
  fi
done < .url_check_tmp/results.txt > .url_check_tmp/results_retry.txt
```

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

The skill writes a report to `<target>/url_check_report.md` (or a user-specified path):

```markdown
# URL Freshness Report

Generated: 2026-05-06
Target: docs/vol25_research/

## Summary

- total: 674
- ok: 595
- broken: 7
- bot-blocked: 32
- redirected: 40

## Broken URLs (hard 404s)

### docs/vol25_research/05_datasets_and_benchmarks.md
- https://example.com/blog/that-was-renamed-or-deleted

### docs/vol25_research/06_tools_and_vendors.md
- https://another-broken-link.example.com/

## Bot-blocked URLs (flagged for manual review)

- https://openai.com/blog/some-post (allowlisted: openai.com)
- ...

## Redirected URLs (final URL recorded)

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
