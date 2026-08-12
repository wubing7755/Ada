# Security hardening recipe (session-derived, verified on 真实项目 PR #4)

## 1. Parser-level sanitizer (HtmlSanitizer 8/9)

```csharp
using Ganss.Xss; // NOTE: lowercase 'ss'; NuGet ID is "HtmlSanitizer", NOT "Ganss.XSS.HtmlSanitizer"

private static readonly HtmlSanitizer Sanitizer = CreateSanitizer();

private static HtmlSanitizer CreateSanitizer()
{
    var sanitizer = new HtmlSanitizer();
    sanitizer.AllowedTags.Clear();
    foreach (var tag in new[] { "p","h1","h2","h3","h4","h5","h6","a","img","ul","ol","li",
        "blockquote","pre","code","table","thead","tbody","tr","th","td",
        "strong","em","del","br","hr","span","figure","figcaption" })
        sanitizer.AllowedTags.Add(tag);

    sanitizer.AllowedAttributes.Clear();
    foreach (var attr in new[] { "href","src","alt","title","class","lang" })
        sanitizer.AllowedAttributes.Add(attr);

    sanitizer.AllowedSchemes.Clear();
    foreach (var scheme in new[] { "http", "https", "mailto" })
        sanitizer.AllowedSchemes.Add(scheme);

    sanitizer.AllowedCssProperties.Clear(); // strip inline style
    return sanitizer;
}
```

Regression tests per bypass class (all previously slipped through a regex blacklist):

```csharp
[Theory]
[InlineData("<a href=\"jav&#x61;script:alert(1)\">x</a>")]
[InlineData("<a href=\"java&#115;cript:alert(1)\">x</a>")]
[InlineData("<a href=\"javascript&#x3a;alert(1)\">x</a>")]
[InlineData("<a href=\"java\tscript:alert(1)\">x</a>")]
[InlineData("<svg><a xlink:href=\"javascript:alert(1)\"><text>x</text></a></svg>")]
public void Sanitize_StripsObfuscatedJavascriptUris(string input)
    => Assert.DoesNotContain("javascript", RenderToHtml(input), StringComparison.OrdinalIgnoreCase);
```

## 2. JWT revocation (jti + in-memory list + OnTokenValidated)

Issue side (JwtTokenService.IssueAsync):
```csharp
new Claim(ClaimTypes.NameIdentifier, user.Id),
new Claim(ClaimTypes.Name, user.UserName ?? ""),
new Claim("jti", Guid.NewGuid().ToString("N")),   // revocation handle
```

Validation side (Program.cs JwtBearer options):
```csharp
options.TokenValidationParameters = new JwtTokenService(...).CreateValidationParameters();
options.TokenValidationParameters.ValidAlgorithms = new[] { SecurityAlgorithms.HmacSha256 };
options.Events = new JwtBearerEvents
{
    OnTokenValidated = context =>
    {
        var revocation = context.HttpContext.RequestServices.GetRequiredService<JwtRevocationService>();
        if (revocation.IsRevoked(context.Principal?.FindFirst("jti")?.Value))
            context.Fail("Token has been revoked.");
        return Task.CompletedTask;
    },
};
```

Revocation service: `ConcurrentDictionary<string, DateTimeOffset>` (jti → revokedAt),
`Revoke(jti)` + `IsRevoked(jti)` with lazy prune older than maxAge (e.g. tokenLife + slack).
Logout endpoint: `.RequireAuthorization()`, reads `principal.FindFirst("jti")`, revokes, 204.

Integration tests:
- login → `/api/auth/me` 200 → logout 204 → same token `/api/auth/me` **401**
- logout twice → second call 401 (token already revoked, auth fails before handler)
- anonymous logout → 401
- re-login issues fresh token → 200

