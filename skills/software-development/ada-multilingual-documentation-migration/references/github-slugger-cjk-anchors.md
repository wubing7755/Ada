# GitHub Slugger and CJK Anchor Behavior

Verified 2026-08-02 against `github-slugger` v1/v2 (npm) and real GitHub
rendering on a public repo.

## The core rule

GitHub's anchor slugger removes full-width punctuation **without inserting a
separator**. Adjacent CJK/ASCII segments get glued together:

```
标题:  ## 附录 D：SRS—HLD 完整设计追溯矩阵
slug:  附录-dsrshld-完整设计追溯矩阵
        ^^^^^^ the ：(U+FF1A) and —(U+2014) vanish, gluing D+SRS+HLD
```

Both `github-slugger@1` and `@2` produce `附录-dsrshld-完整设计追溯矩阵`.
The natural-language separator rule ("punctuation becomes a hyphen") only
applies to ASCII punctuation like `:` / `-`; CJK full-width punctuation is
deleted.

## Practical consequences

- A hand-written link `#附录-dsrs-hld-完整设计追溯矩阵` (with a hyphen
  between SRS and HLD) is **broken** on GitHub even though it looks like the
  "right" anchor.
- When translating headings, the anchor in old links must be regenerated
  from the NEW English heading, not reused from the Chinese heading.

## Verifying against real GitHub rendering

GitHub does not expose heading `id` attributes in the rendered DOM, so you
cannot scrape them. Instead verify by navigation:

1. Navigate to `https://github.com/<owner>/<repo>/blob/<branch>/<file>#<candidate-anchor>`
2. Evaluate `window.scrollY`:
   - valid anchor → `scrollY > 0` (page scrolled to the heading)
   - invalid anchor → `scrollY === 0` (no jump)

This is how the pre-existing broken anchor in
`docs/requirements-traceability.md` (`#附录-dsrs-hld-...`) was confirmed
broken and the correct `#附录-dsrshld-...` confirmed working.

## Local approximation (Python)

Matches github-slugger for the cases seen in this repo:

```python
import re

def github_anchor(heading: str) -> str:
    slug = heading.strip().lower()
    # \w in Python is Unicode-aware; keep CJK, drop CJK punctuation
    slug = re.sub(r"[^\w\s\u4e00-\u9fff\-_]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
```

This produced byte-identical results to `github-slugger` for all headings
tested. When in doubt (mixed CJK/ASCII punctuation), install the real
package temporarily (`npm i github-slugger@2 --no-save`) and compare.
