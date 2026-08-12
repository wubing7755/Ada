#!/usr/bin/env python3
"""Verify structural parity between a source-document line range and its
translated output — the producer-side twin of the bilingual-pair audit.

Usage:
    python verify-translation-parity.py <source.md> <start_line> <end_line> <output.md>

start_line/end_line are 1-based inclusive (the same range handed to the
translator). Stdlib-only; prints one PASS/FAIL line per check; exit 0 iff
every check passes.

Checks
  1. Requirement-block headers (REQ-F-xxx / REQ-NF-xxx): identical set and
     order between the source range and the output.
  2. Per-block AC structure: AC label sequence (AC1..ACn) and
     Given/When/Then/And sequence, counted only inside each block's
     'Acceptance Criteria' section.
  3. Marker-bounded index tables: rows between
     <!-- 项目:requirements-index:start --> and <!-- 项目:requirements-index:end -->
     compared positionally on (ID, priority symbol, actor). The translated
     free-text column is NOT compared (it is a translation by design).
  4. Priority emoji distribution (red/yellow/green) inside the bounded region.
  5. No CJK residual in the output outside code fences (translations should
     not leak source-language text; the language-switch label is the only
     intended CJK in EN docs).

Known false-positive traps handled here (do not "fix" the script by
loosening them — these are real gotchas):
  - Source AC labels use full-width '：', output uses ASCII ':' — normalize
    with re.split(r'[：:]') before comparing labels, or every single AC will
    report a mismatch.
  - English descriptions may legitimately START with 'When'/'And' (e.g.
    "When a tab identifier conflict occurs...") — count GWTA lines only
    AFTER the 'Acceptance Criteria' marker, never across the whole block.
  - The block-header regex MUST be REQ-(F|NF)-\d+ — REQ-[FN] silently misses
    every REQ-NF-xxx id (counts came out 47 vs 47 while grep said 55).
  - Naive '| REQ-' row scans also sweep Appendix B/C rows into the count
    (185 != 150) — always bound table extraction by the start/end markers.
  - Contract translations preserve source-internal inconsistencies verbatim
    (typo ids like 'RE F-034', Actor mismatches between a requirement block
    and its index row, stats table P2=5 vs index 🟢 count=5-in-table-plus-
    appendix-rows). This script compares ID/priority/actor only; report
    preserved inconsistencies in the delivery summary instead.
"""

import io
import re
import sys

CJK = re.compile(r'[\u4e00-\u9fff]')
HEADER = re.compile(r'^(REQ-(?:F|NF)-\d+)')
AC_LABEL = re.compile(r'^AC\d+')
GWTA = {'Given', 'When', 'Then', 'And'}
START_MARKER = '<!-- 项目:requirements-index:start -->'
END_MARKER = '<!-- 项目:requirements-index:end -->'


