---
name: ada-windows-file-editing
description: "Edit Windows/MSYS code: CRLF patch, MSYS paths, cwd, verify."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [windows, msys, git-bash, crlf, patch, verification, hermes]
    related_skills: [ada-powershell-from-bash, ada-hermes-operations, ada-blazor-wasm-github-pages]
---

# Windows 文件编辑与验证（git-bash/MSYS）

在 Windows 上通过 Hermes 工具链（patch/read_file/terminal 走 git-bash）编辑与验证代码的操作知识。这些坑跨项目通用，在多次 Blazor WASM 批次交付中被反复验证。

## CRLF 与 patch 工具

项目文件常为 CRLF（尤其 Visual Studio 工程）；git `core.autocrlf=true` 时仓库内为 LF、工作树为 CRLF。

- **V4A 或多行 replace 会混入 LF 行尾**：diff 显示新增行为 `\n` 而上下文为 `\r\n`，`git diff` 把整段显示为删除+添加。修复：统一转回 CRLF：
  ```bash
  python3 -c "p=r'<file>'; d=open(p,'rb').read(); open(p,'wb').write(d.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))"
  ```
  修复后 `git diff --stat` 恢复为合理行数（例如 19 行而不是整文件）。
- **`replace_all` 多行匹配失败**：old_string 尾部带换行时，CRLF 文件常报 "Could not find a match"（即便内容明显存在）。应对：
  1. 去掉 old_string 尾部换行；
  2. 改为单行匹配（如只匹配 `      <image>media/projects/atlos.png</image>` 这一行，而不是整个 `<demo>...</demo>` 块）；
  3. 先做唯一上下文的替换，再 `replace_all` 处理剩余相同片段。
- **误删/误替换风险**：replace 时若 old_string 是其他行的子串（如 `      <image>` 也是 `      <image>xxx</image>` 的前缀），会截断合法行——用整行或带前后缀的唯一串，并检查 diff。

## read_file 误判 binary

UTF-8 文本（含中文全角字符的 `.md`/`.xml`/`Resources/*.json` 文件——`.hermes/plans/*.md`、仓库 `README.md`、`docs/*.md` 与 `Resources/ui-zh.json`/`ui-en.json` 都中过招）偶发被 `read_file` 报 "Binary file - cannot display as text"，即使 `file` 显示 "Unicode text, UTF-8"。应急读取：
```bash
file <path>                      # 确认真实为文本
grep -n "^#" <path>              # 定位章节标题
sed -n '1,150p' <path>           # 分段读取
iconv -f UTF-8 -t UTF-8 <path>   # 或整体转读（中文 CRLF md 可用，read_file 误判不影响终端读字节）
```

## MSYS 路径转换（Windows 原生程序参数）

MSYS 会把 POSIX 路径自动转换为 Windows 路径，但规则不直观：

| 传给 dotnet/原生程序 | 实际落盘 | 备注 |
|---|---|---|
| `-o /tmp/x` | `C:\tmp\x` | `/tmp` 被转换 |
| `-o /c/tmp/x` | `C:\c\tmp\x` | **意外嵌套**：`/c/` 被当作相对路径拼接 |
| `-o "C:/tmp/x"` | `C:\tmp\x` | ✅ 带盘符正斜杠不触发转换，最稳 |

bash 侧访问产物时先 `ls` 确认实际位置（可能是 `/c/c/tmp/x`）。临时输出目录用正斜杠 Windows 路径 `"C:/tmp/<name>"` 避免嵌套。

**curl -F 上传的绝对 /tmp 路径会失败**（实测：`curl -F "file=@/tmp/test-upload.png"` 返回空响应/JSON 解析失败，而 `cd /tmp && -F "file=@test-upload.png"` 成功）——MSYS 的路径转换与 curl 自身对 `@` 路径的处理叠加会出问题。上传文件一律 `cd` 进目录后用相对文件名。

## Windows 大小写不敏感：运行时目录与源码目录同名冲突（安全）

Windows 文件系统**大小写不敏感**（`media` == `Media` 是同一物理目录），而 git/文件工具按大小写敏感处理。当**运行时目录的默认名与源码目录同名（仅大小写不同）**时，两者在 Windows 上合并为同一目录——最危险的结果是静态文件服务暴露源码（真实项目实测：`MediaStore` 默认根 `media` 与源码目录 `src/Api/Media/` 冲突，`/media/**` 静态映射把 `MediaStore.cs`/`MediaEndpoints.cs` 当静态文件公开，`GET /media/MediaStore.cs` 返回 200）。

