# WiX Desktop Shortcut Pattern

The reason for switching from CPack/NSIS to WiX/MSI in a Windows-first C project. This is the entire short file that replaces 22 PRs of NSIS escape attempts.

## Why NSIS couldn't do this

NSIS creates desktop shortcuts via `CreateShortCut`, but the destination depends on `SetShellVarContext`:

- `current` → current user's personal desktop (`C:\Users\<user>\Desktop`)
- `all` → Public desktop (`C:\Users\Public\Desktop`)

For an admin install (which is mandatory on modern Windows for `C:\Program Files\`), the install template forces `all`, so the shortcut lands on the Public desktop — not where most users expect it. Forcing `current` requires quoting in a context where CPack mangles quotes (see `cmake-nsis-string-escaping.md`).

## DesktopFolder behavior (note after empirical verification)

In a **perMachine** MSI (`Scope="perMachine"` in `<Package>`), `StandardDirectory Id="DesktopFolder"` resolves to `C:\Users\Public\Desktop` — the All Users / Public desktop. This is standard Windows Installer behavior: per-machine packages place shortcuts where all users of the machine can see them.

In a **perUser** MSI (`Scope="perUser"`), `DesktopFolder` resolves to the installing user's personal desktop.

For projects that install to `C:\Program Files\` and therefore require perMachine scope, there are two options:

1. **Accept Public Desktop** — this is what VS Code, Node.js, Git for Windows all do. The shortcut appears on the desktop that every user of the machine sees.

2. **Use a deferred PowerShell custom action** — run after `InstallFiles`, impersonated as the installing user, calling `[Environment]::GetFolderPath('Desktop')` to resolve the current user's personal desktop path. The full pattern is in `references/wix-msi-per-user-desktop-ca.md`.

This pattern replaces 22 PRs of NSIS escape attempts with ~30 lines of WiX XML + a 4-line PowerShell script.

## Minimal `Shortcuts.wxs`

```xml
<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Fragment>
    <ComponentGroup Id="ShortcutsComponents">

      <!-- Desktop shortcut -->
      <Component Id="Shortcut_Desktop"
                 Guid="A1B2C3D4-2222-2222-2222-000000000001"
                 Directory="DesktopFolder">
        <Shortcut Id="Shortcut_Desktop_Wizard"
                  Name="CProjectStandard"
                  Description="Open the CProjectStandard setup wizard"
                  Target="[#File_bin_run_wizard]"
                  WorkingDirectory="INSTALLDIR" />
        <RemoveFolder Id="RemoveDesktopFolder"
                      Directory="DesktopFolder"
                      On="uninstall" />
        <RegistryValue Root="HKCU"
                       Key="Software\CProjectStandard"
                       Name="DesktopShortcutInstalled"
                       Type="integer"
                       Value="1"
                       KeyPath="yes" />
      </Component>

      <!-- Start Menu: Project Setup Wizard -->
      <Component Id="Shortcut_StartMenu_Wizard"
                 Guid="A1B2C3D4-2222-2222-2222-000000000002"
                 Directory="ApplicationProgramsFolder">
        <Shortcut Id="Shortcut_StartMenu_Wizard"
                  Name="Project Setup Wizard"
                  Description="Open the CProjectStandard setup wizard"
                  Target="[#File_bin_run_wizard]"
                  WorkingDirectory="INSTALLDIR" />
        <RemoveFolder Id="RemoveApplicationProgramsFolder"
                      Directory="ApplicationProgramsFolder"
                      On="uninstall" />
        <RegistryValue Root="HKCU"
                       Key="Software\CProjectStandard"
                       Name="StartMenuWizardInstalled"
                       Type="integer"
                       Value="1"
                       KeyPath="yes" />
      </Component>

      <!-- Start Menu: Template Files folder -->
      <Component Id="Shortcut_StartMenu_Template"
                 Guid="A1B2C3D4-2222-2222-2222-000000000003"
                 Directory="ApplicationProgramsFolder">
        <Shortcut Id="Shortcut_StartMenu_Template"
                  Name="Template Files"
                  Description="Open the CProjectStandard template source folder"
                  Target="INSTALLDIR" />
        <RegistryValue Root="HKCU"
                       Key="Software\CProjectStandard"
                       Name="StartMenuTemplateInstalled"
                       Type="integer"
                       Value="1"
                       KeyPath="yes" />
      </Component>

    </ComponentGroup>
  </Fragment>
</Wix>
```

## Required Product.wxs definitions

```xml
<StandardDirectory Id="DesktopFolder" />
<StandardDirectory Id="ProgramMenuFolder">
  <Directory Id="ApplicationProgramsFolder"
              Name="CProjectStandard $(var.CPROJECT.Version)" />
</StandardDirectory>
```

`ApplicationProgramsFolder` is a child of `ProgramMenuFolder` so all Start Menu entries land under a version-named folder (parallel installs of multiple versions coexist without collision).

`DesktopFolder` is referenced directly at the StandardDirectory level.

## Key conventions

- **`HKCU` for KeyPath on shortcut Components.** Shortcuts are per-user artifacts; using HKLM forces a per-machine component, which fails for non-admin contexts. HKCU also lets the uninstall run per-user.
- **`RemoveFolder On="uninstall"`.** Cleans up the version-named Start Menu folder when the last Component in it is uninstalled. Without this, an uninstall leaves an empty Start Menu folder behind.
- **`Target="[#File_bin_run_wizard]"`** is a key-path reference (bracket-hash), not a literal path. Survives the user moving the install directory and remains correct after upgrades.
- **Stable GUIDs** (`A1B2C3D4-2222-2222-2222-NNNNNNNNNNNN`). Never recycle a GUID — Windows Installer treats a Component with a new GUID as a different file, which leaves orphaned install records on upgrade.

## Uninstall registration (Apps & Features)

```xml
<Component Id="UninstallRegistry"
           Guid="A1B2C3D4-2222-2222-2222-0000000000FF"
           Directory="INSTALLDIR">
  <RegistryKey Root="HKLM"
               Key="Software\Microsoft\Windows\CurrentVersion\Uninstall\CProjectStandard">
    <RegistryValue Name="DisplayName"
                   Value="CProjectStandard $(var.CPROJECT.Version)"
                   Type="string" />
    <RegistryValue Name="Publisher"
                   Value="CProjectStandard contributors"
                   Type="string" />
    <RegistryValue Name="DisplayVersion"
                   Value="$(var.CPROJECT.Version)"
                   Type="string" />
    <RegistryValue Name="DisplayIcon"
                   Value="[INSTALLDIR]res\cproject.ico"
                   Type="string" />
  </RegistryKey>
</Component>
```

Note: `Win64="yes"` belongs on `<Package>`, not on the Component (WiX 6 removed the Component attribute).

## Reference in Feature

```xml
<Feature Id="ProductFeature" Title="CProjectStandard" Level="1" ConfigurableDirectory="INSTALLDIR">
  ...
  <ComponentGroupRef Id="ShortcutsComponents" />
  <ComponentRef Id="UninstallRegistry" />
</Feature>
```

## Validation

After install (admin install via `Start-Process -Verb RunAs`):

```powershell
# User desktop shortcut
Test-Path "$env:USERPROFILE\Desktop\CProjectStandard.lnk"
# Expect: True

# Public desktop (where NSIS used to land it)
Test-Path "C:\Users\Public\Desktop\CProjectStandard.lnk"
# Expect: False — this is the point

# Shortcut target
(New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\CProjectStandard.lnk").TargetPath
# Expect: C:\Program Files\CProjectStandard\bin\run-wizard.bat

# Start menu
Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\CProjectStandard 0.1.0\Project Setup Wizard.lnk"
# Expect: True
```

After uninstall, all four should be gone and the version-named folder removed.

## What this does NOT give you

- File-type associations. Those need `<ProgId>` and `<Extension>` Components and live in their own Fragment.
- Start Menu pinning. Windows 10+ decides this itself.
- Auto-update. Use a Burn bundle for that, not a plain MSI.