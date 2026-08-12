# xUnit Test Integration

Convention for xUnit test project setup in a Blazor component library.

## Project structure

```text
tests/Lib.Tests/Lib.Tests.csproj   → net6.0, references src/Lib.csproj
```

## Required packages

```xml
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.1" />
<PackageReference Include="xunit" Version="2.9.2" />
<PackageReference Include="xunit.runner.visualstudio" Version="2.8.2" />
<PackageReference Include="coverlet.collector" Version="6.0.2" />
```

## Test naming

Match source folder structure: `tests/Lib.Tests/Services/LibLayoutValidatorTests.cs` tests `src/Lib/Services/LibLayoutValidator.cs`.

## Verification

Every task ends with:
```bash
dotnet test Lib.slnx --no-restore
```

Expected: all tests pass, build succeeds, no new CS errors.

Only `NETSDK1138` (EOL target framework) warning is acceptable for `net6.0` builds.