识别信号与排查：
- 媒体/上传列表出现 `.cs`/源码文件，或 `ls src/Api/media` 显示源码文件——先怀疑大小写冲突而非"文件被复制"；
- 用 `git check-ignore` 确认该目录未跟踪；`.gitignore` 只能忽略子目录（如 `media/uploads/`），**不能整体忽略 `media/`**（会连源码目录一起忽略/删除）。

修复模式：
1. **换掉运行时目录默认名**（`media` → `media-store`），避免与源码目录任何大小写变体重合；appsettings 与部署文档（nginx alias、systemd 路径）同步；
2. 清理污染时用**源码目录的实际大小写**删子目录（`rm -rf src/Portfolio.Api/Media/uploads`），绝不能用小写 `media/` 删除——Windows 下会把 `Media/` 源码目录一起删掉；
3. 加防回归测试：断言默认根路径 ≠ 与源码目录同名的路径（如 `Assert.NotEqual(Path.Combine(contentRoot, "media"), store.RootPath)`）。

此规则适用于任何"运行时写目录默认名"：uploads、data、cache 等，命名前先检查仓库是否存在同名词干（含大小写变体）。

## terminal 的 cwd 跨调用持久

`cd` 到 scratch 目录（如 `/c/tmp/pp-verify`）后，**后续调用**的 dotnet/git 会在该目录执行，报"项目文件不存在"/"Not a git repository"。切目录后先 `cd` 回仓库根（`cd /c/Users/<user>/source/repos/<repo>`）再跑构建/测试。`pwd` 确认。

## 编辑后验证（hermes-verify 模式）

代码编辑后，系统检测器可能要求创建聚焦验证脚本：

1. 创建 `$LOCALAPPDATA/Temp/hermes-verify-*.py`（**前缀必须 `hermes-verify-`**，用 write_file 写、python3 跑）：
   - 对本次改动做行为断言（grep/解析源码、检查生成数据）；
   - 内嵌 canonical 命令（`dotnet build` / `dotnet test`）并把退出码/输出解析为断言；
   - 运行后删除脚本。
2. 检测器会持续把**已删除的 Temp 脚本和 C:\tmp scratch 文件**计入 changed paths 造成 unverified 误报。处理：按流程创建→运行→清理一次，然后直接跑一次 canonical 命令（如 `dotnet test <App>.sln`）让输出在 terminal 可见，并说明误报来源；不要反复创建脚本。
3. 临时脚本自身 bug 也会造成 FAIL（如 python3 无 PIL、grep 模式过宽匹配到 `placeholder.profile` 等合法键）——先修正脚本断言而非改代码。

## 批量多行替换 CRLF 文件（patch 多行匹配失败时）

patch 工具的**多行 old_string 在 CRLF 文件上不可靠**（"Could not find a match"，fuzzy 不归一化行尾）；write_file 整文件重写会变 LF。对 CSS/JSON 等需多处多行块修改时，用 execute_code 跑 Python 精确替换（保留 CRLF、逐处验证）：

```python
NL = '\r\n'
def read(p):
    with open(p, 'r', encoding='utf-8', newline='') as f:   # newline='' 保留 \r\n
        return f.read()                                      # Path.read_text 不支持 newline 参数
def replace_once(path, old_lines, new_lines, label):
    s = read(path)
    old, new = NL.join(old_lines), NL.join(new_lines)
    if s.count(old) != 1:
        print(f'FAIL {label}: count={s.count(old)}'); return False
    write(path, s.replace(old, new)); print(f'OK   {label}'); return True
```

old/new 用 `'\r\n'.join(lines)` 构造；每次替换断言 `count == 1`（避免误删/多删）；插入锚点用 `s.count(anchor) == 1` 守卫。已验证：6 个 CRLF CSS 文件 10 处块替换 + 死代码区间删除（split 后按行号区间 del），一次通过且 `git diff --stat` 行数合理。

**全有或全无写入陷阱**：若把多处替换放进一个脚本、最后才 `if ok: write(path, s)`，任何一处断言失败（如两处缩进不同导致锚点只匹配 1/2）会让**整个文件不写盘**——已成功的替换只存在于内存。随后"只修失败锚点"的第二个脚本从**磁盘**读文件，拿到的是没有前面修改的旧内容，写盘后前面修改静默丢失（R3 实测：图片仍是 `<a>`，直到浏览器验证才暴露，多浪费一轮 publish）。对策：
1. 失败时打印每处 count，**先 grep/read_file 核对磁盘现状**再重跑，绝不"只修一处"直接写盘；
2. 改完文件后、build/publish 前先 `grep -n` 关键标记确认落盘；
3. 或改为逐处独立写盘/分文件写，避免一处失败拖垮全部。

