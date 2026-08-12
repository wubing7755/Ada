# Supply-chain CI gates (verified on 真实项目, 2026-08)

## NuGet vulnerability gate that actually fails CI

`dotnet list package --vulnerable --include-transitive` PRINTS vulnerable packages but
**exits 0** on SDK 8.0.423. A bare step in a workflow does not fail the build. Gate with
`--format json` and count vulnerability entries:

```yaml
      - name: Audit NuGet vulnerabilities (fail on any)
        run: |
          dotnet list App.sln package --vulnerable --include-transitive --format json > vulns.json
          python3 - <<'EOF'
          import json, sys
          with open('vulns.json', encoding='utf-8') as f:
              data = json.load(f)
          count = 0
          for project in data.get('projects', []):
              for framework in project.get('frameworks', []):
                  for pkg in framework.get('topLevelPackages', []) + framework.get('transitivePackages', []):
                      count += len(pkg.get('vulnerabilities', []))
          print(f'vulnerable packages: {count}')
          if count > 0:
              sys.exit(1)
          EOF
```

Restore-time audit (warning, not error — the CI gate enforces): in `Directory.Build.props`

```xml
<NuGetAudit>true</NuGetAudit>
<NuGetAuditMode>all</NuGetAuditMode>
```

PITFALL: XML comments must not contain `--` (double hyphen); MSBuild fails to parse the
.props with "An XML comment cannot contain '--'". Write `dotnet list package -vulnerable`
in comments, never `--vulnerable`.

## SQLitePCLRaw transitive CVE (real finding)

`Microsoft.EntityFrameworkCore.Sqlite 8.0.29` pulls `SQLitePCLRaw.lib.e_sqlite3 2.1.6` →
advisory **GHSA-2m69-gcr7-jv3q** (High, vulnerable native SQLite dependency). Range:
ALL 2.1.x ≤ 2.1.11 affected (`last_affected: 2.1.11`); the 3.0.x line carries the fix
(latest 3.0.5). Pin in the API csproj:

```xml
<PackageReference Include="SQLitePCLRaw.bundle_e_sqlite3" Version="3.0.5" />
```

Verified: full backend suite (49 tests incl. SQLite CRUD) passes on 3.0.5; the JSON gate
then reports 0.

## Workflow security contract tests

A repo may embed `.github/workflows/*.yml` as `<EmbeddedResource>` in a test project and
assert invariants over the LIVE file (edits are tracked automatically). On
真实项目 `tests/App.Tests/WorkflowSecurityContractTests.cs`
asserts, per workflow:

- every `uses:` line matches `^uses: [^@\s]+@[0-9a-f]{40} # v\d+$` (full SHA pin)
- PR-triggered CI contains NO `GITHUB_TOKEN` and NO `secrets.` string at all
- `persist-credentials: false` present exactly N times
- deploy workflow: `permissions: {}` at top, per-job separation (build: contents: read;
  deploy: pages: write + id-token: write), no `secrets.GITHUB_TOKEN`

Consequence: gitleaks-action (which REQUIRES `GITHUB_TOKEN` to post findings) violates the
"no token in PR CI" contract. Use the no-token docker scan instead:

```yaml
      - name: Scan for leaked secrets (gitleaks, no token)
        run: |
          docker run --rm -v "${PWD}:/repo" -w /repo zricethezav/gitleaks:v8.30.1 detect --source /repo --no-banner
```

Secret-scan allowlist: for an open-source repo, already-public dev/test values (dev JWT
key, test keys) live in the repo; allowlist them in `.gitleaks.toml` so CI isn't red on
every run, while the default ruleset still catches NEW real secrets:

```toml
[extend]
useDefault = true

[allowlist]
regexes = [
  '''dev-only-key-change-me-in-production-[0-9a-zA-Z-]+''',
  '''integration-test-key-[0-9a-zA-Z-]+''',
]
```
