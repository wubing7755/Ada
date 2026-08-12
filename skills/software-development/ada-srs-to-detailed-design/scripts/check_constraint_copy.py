#!/usr/bin/env python3
"""检测详细设计中「设计要求及约束」章节对 SRS 需求 Description 的照搬程度。

用法:
    python check_constraint_copy.py <srs.md> <design.md> [阈值=0.8]

输出: 每处约束的相似度（去空白 difflib 比）、命中阈值标记、统计汇总。
退出码: 1 = 存在疑似照搬；0 = 全部低于阈值。

说明:
- 同时匹配 4 级（#### 5.1.1.1）与 5 级（##### 5.1.2.1.1）约束标题，否则漏 SD-1 类条目
- SD-2/SD-3 共用一个约束小节时按小节计（68 条目 ≠ 67 小节是正常的）
- >0.8 = 基本照搬需重写；1.00 = 一字不差（重灾区，需逐条人工改写）
"""
import re
import sys
from difflib import SequenceMatcher


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    srs_path, design_path = sys.argv[1], sys.argv[2]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    with open(srs_path, encoding="utf-8") as f:
        srs = f.read()
    with open(design_path, encoding="utf-8") as f:
        text = f.read()

    # SRS: REQ-F 编号 -> Description 文本（代码块内 Description 字段）
    req_desc: dict[int, str] = {}
    for blk in re.split(r"```", srs):
        m = re.search(r"REQ-F-(\d+)", blk)
        if m:
            dm = re.search(r"Description\n(.*?)(?:\nSource|\nDerivation|$)", blk, re.S)
            if dm:
                req_desc[int(m.group(1))] = dm.group(1).strip()

    # 设计文档：约束正文 -> 对应 SD 的需求来源
    pattern = re.compile(
        r"^(#{4,5}) (\d+\.\d+\.\d+(?:\.\d+)?)\.1 设计要求及约束\n\n"
        r"(.*?)\n\n\1 \2\.2 设计\n\n【设计编号】\nSD-(\d+).*?【需求来源】\n"
        r"(.*?)(?=\n### |\n#### |\Z)",
        re.M | re.S,
    )

    rows = []
    for m in pattern.finditer(text):
        constraint = norm(m.group(3))
        reqs = [int(x) for x in re.findall(r"REQ-F-(\d+)", m.group(5))]
        best = 0.0
        for r in reqs:
            desc = norm(req_desc.get(r, ""))
            if desc:
                best = max(best, SequenceMatcher(None, constraint, desc).ratio())
        rows.append((int(m.group(4)), best, reqs))

    hits = [r for r in rows if r[1] > threshold]
    for sd, sim, reqs in rows:
        flag = "  <-- 照搬" if sim > threshold else ""
        print(f"SD-{sd:<3} {sim:>6.2f}  {','.join('REQ-F-%d' % r for r in reqs)}{flag}")
    print(
        f"\n共 {len(rows)} 处约束小节；>阈值({threshold}) 疑似照搬 {len(hits)} 处: "
        f"{[r[0] for r in hits]}"
    )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
