#!/usr/bin/env python3
"""Blazor i18n 资源键一致性检查。

扫描 razor 源码中的 Language.T("...") 使用键，与 Resources/ui-zh.json / ui-en.json
对比，报告：缺失键（used 但不在资源）、死键（在资源但无 razor 引用）。

用法：
    python3 resource-key-check.py [repo_root]

默认从当前目录开始；自动发现 `src/*/Resources` 下的 ui-zh.json / ui-en.json。
注意：
- 只匹配字面量 Language.T("key")；动态键（Language.T($"project.status.{...}")、
  三元表达式内键）不会匹配，会误报为"死键"——人工核对时以缺失键为准。
"""
import json
import re
import sys
from pathlib import Path


def find_app_dir(root: Path) -> Path | None:
    """定位含 Resources/ui-zh.json + ui-en.json 的 Blazor 应用目录。"""
    for res in (root / "src").glob("*/Resources"):
        if (res / "ui-zh.json").exists() and (res / "ui-en.json").exists():
            return res.parent
    return None


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    app_dir = find_app_dir(root)
    if app_dir is None:
        print("ERROR: 找不到 src/*/Resources/ui-{zh,en}.json")
        return 2
    zh_path = app_dir / "Resources" / "ui-zh.json"
    en_path = app_dir / "Resources" / "ui-en.json"

    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    en = json.loads(en_path.read_text(encoding="utf-8"))

    used: set[str] = set()
    for f in app_dir.rglob("*.razor"):
        src = f.read_text(encoding="utf-8")
        used.update(re.findall(r'Language\.T\("([^"]+)"\)', src))

    missing_zh = sorted(k for k in used if k not in zh)
    missing_en = sorted(k for k in used if k not in en)
    # 动态键/条件键无法静态匹配，死键列表只作参考
    unused = sorted(k for k in zh if k not in used)

    print(f"app dir: {app_dir}")
    print(f"used keys: {len(used)}")
    print(f"MISSING in zh: {missing_zh}")
    print(f"MISSING in en: {missing_en}")
    print(f"unused in zh (可能为动态键误报，仅供参考): {unused}")
    return 1 if (missing_zh or missing_en) else 0


if __name__ == "__main__":
    raise SystemExit(main())
