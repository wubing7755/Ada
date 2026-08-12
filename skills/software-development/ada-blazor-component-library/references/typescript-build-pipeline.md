# TypeScript Build Pipeline

Convention for building TypeScript interop code in a Blazor component library.

## Convention

- **Source**: `ClientScripts/lib/index.ts` (TypeScript only)
- **Output**: `wwwroot/lib/lib.js` (generated, never committed)
- **Build tool**: `esbuild` via `npx` or `npm run build:js`

## package.json

```json
{
  "private": true,
  "scripts": {
    "build:js": "npx --yes esbuild@0.24.2 ClientScripts/lib/index.ts --bundle --format=esm --target=es2020 --outfile=wwwroot/lib/lib.js"
  },
  "devDependencies": {
    "esbuild": "0.24.2",
    "typescript": "^5.0.0"
  }
}
```

## MSBuild Integration

Add to `.csproj`:

```xml
<Target Name="BuildLibTypeScript" BeforeTargets="BeforeBuild">
  <Message Importance="high" Text="Building Lib TypeScript interop..." />
  <Exec Command="npm run build:js" WorkingDirectory="$(MSBuildProjectDirectory)" />
</Target>
```

## .gitignore

```gitignore
node_modules/
src/wwwroot/lib/*.js
src/wwwroot/lib/*.js.map
```

## Pitfall

MSBuild npm dependency: `npx --yes` downloads esbuild on first use. Ensure `node` and `npm` are available in the build environment.
