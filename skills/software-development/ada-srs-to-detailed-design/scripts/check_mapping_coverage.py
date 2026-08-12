#!/usr/bin/env python3
"""Check that a 需求→设计条目映射表 covers all 实现需求 in the SRS.

Usage: python check_mapping_coverage.py <srs.md> <mapping.md>

Classification rules:
- 实现需求: REQ-F blocks whose Source line starts with "REQ-F-" (parent-requirement
  reference). 用户/研发需求 Source = protocol section numbers (e.g. 5.1.2（1）2）).
- Mapping rows: table rows whose first cell matches (SD|P|T|C|I|F|S|PERF)[-\d]*\d+
  (accepts SD-1 and P1/T1-style planned codes); requirement IDs are collected from all
  non-first cells of the row (robust across 4-col and 7-col mapping tables).
- Extras are informational: expected to be empty, or exactly the 性能/容量 研发需求
  when the user decided to derive design entries directly from them (目标项目: F-119~123).

Exit code 0 = no missing 实现需求; 1 = missing; 2 = usage error.
"""
import re, sys


def parse_srs(path):
    text = open(path, encoding="utf-8").read()
    impl, other = set(), set()
    for m in re.finditer(
        r'REQ-F-(\d+)\n\nTitle\n.*?\n\nDescription\n.*?\n\nSource\n(.*?)\n```',
        text, re.S,
    ):
        n = int(m.group(1))
        src = m.group(2).strip().splitlines()[0].strip() if m.group(2).strip() else ""
        (impl if src.startswith("REQ-F-") else other).add(n)
    return impl, other


def parse_mapping(path):
    text = open(path, encoding="utf-8").read()
    sources, entries = set(), 0
    for line in text.splitlines():
        if re.match(r'^\| (SD|P|T|C|I|F|S|PERF)[-\d]*\d+ \|', line):
            entries += 1
            cells = [c.strip() for c in line.split("|")[1:-1]]
            for cell in cells[1:]:  # skip the 编号 cell
                for num in re.findall(r'F-(\d+)', cell):
                    sources.add(int(num))
    return sources, entries


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    impl, other = parse_srs(sys.argv[1])
    sources, entries = parse_mapping(sys.argv[2])
    missing = sorted(impl - sources)
    extra = sorted(sources - impl)
    print(f"SRS 实现需求: {len(impl)}; 映射条目: {entries}; 映射来源去重: {len(sources)}")
    print("未覆盖 (missing):", missing if missing else "无 ✅")
    print("额外来源 (extra):", extra if extra else "无 ✅")
    print("实现需求全覆盖:", impl <= sources)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
