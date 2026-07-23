# WiX perMachine MSI — User-Personal Desktop Shortcut via PowerShell CA

In a `Scope="perMachine"` MSI, `StandardDirectory Id="DesktopFolder"` resolves to
`C:\Users\Public\Desktop` (the All Users desktop). To land the shortcut on the
**current user's personal desktop**, use a deferred PowerShell custom action.

## Pattern overview

1. A `.ps1` script is installed alongside the product files (e.g., `bin/create-shortcut.ps1`).
2. `<SetProperty>` primes the command line for `WixQuietExec64`.
3. `<CustomAction>` with `BinaryRef="Wix4UtilCA_X64"` + `DllEntry="WixQuietExec64"`
   runs the PowerShell script after files are installed.
4. `Impersonate="yes"` runs the command as the installing user (not SYSTEM), so
   `[Environment]::GetFolderPath('Desktop')` returns the correct personal path.
5. A mirrored `<SetProperty>` + `<CustomAction>` pair removes the shortcut on uninstall.
6. `<CustomActionRef>` in `Product.wxs` pulls the actions into the Package.

## Files

### installer/create-shortcut.ps1

```powershell
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\CProjectStandard.lnk')
$lnk.TargetPath = $args[0]
$lnk.WorkingDirectory = $args[1]
$lnk.IconLocation = (Join-Path $args[1] "share\c-project-standard\res\cproject.ico")
$lnk.Save()
```

