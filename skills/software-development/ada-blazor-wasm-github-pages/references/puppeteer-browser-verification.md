# Blazor WASM 实机浏览器验证：puppeteer-core + 系统 Chrome（Windows）

当需要验证 Blazor WASM 的真实渲染（diff/layout/CSS 行为，bUnit 无法复现）、加载态、
交互切换，或没有 vision provider 时，用本配方。实测于真实 GitHub Pages Blazor WASM 站点（2026-08），
验证脚本全部成功（响应式 6 视口、排序切换、加载动画、fallback 降级、锚点滚动）。

## 为什么用 puppeteer-core + 系统 Chrome

- `puppeteer` 会下载 ~130MB Chromium；`puppeteer-core` 直接驱动已装的 Chrome/Edge，零下载。
- headless `--headless=new` 截 WASM 页面要等真实网络加载：`--virtual-time-budget` 不等待
  HTTP 下载，`--timeout` 也常截到加载页（8KB 全背景色）。**放弃 chrome --headless CLI 截图，
  改用 puppeteer 脚本 + `waitForFunction`**——这是本会话最大的工具教训。

## 最小可用脚本骨架

```js
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://localhost:5088';

(async () => {
  const b = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 800 });
  await p.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 });
  // WASM 水合完成标志：index.html 的 loader 消失、main 出现 h1
  await p.waitForFunction(() => document.querySelector('main h1') !== null, { timeout: 45000 });
  await new Promise(r => setTimeout(r, 1000)); // 稳定期
  const info = await p.evaluate(() => ({ ... }));
  console.log(JSON.stringify(info, null, 1));
  await b.close();
})();
```

- **运行**：脚本放 OS Temp（`tempfile.mkdtemp(prefix='hermes-verify-')` 产出目录），
  `NODE_PATH="C:/Users/.../Temp/pp-shots/node_modules" node script.js "$VERIFY_DIR"` ——
  NODE_PATH 指向装有 puppeteer-core 的 node_modules（npm init -y && npm i puppeteer-core 一次）。
- **异步数据等待**（GitHub API fallback）：`waitForFunction(() => document.querySelectorAll('.project-card').length > 0 || document.querySelector('.page-hint-warn') !== null, {timeout:30000})`。
- **加载态捕获**：用 `{ waitUntil: 'domcontentloaded' }` 导航 + `waitForSelector('.loading-indicator', {timeout:20000})`，
  在异步数据 resolve 前截住加载动画；再等指示器消失 + 卡片出现。
- **交互断言**：`page.evaluate` 里 `btn.click()` 后等 ~1s，再读状态；`aria-pressed` / class 切换都断言。
- **reduced-motion 验证**：`page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }])`，
  断言 `getComputedStyle(el).animationName === 'none'`。
- 控制台错误：`page.on('pageerror'/'console')` 收集；403 只来自 `api.github.com` 时是**预期的
  GitHub 限流 fallback**，不是站点缺陷——用 response 监听确认 403 URL 来源。

## 无 vision provider 时的视觉验证（PIL 截图分析）

`browser_vision` / `vision_analyze` 报 "No LLM provider configured for task=vision" 时，
截图仍会保存。用 Python + PIL 做可量化分析（不要只看"有没有图"）：

```python
from PIL import Image
import collections
im = Image.open(png).convert('RGB')
small = im.resize((w//4, h//4))                       # 采样，避免逐像素
colors = collections.Counter(small.getdata())
# 饱和色（非灰度）直方图 → 验证强调色出现/消失、火焰色清除
sat = [(f'#{r:02x}{g:02x}{b:02x}', n) for (r,g,b), n in colors.most_common(500)
       if max((r,g,b))-min((r,g,b)) > 50]
# 定位特定色像素所在区域 → 判断元素在页面的 y 带
# 行剖面（每行非背景像素比例）→ 内容条带、Hero 是否独占整行
```

## WCAG 对比度快速计算（Python）

验证颜色 token 是否达标（文本 ≥4.5:1、非文本 ≥3:1），用相对亮度公式：

```python
def lum(r,g,b):
    def f(c):
        c=c/255
        return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def ratio(a,b):
    l1,l2=lum(*a),lum(*b)
    if l1<l2: l1,l2=l2,l1
    return (l1+0.05)/(l2+0.05)
```

本会话用它发现金色 `#e6a817` 白底仅 2.10:1（不达标），改为深金 `#8a6d00`（4.47-4.92:1）；
警告文字金色→红 `#c0392b`（5.44:1）。

## 陷阱

- `window.resizeTo` 对 puppeteer 远程/headless 无效——用 `page.setViewport`。
- headless Chrome CLI `--screenshot` 截 WASM 页面几乎必截到加载页；即使 `--timeout=50000`
  + user-data-dir 缓存也失败。坚持 puppeteer 脚本。
- `node --check` 通过 ≠ 运行成功；缺 `puppeteer-core` 时 `Cannot find module`——设 NODE_PATH。
- 验证脚本运行完删除（见 SKILL.md "Verification-loop self-lock"），不要在仓库里留 `*.js` 测试脚本。
