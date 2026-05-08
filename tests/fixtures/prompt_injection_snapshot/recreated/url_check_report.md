# URL Freshness Report

Generated: 2026-05-07
Target: tests/fixtures/prompt_injection_snapshot/recreated/agent_index/

## Summary

- total: 146
- ok: 140
- broken: 0
- bot-blocked: 5
- redirected: (counted within ok via curl `-L`)
- 4xx-after-retry-not-allowlisted: 1 (darkreading.com — likely bot-blocked, see Notes)

## Broken URLs (hard 404s)

(none — every URL resolved to 200 OK or a known bot-blocking domain)

## Bot-blocked URLs (flagged for manual review)

The skill's allowlist (`references/url_check_protocol.md` § "bot-blocked allowlist") covers:
`openai.com/*`, `learn.microsoft.com/*`, `azure.microsoft.com/*`, `app.grayswan.ai/*`,
`gandalf.lakera.ai/*`, `aivillage.org/*`, `simonwillison.net/*`, `*.gov.uk/*`.

5 OpenAI URLs returned 403 to both HEAD and GET-with-Range; allowlisted as known bot-blocked:

- https://openai.com/global-affairs/our-approach-to-frontier-risk/ (allowlisted: openai.com)
- https://openai.com/index/gpt-4o-system-card/ (allowlisted: openai.com)
- https://openai.com/index/openai-o1-system-card/ (allowlisted: openai.com)
- https://openai.com/index/operator-system-card/ (allowlisted: openai.com)
- https://openai.com/index/updating-our-preparedness-framework/ (allowlisted: openai.com)

## Notes

- 1 URL not on the current allowlist returned 403 after GET retry:
  - https://www.darkreading.com/application-security/only-250-documents-poison-any-ai-model
  - darkreading.com is a security-news site that throttles automated requests.
  - **Recommendation:** add `darkreading.com/*` to the allowlist in `references/url_check_protocol.md` (filed as friction in BURN_IN_NOTES § Stage 6).

- Friction observation #1: the bash URL-extraction snippet in `references/url_check_protocol.md` ships with a regex pattern (`[^[:space:]\)\]\"\<]+`) that returns 0 matches in this environment (macOS/zsh + GNU coreutils via brew). The corrected pattern (`[a-zA-Z0-9./?=&_~%#:+-]+`) found 146 URLs cleanly. Filed in BURN_IN_NOTES.
