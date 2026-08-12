#!/usr/bin/env python3
"""Validate a generated 详细设计 (SDD) chapter against its layered SRS.

Checks:
1. Design entry IDs are sequential and unique (auto-detects pattern SD-1 or DES-XXX-001)
2. Every entry has exactly the 4 fields: 设计编号 / 设计名称 / 设计描述 / 需求来源
3. Every 【需求来源】 ID belongs to an 实现需求 parsed from the SRS (H3 section "### 实现需求",
   also accepts legacy name "### 具体实现子需求")
4. Every implementation requirement in the SRS is covered by >= 1 design entry

Usage:
    python validate_sdd.py <srs.md> <design.md>

Exit code 0 = all checks pass; 1 = failures; 2 = usage error.
"""
import re
import sys


def parse_srs(path):
    """Return (impl_ids, all_ids) from a layered SRS."""
    lines = open(path, encoding="utf-8").read().splitlines()
    impl_ids, all_ids = set(), set()
    current_heading = ""
    in_block = False
    heading_re = re.compile(r"^(#{2,4})\s+(.+)$")
    for line in lines:
        m = heading_re.match(line)
        if m:
            current_heading = m.group(2).strip()
            continue
        if line.strip().startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            # Anchor to whole line: requirement ID lines are bare "REQ-F-268";
            # Source lines like "REQ-F-062（可编辑文件管理）" are PARENT refs and
            # must NOT be counted as implementation requirements.
            for rid in re.findall(r"^REQ-[A-Z]+-\d+$", line.strip()):
                all_ids.add(rid)
                if "实现需求" in current_heading or "实现子需求" in current_heading:
                    impl_ids.add(rid)
    return impl_ids, all_ids


def parse_design(path):
    """Return entries: [{id, idnum, fields, sources}]."""
    text = open(path, encoding="utf-8").read()
    entries = []
    for b in re.split(r"(?=【设计编号】)", text):
        if not b.strip().startswith("【设计编号】"):
            continue
        fields = {}
        for fname in ["【设计编号】", "【设计名称】", "【设计描述】", "【需求来源】"]:
            m = re.search(re.escape(fname) + r"\s*\n([\s\S]*?)(?=\n【|\Z)", b)
            fields[fname] = m.group(1).strip() if m else ""
        did = fields["【设计编号】"].splitlines()[0] if fields["【设计编号】"] else "?"
        mnum = re.search(r"(\d+)\s*$", did)
        entries.append({
            "id": did,
            "idnum": int(mnum.group(1)) if mnum else None,
            "fields": fields,
            "sources": re.findall(r"(REQ-[A-Z]+-\d+)", fields["【需求来源】"]),
        })
    return entries


def main():
    if len(sys.argv) != 3:
        print("usage: python validate_sdd.py <srs.md> <design.md>")
        return 2
    impl, all_ids = parse_srs(sys.argv[1])
    entries = parse_design(sys.argv[2])
    errors = []

    nums = [e["idnum"] for e in entries]
    if any(n is None for n in nums):
        errors.append("无法解析的设计编号: " + ", ".join(e["id"] for e in entries if e["idnum"] is None))
    elif nums != list(range(1, len(nums) + 1)):
        dup = sorted({n for n in nums if nums.count(n) > 1})
        miss = sorted(set(range(1, max(nums) + 1)) - set(nums))
        errors.append(f"设计编号不连续: 总数={len(nums)} 重复={dup} 缺失={miss}")

    for e in entries:
        missing = [f for f in ["【设计编号】", "【设计名称】", "【设计描述】", "【需求来源】"] if not e["fields"][f]]
        if missing:
            errors.append(f"{e['id']} 缺少字段: {missing}")

    used = {s for e in entries for s in e["sources"]}
    bad = sorted(used - impl)
    if bad:
        errors.append("需求来源含非实现需求编号(应从SRS'实现需求'小节提取): " + ", ".join(bad))

    uncovered = sorted(impl - used)
    if uncovered:
        errors.append("实现需求未被任何设计条目覆盖: " + ", ".join(uncovered))

    if errors:
        print("FAIL:")
        for err in errors:
            print(" -", err)
        return 1
    print(f"OK: {len(entries)} entries, 编号连续, 四字段齐全, "
          f"{len(used)}/{len(impl)} 实现需求全覆盖")
    return 0


if __name__ == "__main__":
    sys.exit(main())
