#!/usr/bin/env python3
"""Verify structural parity for an SRS/HLD line-range translation where the
REQ blocks live in plain ``` fences WITHOUT marker-bounded index tables —
the producer-side twin of scripts/verify-translation-parity.py for that
document shape. Session-proven on a 1760-line Chinese SRS -> English part
(SRS.part1.md, 35 REQ blocks, all checks green).

Usage:
    python verify-srs-block-translation.py <source.md> <start_line> <end_line> <output.md> \
        [--tokens t1,t2,...] [--cjk-allow "sub1|sub2|..."]

    start/end are 1-based inclusive (the range handed to the translator).
    --tokens      comma-separated identifiers that must appear byte-identical
                  in the output (REQ/DES ids, paths, "300ms", "F-135", ...).
    --cjk-allow   pipe-separated substrings of INTENTIONAL CJK (glossary
                  table Chinese column, parenthetical annotations like
                  "Dock Panel (Dock 面板)") so they are not flagged.
    Stdlib-only; prints one PASS/FAIL line per check; exit 0 iff all pass.

Checks
  1. REQ-block tuple parity: (ID, priority marker, Actor) parsed from each
     `REQ-F-xxx [🔴🟡🟢] [Actor: ...]` header line — compared positionally
     against the source range (the header line IS the contract tuple when
     no index table exists).
  2. AC label sequences per block (AC1..ACn in order). Sequence comparison
     naturally PRESERVES source quirks (e.g. a duplicated `AC2` label in
     REQ-F-017) — a mismatch means the translator renumbered, not that the
     source was odd.
  3. Fenced code blocks balanced; file ends outside a fence.
  4. Mermaid/SVG block counts identical to the source range.
  5. Anchor-slug resolvability: every `](#slug)` in the output resolves to a
     heading slug derived from the output's own headings via the
     github-slugger rule (lowercase, spaces->hyphens, strip punctuation);
     anchor count equals the source range's anchor count.
  6. Token preservation (--tokens).
  7. CJK residual outside code fences, minus the --cjk-allow allowlist.
  8. Priority emoji distribution (🔴🟡🟢) identical between range and output.

Known false-positive traps (do not loosen the script to dodge them):
  - Source AC labels use full-width '：', output uses ASCII ':' — normalize
    with re.split(r'[：:]') before comparing.
  - "Token preserved" lists must be sourced from the SOURCE text, not from
    memory: a check token absent from the source (e.g. 'REQ-F-135' when the
    source writes 'F-135' as a historical number) is a test bug, not a
    translation bug. grep the source for every token first.
  - git-bash `grep -c '🔴'` can silently return 0 on multibyte patterns —
    count emoji with Python regex + Counter, never grep.
  - A bilingual-annotation translation intentionally keeps CJK (glossary
    Chinese column, parenthetical annotations); a bare zero-CJK rule would
    flag legitimate content — use --cjk-allow.
"""

import io
import re
import sys
from collections import Counter

CJK = re.compile(r'[\u4e00-\u9fff]')
HEADER = re.compile(
    r'^(REQ-(?:F|NF)-\d+)(?:\s+([\U0001F534\U0001F7E1\U0001F7E2]))?'
    r'(?:\s*\[Actor:\s*([^\]]+)\])?')
AC_LABEL = re.compile(r'^AC\d+')
EMOJI = re.compile(r'[\U0001F534\U0001F7E1\U0001F7E2]')
ANCHOR = re.compile(r'\]\(#([^)]+)\)')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')