**IMPORTANT — `Join-Path` is mandatory here, not string interpolation.**  
`"$($args[1])share\c-project-standard\..."` drops the backslash before `s` because
PowerShell string interpolation treats `\s` as a character (not an escape, but it
strips the `\`). `Join-Path` resolves the backslash correctly regardless of the
first character of the suffix. The resulting `IconLocation` value will be something
like `C:\Program Files\CProjectStandard\share\c-project-standard\res\cproject.ico`
(Windows Installer appends `,0` for the icon index automatically).

### installer/remove-shortcut.ps1

```powershell
Remove-Item ([Environment]::GetFolderPath('Desktop') + '\CProjectStandard.lnk') -ErrorAction SilentlyContinue
```

### installer/Shortcuts.wxs excerpt

```xml
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">

  <Fragment>
    <!-- Command lines for WixQuietExec64.
         [#File_bin_create_shortcut_ps1] is a key-path File reference;
         [INSTALLDIR] is the MSI install-directory property. Both are
         resolved by Windows Installer at scheduling time (the SetProperty
         runs in the execute sequence, after CostFinalize). -->
    <SetProperty Id="CreateDesktopShortcut"
                 Value="&quot;C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe&quot; -NoProfile -WindowStyle Hidden -File &quot;[#File_bin_create_shortcut_ps1]&quot; &quot;[#File_bin_run_wizard]&quot; &quot;[INSTALLDIR]&quot;"
                 After="CostFinalize" />
    <SetProperty Id="RemoveDesktopShortcut"
                 Value="&quot;C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe&quot; -NoProfile -WindowStyle Hidden -File &quot;[#File_bin_remove_shortcut_ps1]&quot;"
                 After="CostFinalize" />

    <ComponentGroup Id="ShortcutsComponents">
      <!-- Registry marker only — the actual .lnk is created by the CA. -->
      <Component Id="Shortcut_Desktop"
                 Guid="A1B2C3D4-2222-2222-2222-000000000001"
                 Directory="INSTALLDIR">
        <RegistryValue Root="HKCU"
                       Key="Software\CProjectStandard"
                       Name="DesktopShortcutInstalled"
                       Type="integer" Value="1" KeyPath="yes" />
      </Component>
      <!-- Start Menu entries as usual (Directory="ApplicationProgramsFolder" under ProgramMenuFolder). -->
    </ComponentGroup>
  </Fragment>

  <!-- Deferred custom actions backed by WixQuietExec64 (from WixToolset.Util.wixext).
       The WixQuietExec64 pattern: the CustomAction Id is the property prefix.
       WiX reads property "CreateDesktopShortcut" when that custom action fires. -->
  <Fragment>
    <CustomAction Id="CreateDesktopShortcut"
                  BinaryRef="Wix4UtilCA_X64"
                  DllEntry="WixQuietExec64"
                  Execute="deferred"
                  Impersonate="yes"
                  Return="check" />

    <CustomAction Id="RemoveDesktopShortcut"
                  BinaryRef="Wix4UtilCA_X64"
                  DllEntry="WixQuietExec64"
                  Execute="deferred"
                  Impersonate="yes"
                  Return="ignore" />

    <InstallExecuteSequence>
      <Custom Action="CreateDesktopShortcut" After="InstallFiles" Condition="NOT Installed" />
      <Custom Action="RemoveDesktopShortcut" Before="RemoveFiles" Condition="Installed" />
    </InstallExecuteSequence>
  </Fragment>
</Wix>
```

### installer/Product.wxs — CustomActionRef (required)

Without `<CustomActionRef>`, the linker ignores the custom actions even though they
are defined in a Fragment:

```xml
<Package ...>
  ...
  <CustomActionRef Id="CreateDesktopShortcut" />
  <CustomActionRef Id="RemoveDesktopShortcut" />
  ...
</Package>
```

## WiX 6 schema traps hit here

| Trap | Symptom | Fix |
|---|---|---|
| `<Custom>` inner text for condition | `WIX0400: illegal inner text: 'NOT Installed'` | Use `Condition="NOT Installed"` attribute, not inner text or CDATA |
| `<CustomAction>` not in `<Fragment>` | `WIX0005: unexpected child element 'CustomAction'` | Wrap in `<Fragment>` |
| Missing `<CustomActionRef>` | Action silently skipped; log shows no "Action start" for the CA | Add `<CustomActionRef Id="X"/>` in `<Package>` |
| Missing `WixToolset.Util.wixext` | `WIX0094: identifier 'WixAction:...' could not be found` | `wix extension add WixToolset.Util.wixext`; pass `-ext` to `wix build` |
| `SetProperty` Id clash between install/uninstall CAs | Uninstall CA sees wrong command line | Use **different Ids** for install and uninstall (e.g., `CreateDesktopShortcut` vs `RemoveDesktopShortcut`) |
| `&quot;` escaping in `SetProperty/@Value` | Command line garbled in the log, `Error 0x80070001` | Use `-File` to a `.ps1` script rather than `-Command` with inline PowerShell; let WiX handle the `[#File_X]` key-path references directly |
| PowerShell `-Command` with `'` (single quotes) | Garbled Unicode in WixQuietExec64 output, `Error 0x80070001` | Use `-File` instead; the `.ps1` file can contain any characters |
| PowerShell `"$($args[1])share\..."` (string interpolation for IconLocation) | Missing backslash before `s` — shortcut has no icon | Use `(Join-Path $args[1] "share\...")` — see `create-shortcut.ps1` above |

## CMake integration

The `.ps1` files must be available in the staging directory before `wix build`. Add
them to `install-staging` via `cmake -E copy_if_different`:

```cmake
add_custom_target(install-staging
    ...
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CPROJECT_INSTALLER_DIR}/create-shortcut.ps1"
        "${CMAKE_CURRENT_BINARY_DIR}/installer-staging/bin/create-shortcut.ps1"
    ...
    VERBATIM)
```

And add them as `<File>` entries in a `bin/` Component in `Files.wxs`:

```xml
<Component Id="Files_bin_shortcut_scripts" Guid="A1B2C3D4-1111-1111-1111-000000000003">
  <File Id="File_bin_create_shortcut_ps1"
        Source="$(var.CPROJECT.StagingDir)\bin\create-shortcut.ps1" />
  <File Id="File_bin_remove_shortcut_ps1"
        Source="$(var.CPROJECT.StagingDir)\bin\remove-shortcut.ps1" />
</Component>
```

## End-to-end verification

```powershell
# Install
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i","path\to\package.msi","/quiet","/norestart" -Verb RunAs -Wait

# Verify user desktop (NOT Public)
Test-Path "$env:USERPROFILE\Desktop\CProjectStandard.lnk"  # Expect: True
Test-Path "C:\Users\Public\Desktop\CProjectStandard.lnk"    # Expect: False

# Shortcut target
(New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\CProjectStandard.lnk").TargetPath
# Expect: C:\Program Files\CProjectStandard\bin\run-wizard.bat

# Uninstall
Start-Process -FilePath "msiexec.exe" -ArgumentList "/x","path\to\package.msi","/quiet","/norestart" -Verb RunAs -Wait

# Verify cleanup
Test-Path "$env:USERPROFILE\Desktop\CProjectStandard.lnk"  # Expect: False
```