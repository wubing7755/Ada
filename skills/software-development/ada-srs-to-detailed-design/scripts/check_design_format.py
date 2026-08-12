#!/usr/bin/env python3
"""设计条目格式检查（四字段口径）：字段序列 / 单一自然段 / 无列表标题 / 来源格式 / 编号连续 / 描述长度。

用法: python check_design_format.py <design.md> [--terms "A|B|C"]

--terms: 术语一致性扫描，给定同一概念的备选写法（用 | 分隔），若文档同时出现多个则告警
         （实例：'集成格式规格|目标项目 标准格式规格|外部规格' 三种并存即不合格）。

解析要点（实测坑，勿改）：
- 按 【设计编号】 的位置切片（starts），不要 re.split 吞掉标签；
- 标签提取用 【([^】]+)】 无括号，比较基准同步去括号；
- 需求来源区只取 ^F-\\d+$ 行，跳过模块标题（^#）行。
"""
import re
import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    terms_arg = None
    if "--terms" in sys.argv:
        terms_arg = sys.argv[sys.argv.index("--terms") + 1]

    text = open(path, encoding="utf-8").read()
    starts = [m.start() for m in re.finditer(r"(?m)^【设计编号】\n", text)]
    issues = []
    nums = []

    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        blk = text[s:e]
        m = re.search(r"【设计编号】\n(SD-\d+)", blk)
        sd = m.group(1) if m else f"#{i + 1}"
        nums.append(int(sd[3:]) if m else 0)

        labels = re.findall(r"【([^】]+)】", blk)
        if labels != ["设计编号", "设计名称", "设计描述", "需求来源"]:
            issues.append((sd, f"字段序列异常: {labels}"))

        dm = re.search(r"【设计描述】\n(.*?)\n【需求来源】", blk, re.S)
        desc = dm.group(1).strip() if dm else ""
        if not desc:
            issues.append((sd, "设计描述为空"))
        else:
            if "\n\n" in desc:
                issues.append((sd, "描述非单一自然段（含空行分段）"))
            for ln in desc.splitlines():
                s2 = ln.strip()
                if re.match(r"^[-*•]\s", s2) or re.match(r"^\d+[\.、)]\s", s2) or re.match(r"^[①-⑩]", s2):
                    issues.append((sd, f"描述含列表/编号标记: {s2[:24]}"))
                    break
            if re.match(r"^#{1,6}\s", desc):
                issues.append((sd, "描述含标题"))
            if len(desc) > 300:
                issues.append((sd, f"描述过长 {len(desc)} 字（建议精简至 ≤300）"))

        if "【需求来源】" in blk:
            tail = blk.split("【需求来源】", 1)[1]
            src_lines = [ln.strip() for ln in tail.splitlines()
                         if ln.strip() and not ln.strip().startswith("#")]
            bad = [ln for ln in src_lines if not re.match(r"^F-\d+$", ln)]
            if not src_lines:
                issues.append((sd, "需求来源为空"))
            elif bad:
                issues.append((sd, f"需求来源格式异常: {bad}"))

    if nums:
        if len(set(nums)) != len(nums):
            issues.append(("编号", "有重复编号"))
        if nums != list(range(min(nums), max(nums) + 1)):
            issues.append(("编号", f"编号不连续: {nums}"))

    if terms_arg:
        alts = terms_arg.split("|")
        found = [t for t in alts if t in text]
        if len(found) > 1:
            issues.append(("术语", f"同概念多种叫法并存，需统一主术语: {found}"))

    print(f"条目数: {len(starts)}")
    if issues:
        for sd, msg in issues:
            print(f"{sd}: {msg}")
        sys.exit(1)
    print("格式检查通过 ✅")


if __name__ == "__main__":
    main()
