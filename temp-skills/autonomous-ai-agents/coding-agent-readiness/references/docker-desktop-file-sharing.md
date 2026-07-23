# Docker Desktop File Sharing (Windows)

When Hermes runs inside Docker Desktop on Windows, the host `C:\` drive is accessible inside the container via 9p mounts.

## Verify the mount

```bash
mount | grep "on /workspace"
# Expected output: C:\ on /workspace type 9p (rw,noatime,dirsync,...)
```

## Write files to the Windows desktop

```bash
# The user's desktop is at:
/workspace/Users/<username>/Desktop/

# Example: save a file to the desktop
cp my_program.c "/workspace/Users/World/Desktop/"

# Create a project folder on the desktop
mkdir -p "/workspace/Users/World/Desktop/my-project"
cp *.c "/workspace/Users/World/Desktop/my-project/"
```

## Write files to any Windows path

Since `/workspace` maps to `C:\`:
- `/workspace/Users/World/Documents/` → `C:\Users\World\Documents\`
- `/workspace/Projects/my-app/` → `C:\Projects\my-app\`

## Caveats

- The user may need to press F5 in File Explorer to see new files
- If the user's Desktop is redirected (e.g., OneDrive), the actual path may differ
- Compiled Linux binaries won't run on Windows — only the source code is useful to deliver
