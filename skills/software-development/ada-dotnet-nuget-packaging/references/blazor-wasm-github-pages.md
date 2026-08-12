# Blazor WASM Demo → GitHub Pages (as part of the release loop)

Deploying a frozen Blazor WASM sample site to GitHub Pages so it showcases the
library. Works for any .NET 6+ WASM demo that consumes the published NuGet
package; verified on a real library (repo `<owner>/<repo>`, site at `https://<owner>.github.io/<repo>/`).

## When to use

- A NuGet library wants a public live demo of the consumer sample.
- The demo is FROZEN: it only bumps the referenced package version at release
  nodes (or fixes a showcase bug), and the Pages site must always reflect the
  officially published package — never a local pack or cache.

## Design decisions (the part that matters)

1. **Source `index.html` keeps `<base href="/" />`** — local `dotnet run`
   development keeps working. The CI workflow rewrites it to the Pages
   subpath after publish:
   ```bash
   sed -i 's|<base href="/" />|<base href="/<repo>/" />|' publish/demo/wwwroot/index.html
   ```
   .NET 6 WASM requires an ABSOLUTE base href (relative base support came
   later); the repo name is fixed so hardcoding `/<repo>/` is fine (breaks
   only if the repo is renamed).
2. **Deploy resolves the official package**: `dotnet publish ... --source
   https://api.nuget.org/v3/index.json` — `--source` OVERRIDES all
   NuGet.Config sources, so the local feed and `.packages`
   cache are never involved. The demo props pin the version, so deploy
   doubles as a "package is consumable on nuget.org" check — publish the
   package BEFORE deploying or the workflow fails (fail-fast, desired).
3. **THE PITFALL — artifact root maps to `/<repo>/` automatically; do NOT
   add a repo-name directory inside the artifact.** GitHub Pages project
   sites serve the deployed artifact ROOT at `https://<owner>.github.io/<repo>/`.
   Staging `site/<repo>/index.html` puts the app at `/<repo>/<repo>/index.html`,
   `/<repo>/index.html` 404s, and a naive root `404.html` redirecting
   `/<repo>/` back to itself produces an infinite refresh loop (browser shows
   `TypeError: can't access property "appendChild", document.body is null`).
   Stage the publish output **directly at the site root**:
   ```bash
   mkdir -p site
   cp -r publish/demo/wwwroot/. site/     # site/index.html -> /<repo>/index.html
   ```
   `actions/upload-pages-artifact@v3` path = `site`; `actions/deploy-pages@v4`
   follows. The `404.html` shipped inside wwwroot lands at `site/404.html`
   automatically (no extra copy step needed).
4. **404.html must NOT redirect asset requests** — only extension-less page
   navigations. A "redirect everything to `/<repo>/`" fallback loops forever
   when a bundled asset 404s (`/<repo>/_framework/missing.js` → 404.html →
   redirect → index → asks again):
   ```html
   <script>
     (function () {
       var path = window.location.pathname;
       var last = path.substring(path.lastIndexOf("/") + 1);
       if (last.indexOf(".") === -1) {
         window.location.replace("/<repo>/" + window.location.search + window.location.hash);
       }
     })();
   </script>
   ```
5. **Workflow shape**: manual `workflow_dispatch` (frozen demo — don't
   redeploy on every push), `permissions: pages: write, id-token: write`,
   `environment: github-pages` with `url: ${{ steps.deployment.outputs.page_url }}`,
   `actions/setup-dotnet@v4` with `dotnet-version: '6.0.x'` (the SDK must
   match the target framework for WASM publish).
6. **One-time user step**: Repo Settings → Pages → Source: **GitHub Actions**
   (the deploy-from-Actions mode, not a gh-pages branch). The workflow only
   shows in the Actions tab after the file exists on the DEFAULT branch —
   a workflow on a feature branch is invisible.

## Verification recipe (local, before merging the workflow)

Stage under the mapped subpath — the EXACT structure GitHub Pages produces:

```bash
dotnet publish samples/<Demo>/<Demo>.csproj -c Release -o publish/demo \
  --source https://api.nuget.org/v3/index.json   # confirm assets.json shows <Pkg>/<version>
sed -i 's|<base href="/" />|<base href="/<repo>/" />|' publish/demo/wwwroot/index.html
mkdir -p /tmp/pages-root/<repo>
cp -r publish/demo/wwwroot/. /tmp/pages-root/<repo>/   # artifact root -> /<repo>/
cd /tmp/pages-root && python -m http.server 8097
# probe the exact URLs a browser hits:
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8097/<repo>/index.html
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8097/<repo>/_framework/blazor.webassembly.js
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8097/<repo>/_content/<Pkg>/app-v2/app.css
# browser: http://127.0.0.1:8097/<repo>/ -> workspace renders, base href = /<repo>/,
# splitter drag works; http.server log shows every /<repo>/_framework/*.dll 200
```

## Diagnosing a live 404 / refresh loop

Probe both paths on the live site:

```bash
curl -s -o /dev/null -w "%{http_code}" https://<owner>.github.io/<repo>/index.html
curl -s -o /dev/null -w "%{http_code}" https://<owner>.github.io/<repo>/<repo>/index.html
```

If the DOUBLED path returns 200 while the single one 404s, the artifact
contains an extra repo-name directory — stage at the artifact root instead.
A 200 on `/repo/404.html` alongside a 404 on `/repo/index.html` confirms the
mapping bug.

## Pitfalls

- **Stale WASM dev-server processes serve OLD DLLs — "my edit had no
  effect" is usually a zombie server.** On Windows, `dotnet run` spawned in a
  background terminal survives `process kill` (the bash wrapper dies, the
  Kestrel/DevServer child keeps the port and serves the previous build).
  Symptom: the browser shows old razor content even after a clean rebuild;
  `netstat -ano | grep :<port>` shows a LISTENING pid you already "killed".
  Fix: kill by port, not by session — `taskkill /PID <pid> /F` for every
  LISTENING pid on the dev ports, confirm the port is free (curl → 000),
  then start exactly one server. Always verify the SERVED dll, not the build
  output: `curl -s <origin>/_framework/<App>.dll | grep` for a string you
  just added — absent = stale server, not a razor bug.
- **pyyaml `safe_load` parses `on:` as boolean `True`** (YAML 1.1) — workflow
  validation must use text greps for `on:`/`workflow_dispatch`, or only parse
  the non-`on` structure; don't trust a KeyError-driven failure.
- WASM publish output is `publish/wwwroot/` (index.html + `_framework/` +
  `_content/`) — point upload-pages-artifact at the STAGED root, not the
  publish root.
- The demo consumes the package's bundled JS/CSS (`_content/<Pkg>/...`); no
  npm/build step needed in the deploy workflow.
- Don't attach deploy byproducts to the GitHub Release — the nupkg is the
  release asset; the Pages site is rebuilt from the workflow.
