---
name: coding-agent-readiness
description: "Pre-flight checks before delegating to Claude Code, Codex, or OpenCode in the Docker sandbox."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Sandbox, Auth]
    related_skills: [claude-code, codex, opencode]
---

# Coding Agent Readiness — Pre-Flight Checks

Before delegating a coding task to an external CLI agent (Claude Code, Codex, OpenCode), verify the tool is actually usable in the current Docker sandbox. Users often have these tools installed and authenticated on their Windows host, but the Docker container runs a separate environment with its own auth state.

## Step 1: Check binary availability

```bash
which claude || which codex || which opencode
```

If not installed: `npm install -g @anthropic-ai/claude-code` (or equivalent).

## Step 2: Check authentication

```bash
claude auth status --text    # Claude Code
codex auth status            # Codex
```

The user saying "I just type `claude` in PowerShell/CMD" means it works on their Windows host, NOT necessarily in the Docker container. Auth is separate.

## Step 3: Decide — delegate or write directly?

| Task type | If tool is ready | If tool is NOT ready |
|-----------|-----------------|---------------------|
| Single-file script, config, or standalone program | Either works | **Write directly** with `write_file` + `terminal` (compile/run) |
| Multi-file refactor across a project | Delegate | Ask user to authenticate, or attempt `claude auth login --console` |
| PR review / code audit | Delegate (print mode `-p`) | Ask user to authenticate |
| Bug fix in a known location | Delegate | Write directly if the fix is small and well-understood |

## Pitfall: Console auth flow timeouts

`claude auth login --console` prints a URL for the user to visit in a browser, then waits for a code to be pasted back. This will timeout in automated contexts if the user isn't watching. Avoid unless you have the user's active participation.

## Docker Desktop file sharing (Windows)

When running in Docker Desktop on Windows, the host `C:\` drive is mounted at `/workspace` via 9p. Use this to deliver files to the user's actual desktop:

```bash
# Write a file to the user's Windows desktop
cp myfile.c "/workspace/Users/<username>/Desktop/"
```

Verify the mount with: `mount | grep "C:\\\\ on /workspace"`

## Reference Files

- `references/auth-failure-example.md` — Transcript of a real auth timeout in the Docker sandbox
- `references/docker-desktop-file-sharing.md` — How to deliver files to the user's Windows desktop via 9p mount
