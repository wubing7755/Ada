# -*- coding: utf-8 -*-
"""SRS consistency verifier for the user's SRS convention
(REQ-(F|NF)-XXX 🔴/🟡/🟢 [Actor: ...] headers inside bare ``` fences).

Usage: python verify_srs_consistency.py <path/to/SRS.md>

Checks:
  - F/NF header counts, uniqueness, ID gaps (deleted requirements)
  - per-section requirement count + P0/P1/P2 distribution (compare vs §5 table manually)
  - same-segment duplicate bilingual annotations (Title/Description/AC rule:
    annotate a term once per segment) — requirement blocks only, mermaid excluded
  - '本节需求索引 (N 条)' headers vs actual per-section counts

Pitfalls encoded (do not simplify these away):
  - Header regex MUST include emoji + [Actor: — loose ^REQ-F-\\d{3} also matches
    line-initial cross-references ("REQ-F-017 所述的...") and corrupts state.
  - Opening fences may carry a language tag (```mermaid); closing fences are
    always bare. A requirement block = bare fence + genuine header on next line.
"""
import re, io, sys, collections

HDR_RE = re.compile(r"^REQ-(F|NF)-(\d{3})\s+(🔴|🟡|🟢)\s+\[Actor:")
SEC_RE = re.compile(r"^(##+ \d[\d.]*|# \d)\s")
SEG_RE = re.compile(r"^(Title|Description|Acceptance Criteria|AC\d+[：:])")
IDX_RE = re.compile(r"本节需求索引\s*\((\d+)\s*条\)")

# Bilingual annotation whitelist: extend per project glossary (§1.5).
TERMS = ["Editor Tab（编辑器标签页）","Editor View（编辑器视图）","Dock Panel（Dock 面板）",
"Dock Region（Dock 区域）","Splitter（分割条）","Empty State（空状态）","Collapsed State（折叠状态）",
"Collapsed Size（折叠尺寸）","Auto-hide（自动隐藏）","Flyout（浮层）","ToolBar Entry（ToolBar 条目）",
"Active Panel（活跃面板）","Active State（激活状态）","Content Identifier（内容标识）",
"Content Registry（内容注册表）","Dedup Key（去重键）","Dedup Parameter（去重参数）",
"Layout Preset（布局预设）","Layout Instance（布局实例）","Docking（停靠）","Focus（焦点）",
"Pinned（固定标记）","Panel Header（面板标题栏）","Error Boundary（错误边界）","Fixed Region（固定区域）"]


def main(path):
    lines = io.open(path, encoding="utf-8").read().split("\n")
    sec, in_fence, req_fence = "?", False, False
    stats = collections.OrderedDict()
    idx_claims = {}
    ids = {"F": [], "NF": []}
    dups = []
    seg = collections.Counter()

    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not in_fence and SEC_RE.match(raw):
            sec = raw.lstrip("#").strip().split()[0]
        if not in_fence:
            m = IDX_RE.search(raw)
            if m:
                idx_claims[sec] = int(m.group(1))
        if s.startswith("```"):
            was = in_fence
            in_fence = not in_fence if s == "```" or not in_fence else in_fence
            req_fence = (not was and in_fence and s == "```"
                         and i < len(lines) and bool(HDR_RE.match(lines[i].strip())))
            seg.clear()
            continue
        if not in_fence or not req_fence:
            continue
        h = HDR_RE.match(s)
        if h:
            ids[h.group(1)].append(int(h.group(2)))
            stats.setdefault(sec, collections.Counter())[h.group(3)] += 1
        if SEG_RE.match(s) or h:
            seg.clear()
        for t in TERMS:
            c = raw.count(t)
            if c:
                seg[t] += c
                if seg[t] > 1:
                    dups.append(f"L{i}: {t} x{seg[t]}")

    for k in ("F", "NF"):
        v = ids[k]
        gaps = sorted(set(range(1, max(v) + 1)) - set(v)) if v else []
        print(f"{k}: count={len(v)} unique={len(set(v))} max={max(v) if v else 0} gaps={gaps}")
    print("\nper-section (compare against §5 statistics table AND 本节需求索引):")
    total = collections.Counter()
    for scn, c in stats.items():
        claim = idx_claims.get(scn)
        flag = "" if claim in (None, sum(c.values())) else f"  <-- index claims {claim}!"
        print(f"  §{scn}: total={sum(c.values())} P0={c['🔴']} P1={c['🟡']} P2={c['🟢']}{flag}")
        total.update(c)
    print(f"TOTAL: {sum(total.values())}  P0={total['🔴']} P1={total['🟡']} P2={total['🟢']}")
    print(f"\nsame-segment duplicate annotations: {len(dups)}")
    for d in dups[:20]:
        print("  ", d)
    return 1 if dups else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/SRS.md"))