def read_lines(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read().splitlines()


def fail(msg):
    print('FAIL ' + msg)
    return False


def parse_header(line):
    m = HEADER.match(line)
    if not m:
        return None
    tup = (m.group(1),)
    if m.group(2):
        tup += (m.group(2),)
    if m.group(3):
        tup += (m.group(3).strip(),)
    return tup


def check_block_tuples(src, out):
    ts = [t for l in src if (t := parse_header(l))]
    to = [t for l in out if (t := parse_header(l))]
    if ts == to:
        print('PASS block tuples: %d blocks, (ID%s) identical in order'
              % (len(ts), ', marker, Actor' if ts and len(ts[0]) > 1 else ''))
        return True
    return fail('block tuples: src=%d out=%d; missing=%s extra=%s'
                % (len(ts), len(to),
                   sorted(set(ts) - set(to)), sorted(set(to) - set(ts))))


def block_map(lines):
    blocks, cur = {}, None
    for l in lines:
        m = re.match(r'^(REQ-(?:F|NF)-\d+)', l)
        if m:
            cur = m.group(1)
            blocks[cur] = []
        elif cur is not None:
            blocks[cur].append(l)
    return blocks


def ac_labels(block_lines):
    return [re.split(r'[：:]', l)[0] for l in block_lines if AC_LABEL.match(l)]


def check_ac_sequences(src, out):
    bs, bo = block_map(src), block_map(out)
    bad = [(k, ac_labels(bs[k]), ac_labels(bo.get(k, [])))
           for k in bs if ac_labels(bs[k]) != ac_labels(bo.get(k, []))]
    if not bad:
        print('PASS AC sequences: %d blocks, labels identical incl. quirks' % len(bs))
        return True
    for k, s, o in bad[:5]:
        print('  diff in %s: src=%s out=%s' % (k, s, o))
    return fail('AC sequences: %d/%d blocks differ' % (len(bad), len(bs)))


def check_fences(out):
    fences = [i for i, l in enumerate(out) if l.startswith('```')]
    if len(fences) % 2 == 0:
        print('PASS fences: %d fence lines, balanced' % len(fences))
        return True
    return fail('fences: %d lines (unbalanced)' % len(fences))


def check_diagram_counts(src, out):
    ok = True
    for kind in ('mermaid', 'svg'):
        s = sum(1 for l in src if kind in l)
        o = sum(1 for l in out if kind in l)
        if s == o:
            print('PASS %s blocks: %d == %d' % (kind, s, o))
        else:
            ok = False
            print('FAIL %s blocks: src=%d out=%d' % (kind, s, o))
    return ok


def slugify(heading_text):
    s = heading_text.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s, flags=re.UNICODE)  # strip punctuation
    s = re.sub(r'\s+', '-', s)
    return s


def check_anchors(src, out):
    s_anchors = [a for _, a in ANCHOR.findall('\n'.join(src))]
    o_anchors = [a for _, a in ANCHOR.findall('\n'.join(out))]
    if len(s_anchors) != len(o_anchors):
        return fail('anchor count: src=%d out=%d' % (len(s_anchors), len(o_anchors)))
    slugs = set()
    for l in out:
        m = HEADING.match(l)
        if m:
            slugs.add(slugify(m.group(2)))
    missing = sorted(set(o_anchors) - slugs)
    if not missing:
        print('PASS anchors: %d links, all resolve to output heading slugs' % len(o_anchors))
        return True
    return fail('anchors unresolved: %s' % missing)


def check_tokens(out, tokens):
    if not tokens:
        print('SKIP tokens: none provided (--tokens)')
        return True
    missing = [t for t in tokens if t not in '\n'.join(out)]
    if not missing:
        print('PASS tokens: %d/%d present' % (len(tokens), len(tokens)))
        return True
    return fail('tokens missing: %s' % missing)


def check_cjk(out, allow):
    in_fence = False
    hits = []
    for i, l in enumerate(out, 1):
        if l.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence and CJK.search(l):
            if not any(sub in l for sub in allow):
                hits.append((i, l[:90]))
    if not hits:
        print('PASS CJK residual: none outside fences/allowlist (%d allowed substrings)'
              % len(allow))
        return True
    for i, l in hits[:10]:
        print('  line %d: %s' % (i, l))
    return fail('CJK residual: %d lines outside fences and allowlist' % len(hits))


def check_emoji_dist(src, out):
    cs = Counter(EMOJI.findall('\n'.join(src)))
    co = Counter(EMOJI.findall('\n'.join(out)))
    if cs == co:
        print('PASS emoji distribution: %s' % dict(cs))
        return True
    return fail('emoji distribution: src=%s out=%s' % (dict(cs), dict(co)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 4:
        print(__doc__)
        return 2
    src_path, start, end, out_path = args
    tokens = []
    allow = []
    for a in sys.argv[1:]:
        if a.startswith('--tokens='):
            tokens = [t.strip() for t in a.split('=', 1)[1].split(',') if t.strip()]
        elif a.startswith('--cjk-allow='):
            allow = [t.strip() for t in a.split('=', 1)[1].split('|') if t.strip()]
    src = read_lines(src_path)[int(start) - 1:int(end)]
    out = read_lines(out_path)
    print('source range %s:%s-%s (%d lines) -> %s (%d lines)'
          % (src_path, start, end, len(src), out_path, len(out)))
    results = [
        check_block_tuples(src, out),
        check_ac_sequences(src, out),
        check_fences(out),
        check_diagram_counts(src, out),
        check_anchors(src, out),
        check_tokens(out, tokens),
        check_cjk(out, allow),
        check_emoji_dist(src, out),
    ]
    if all(results):
        print('ALL CHECKS PASSED')
        return 0
    print('CHECKS FAILED — see FAIL lines above')
    return 1


if __name__ == '__main__':
    sys.exit(main())