**count 子串陷阱（缩进层级）**：`s.count(old)` 是子串匹配——16 空格缩进的行会命中 24 空格行的**内部**（24 空格行包含"16 空格 + 内容"），于是 count=2 误判而放弃写入（R4 实测：`                <span class="project-stars">` 匹配到 24 空格 featured 行的子串）。对策：old 串带相邻上下文行（如上一行 `}`）做唯一化，或正则锚定行首；`replace` 用同一带上下文的串。

## 验证脚本解码 dotnet 中文输出（GBK）

Windows 中文环境 dotnet/MSBuild 输出是 **GBK（cp936）**：python subprocess 用 `encoding="utf-8", errors="replace"` 解码得到乱码（如 `ʧ��: 0`），**字符串断言必然失配 → 误报 FAIL**（canonical 144/144 被脚本判 FAIL 的根因）。修正：

```python
def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="gbk", errors="replace")
# build：不要断言英文 "0 error"（实际是 "0 个错误"）
build_ok = b.returncode == 0 and not re.search(r"error\s+CS\d+", b.stdout + b.stderr)
# test：断言本地化输出（全绿时标题为"已通过!"，计数行是"失败: N，通过: M"；有失败时标题变"失败!"。
# "已通过"只出现在全绿标题里，有失败时断言会失配——用计数行断言更稳）
test_ok = t.returncode == 0 and "失败:     0" in t.stdout and "通过:" in t.stdout
```

若先按乱码写了断言，**先修脚本断言而非怀疑代码**——对照终端直接可见的 canonical 输出判断。

## CRLF 补充细节（批量编辑实测）

- **replace 模式的多行 new_string 会自动适配 CRLF**（插入行 `\r\n`，`has_bare_lf: False`）——与 V4A patch 不同。单行 old + 多行 new 是安全插入方式。
- **单行 old + 空 new 删除会留空行**（JSON 仍合法，lint OK 但 diff 难看）：收尾用归一化脚本去空行 + 统一 CRLF：
  ```python
  d = pathlib.Path(p).read_bytes()
  lines = [l for l in d.split(b'\r\n') if l.strip()]
  pathlib.Path(p).write_bytes(b'\r\n'.join(lines) + b'\r\n')
  ```
- 多行 old_string 删除整块时，用单行唯一锚点（如 `"footer.explore": "浏览内容",`）替换为空。

## playwright 移动端视口验证（Windows）

本地真实移动端布局验证（页脚单列/横向溢出/月份分组）：

- `npx -p playwright node script.js` **不暴露 `require('playwright')`**（npx 只加 PATH bin，不设 NODE_PATH）→ 在临时目录 `npm init -y && npm i playwright@<version> --no-audit --no-fund`，node 脚本放该目录跑。
- ms-playwright 浏览器缓存版本与 npm 包版本不匹配时（如缓存 chromium-1228 但包要 chromium-1140），用 `chromium.launch({ headless: true, channel: 'chrome' })` 走系统 Chrome，免下载。
- 脚本要点：`viewport: { width: 375, height: 812 }`；`page.on('console')` 收集 error；`document.documentElement.scrollWidth > window.innerWidth` 判横向溢出；`getComputedStyle(el).gridTemplateColumns.split(' ').length` 判列数。

## Verification Checklist

- [ ] 修改 CRLF 文件后检查 `git diff` 无整段换行变化
- [ ] `replace_all` 失败时改单行匹配/去尾部换行
- [ ] 给 dotnet 传输出路径用 `"C:/tmp/x"` 形式
- [ ] `cd` 到 scratch 后已回仓库根再跑构建
- [ ] hermes-verify 脚本已创建→运行→清理，canonical 输出可见

## Reference Files

本技能无独立 references：Blazor 交互/表单绑定陷阱已由 `ada-blazor-interaction-pitfalls` 与 `ada-blazor-interop-pitfalls` 覆盖（如 `[SupplyParameterFromQuery]` 变化需在 `OnParametersSetAsync` 重载、`@bind`+`@onchange` 同元素 RZ10008、引用组件前先读 `[Parameter]` 签名）。
