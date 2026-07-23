# TypeScript Build Pipeline

Convention for building TypeScript interop code in a Blazor component library.

## Convention

- **Source**: `ClientScripts/xdocker/index.ts` (TypeScript only)
- **Output**: `wwwroot/xdocker/xdocker.js` (generated, never committed)
- **Build tool**: `esbuild` via `npx` or `npm run build:js`

## package.json

```json
{
  "private": true,
  "scripts": {
    "build:js": "npx --yes esbuild@0.24.2 ClientScripts/xdocker/index.ts --bundle --format=esm --target=es2020 --outfile=wwwroot/xdocker/xdocker.js"
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
<Target Name="BuildXDockerTypeScript" BeforeTargets="BeforeBuild">
  <Message Importance="high" Text="Building XDocker TypeScript interop..." />
  <Exec Command="npm run build:js" WorkingDirectory="$(MSBuildProjectDirectory)" />
</Target>
```

## .gitignore

```gitignore
node_modules/
src/wwwroot/xdocker/*.js
src/wwwroot/xdocker/*.js.map
```

## Pitfall

MSBuild npm dependency: `npx --yes` downloads esbuild on first use. Ensure `node` and `npm` are available in the build environment.