def read_lines(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read().splitlines()


def fail(msg):
    print('FAIL ' + msg)
    return False


def check_headers(src, out):
    ids_s = [l.split()[0] for l in src if HEADER.match(l)]
    ids_o = [l.split()[0] for l in out if HEADER.match(l)]
    if ids_s == ids_o:
        print('PASS block headers: %d ids, identical set and order' % len(ids_s))
        return True
    return fail('block headers: src=%d out=%d, sets differ (missing=%s extra=%s)'
                % (len(ids_s), len(ids_o),
                   sorted(set(ids_s) - set(ids_o)), sorted(set(ids_o) - set(ids_s))))


def block_map(lines):
    blocks, cur = {}, None
    for l in lines:
        m = HEADER.match(l)
        if m:
            cur = m.group(1)
            blocks[cur] = []
        elif cur is not None:
            blocks[cur].append(l)
    return blocks


def ac_section(lines):
    try:
        i = lines.index('Acceptance Criteria')
    except ValueError:
        return []
    return lines[i + 1:]


def check_ac_structure(src, out):
    bs, bo = block_map(src), block_map(out)
    bad = 0
    for k in bs:
        s, o = ac_section(bs[k]), ac_section(bo[k])
        acs_s = [re.split(r'[：:]', l)[0] for l in s if AC_LABEL.match(l)]
        acs_o = [re.split(r'[：:]', l)[0] for l in o if AC_LABEL.match(l)]
        gwta_s = [l.split()[0] for l in s if l.split() and l.split()[0] in GWTA]
        gwta_o = [l.split()[0] for l in o if l.split() and l.split()[0] in GWTA]
        if acs_s != acs_o or gwta_s != gwta_o:
            bad += 1
            print('  diff in %s: AC src=%s out=%s | GWTA src=%s out=%s'
                  % (k, acs_s, acs_o, gwta_s, gwta_o))
    if bad == 0:
        print('PASS AC structure: %d blocks, AC labels + Given/When/Then/And sequences identical' % len(bs))
        return True
    return fail('AC structure: %d/%d blocks differ (see lines above)' % (bad, len(bs)))


def bounded_rows(lines):
    try:
        i1 = next(i for i, l in enumerate(lines) if START_MARKER in l)
        i2 = next(i for i, l in enumerate(lines) if END_MARKER in l)
    except StopIteration:
        return None
    return [l for l in lines[i1 + 1:i2] if l.startswith('| REQ-')]


def norm_row(r):
    parts = [p.strip() for p in r.strip('|').split('|')]
    return (parts[0], parts[1], parts[2])  # ID, priority, actor


def check_index_tables(src, out):
    s, o = bounded_rows(src), bounded_rows(out)
    if s is None or o is None:
        print('SKIP index tables: markers %s / %s not found in one of the files'
              % (START_MARKER, END_MARKER))
        return True
    if len(s) != len(o):
        return fail('index table: src=%d rows, out=%d rows' % (len(s), len(o)))
    mism = [(a, b) for a, b in zip(s, o) if norm_row(a) != norm_row(b)]
    if mism:
        for a, b in mism[:5]:
            print('  row diff:\n    src: %s\n    out: %s' % (a, b))
        return fail('index table: %d/%d rows differ on (ID, priority, actor)' % (len(mism), len(s)))
    print('PASS index table: %d rows, (ID, priority, actor) identical in order' % len(s))
    return True


def check_emoji(src, out):
    s, o = bounded_rows(src), bounded_rows(out)
    if s is None or o is None:
        return True
    from collections import Counter
    cs = Counter(re.findall(r'[🔴🟡🟢]', ' '.join(s)))
    co = Counter(re.findall(r'[🔴🟡🟢]', ' '.join(o)))
    if cs == co:
        print('PASS priority emoji distribution in index table: %s' % dict(cs))
        return True
    return fail('emoji distribution: src=%s out=%s' % (dict(cs), dict(co)))


def check_no_cjk(out):
    in_fence = False
    hits = []
    for i, l in enumerate(out, 1):
        if l.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence and CJK.search(l):
            hits.append((i, l[:80]))
    if not hits:
        print('PASS no CJK residual outside code fences')
        return True
    for i, l in hits[:10]:
        print('  line %d: %s' % (i, l))
    return fail('CJK residual outside code fences: %d lines' % len(hits))


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    src_path, start, end, out_path = sys.argv[1:]
    src = read_lines(src_path)[int(start) - 1:int(end)]
    out = read_lines(out_path)
    print('source range %s:%s-%s (%d lines) -> %s (%d lines)'
          % (src_path, start, end, len(src), out_path, len(out)))
    results = [
        check_headers(src, out),
        check_ac_structure(src, out),
        check_index_tables(src, out),
        check_emoji(src, out),
        check_no_cjk(out),
    ]
    if all(results):
        print('ALL CHECKS PASSED')
        return 0
    print('CHECKS FAILED — see FAIL lines above')
    return 1


if __name__ == '__main__':
    sys.exit(main())
