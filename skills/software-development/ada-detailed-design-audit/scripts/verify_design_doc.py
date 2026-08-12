#!/usr/bin/env python3
"""Verify SRS(实现需求) <-> 详细设计(设计条目) traceability & structure.

Usage:
    python verify_design_doc.py <design.md> <srs.md> [old_term ...]

Checks:
  1. Design entry numbering (SD-N) continuous from 1, no missing/dup.
  2. Every REQ-F referenced by design entries is an SRS implementation
     requirement (block containing 'Derivation'); zero missing / zero extra
     (design must NOT reference 研发/用户层 requirements).
  3. Every SD block has the four fixed fields 【设计编号】【设计名称】【设计描述】【需求来源】.
  4. Cross-references (SD-N inside text) resolve to existing entries.
  5. (optional) old_term ... residue counts — expect 0 for each.

Why a script instead of search_files: on Windows/MSYS, rg fails on absolute
paths containing CJK characters (IO error 系统找不到指定的路径). Python's
open(path, encoding='utf-8') reads them fine.

Note: a 【需求来源】 mention in the chapter intro / component tables is a
field-name reference, not a 69th entry — check line numbers before flagging.
"""
import re
import sys


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def main():
    design_path, srs_path = sys.argv[1], sys.argv[2]
    old_terms = sys.argv[3:]
    design = read(design_path)
    srs = read(srs_path)

    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), msg)
        if not cond:
            ok = False

    # 1. numbering
    nums = [int(x) for x in re.findall(r"^SD-(\d+)$", design, re.M)]
    check(nums == list(range(1, len(nums) + 1)),
          f"SD 编号连续 1..{len(nums)} (共 {len(nums)} 条)")
    dups = sorted({x for x in set(nums) if nums.count(x) > 1})
    check(not dups, f"SD 编号无重复 (重复: {dups})")

    # 2. REQ coverage vs SRS implementation requirements (blocks with Derivation)
    impl = set()
    for blk in re.split(r"```", srs):
        if "Derivation" in blk:
            m = re.search(r"REQ-F-(\d+)", blk)
            if m:
                impl.add(int(m.group(1)))
    doc = set(int(x) for x in re.findall(r"REQ-F-(\d+)", design))
    check(doc == impl,
          f"REQ 引用 {len(doc)} 个 == SRS 实现需求 {len(impl)} 个; "
          f"缺: {sorted(impl - doc)} 多(混入上层): {sorted(doc - impl)}")

    # 3. four-field structure per entry
    blocks = re.split(r"【设计编号】", design)[1:]
    missing = [(i + 1, f) for i, b in enumerate(blocks)
               for f in ("设计名称", "设计描述", "需求来源")
               if f"【{f}】" not in b]
    check(not missing, f"四字段完整 ({len(blocks)} 个条目; 缺字段: {missing})")

    # 4. cross refs resolve
    refs = set(int(x) for x in re.findall(r"SD-(\d+)", design))
    oob = sorted(x for x in refs if not (1 <= x <= len(nums)))
    check(not oob, f"交叉引用均在范围内 (越界: {oob})")

    # 5. old terms residue
    for t in old_terms:
        n = design.count(t)
        check(n == 0, f"旧表述残留 [{t}] 应为 0 (实际 {n})")

    print("\n总判定:", "通过" if ok else "存在失败项")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
