# Batch Refactoring with execute_code

When an API migration requires updating the same pattern across 10+ files, `patch(mode='replace')` with `replace_all` does not work on directory targets (it needs a file path). Use `execute_code` with hermes_tools and regex:

```python
from hermes_tools import read_file, write_file
import re

files = ["file1.cs", "file2.cs", ...]
rules = [
    (r"(\w+)\.DockPanels\.Add\(",      r"\1.AddDockPanel("),
    (r"(\w+)\.EditorViews\.RemoveAll\(", r"\1.RemoveEditorViewsWhere("),
    # Order matters: longer/more-specific patterns first
]

for f in files:
    r = read_file(f, limit=2000)
    # Strip line numbers from read_file output format
    lines = [l.split("|", 1)[1] if "|" in l else l for l in r["content"].split("\n")]
    text = "\n".join(lines)
    for pat, rep in rules:
        text = re.sub(pat, rep, text)
    write_file(f, text)
```

**Caveat**: `read_file` returns line-numbered output (`N|content`). Strip the prefix before regex, or include `\d+\|` in patterns. The script above strips them.

**Verification**: After batch refactoring, always `dotnet build` to catch any missed call sites before running tests.