## 3. Built-in rate limiter (net8) — lazy options + 429 test

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.OnRejected = (context, _) =>
    {
        if (context.Lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
            context.HttpContext.Response.Headers.RetryAfter =
                ((int)Math.Ceiling(retryAfter.TotalSeconds)).ToString();
        return ValueTask.CompletedTask;
    };
    options.AddPolicy("login", ctx =>
        RateLimitPartition.GetFixedWindowLimiter(ClientIp(ctx), _ =>
            new FixedWindowRateLimiterOptions
            {
                PermitLimit = ctx.RequestServices.GetRequiredService<IOptions<RateLimitOptions>>().Value.LoginPerMinute,
                Window = TimeSpan.FromMinutes(1),
                QueueLimit = 0,
            }));
});
// endpoints: app.MapPost("/api/auth/login", LoginAsync).RequireRateLimiting("login");
```

KEY: the `PermitLimit` must be read inside the partition delegate via `IOptions<T>` —
reading config at registration time means WebApplicationFactory overrides never apply.

429 test pattern — dedicated factory with a low limit so the shared class fixture stays clean:

```csharp
public class LoginRateLimitFactory : ApiFactory
{
    protected override IDictionary<string, string?> ExtraConfiguration => new()
        { ["RateLimiting:LoginPerMinute"] = "2" };
}
// first two login POSTs → 401, third → 429 with Retry-After header
```

Client IP: prefer `X-Forwarded-For` ONLY when the edge overwrites it; otherwise use
`context.Connection.RemoteIpAddress`. Document the nginx rule:
`proxy_set_header X-Forwarded-For $remote_addr;`

## 4. Media upload chain

```csharp
await using var input = file.OpenReadStream();
var header = new byte[12];
var headerLength = await input.ReadAsync(header);
if (!MediaStore.IsAllowedSignature(header, headerLength)) return 400; // magic bytes

input.Position = 0;
try
{
    using var image = await Image.LoadAsync(input);       // real decode
    if (image.Width > store.MaxDimension || image.Height > store.MaxDimension) return 400;
}
catch (Exception ex) when (ex is UnknownImageFormatException or InvalidImageContentException or NotSupportedException)
{
    return 400; // "文件不是有效的图片"
}

input.Position = 0;
await using var output = new FileStream(fullPath, FileMode.CreateNew);
await input.CopyToAsync(output);
```

Magic-byte signatures: PNG `89 50 4E 47`, JPEG `FF D8 FF`, GIF `GIF8[79]a`,
WebP `RIFF....WEBP`. Reject svg entirely (scriptable image).

## 5. Production secret fail-fast (Program.cs)

```csharp
if (!app.Environment.IsDevelopment()
    && string.Equals(builder.Configuration["Jwt:Key"], "dev-only-key-change-me-in-production-...", StringComparison.Ordinal))
    throw new InvalidOperationException("生产环境禁止使用开发 JWT 密钥，请通过环境变量注入 Jwt__Key。");
```
Test: dedicated ApiFactory with `["Jwt:Key"] = devValue` → `Assert.ThrowsAny<Exception>(() => factory.CreateClient())`.

## 6. Open-source attacker → defense mapping (condensed)

| White-box attack | Defense |
|---|---|
| Known rate-limit params → botnet bypass | per-IP limits + edge XFF overwrite + lockout per IP+user |
| Known lockout (5 fail/15min) → lock victims | don't lock on username alone; combine with IP |
| Open registration → spam/enumeration | `AllowRegistration=false` in prod, captcha, email verify |
| Dev JWT key / admin seed in git history | fail-fast + env-only secrets + secret scanning + filter-repo on leak |
| Regex sanitizer bypass hunting | parser-level allowlist sanitizer + per-bypass regression tests |
| localStorage token + any XSS → takeover | jti revocation, short expiry, CSP; evaluate HttpOnly cookie |
| Dependency CVE (public versions) | Dependabot + `dotnet list package --vulnerable` in CI |
| SQLite file on disk | store outside webroot, encrypted backups, file perms |
| Admin actions untraceable | audit log for admin writes |

## 7. TRX encoding-proof test counting

```sh
rm -rf tests/*/TestResults
dotnet test App.sln --nologo --logger "trx;LogFileName=verify.trx" >/dev/null 2>&1
echo "TEST_EXIT=$?"   # 0 = all projects passed (authoritative, locale-independent)
```
```python
import glob, xml.etree.ElementTree as ET
ns = {'t': 'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'}
passed = failed = total = 0
for f in glob.glob('tests/*/TestResults/verify.trx'):
    for r in ET.parse(f).getroot().findall('.//t:UnitTestResult', ns):
        total += 1
        if r.get('outcome') == 'Passed': passed += 1
        elif r.get('outcome') == 'Failed': failed += 1
print(f'TRX: passed={passed} failed={failed} total={total}')
```
(TRX has an XML namespace; plain `iter('Counters')` matches nothing.)
