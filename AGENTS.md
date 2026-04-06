# AGENTS.md

## Current repo reality (read this first)
- This repository is currently **spec-first**: no app source code, no build/test config, no CI workflows, no package manifests.
- The only canonical product spec is `raw_requirements.md`.
- Before running any command, verify whether required files actually exist; do not assume a Python package, `install.sh`, or tests are present yet.

## Primary source of truth
- `raw_requirements.md` defines required behavior, runtime paths, and install/uninstall expectations.
- If any future docs conflict with executable scripts/config, prefer executable config.

## Required runtime paths from spec
- Nautilus extension target: `~/.local/share/nautilus-python/extensions/`
- Generated launcher files: `~/.local/share/applications/<sanitized-name>.desktop`
- App settings file: `~/.config/nautilus-app-registrar/settings.json`

## Command-level facts already defined by spec
- After writing or deleting `.desktop` files, run:
  - `update-desktop-database ~/.local/share/applications/`
- Install flow is expected to include:
  - dependencies: `python3-nautilus`, `python3-gi`
  - Nautilus restart: `nautilus -q`
- `install.sh` / `uninstall.sh` are required by spec but are not implemented in repo yet.

## Implementation boundaries agents should respect
- All operations are user-space only (`~/.local`, `~/.config`), no root-required runtime behavior.
- Feature scope includes two surfaces:
  1. Nautilus context-menu extension (`Register as App` / `Unregister App`)
  2. Standalone GTK/libadwaita app with CRUD over managed `.desktop` files
- Managed desktop entries should be tracked with metadata key `X-RegisteredBy=nautilus-app-registrar`.

## Practical workflow for future sessions
1. Start from `raw_requirements.md` and map each requirement to concrete files to create.
2. Scaffold missing executable sources first (extension module, standalone app module, install/uninstall scripts).
3. Implement `.desktop` write/delete logic and settings persistence exactly at the specified paths.
4. Verify launcher refresh via `update-desktop-database` after each write/delete path.

## Additional research notes (non-canonical)
- `README_GOTCHAS.md`, `FRAMEWORK_GOTCHAS.md`, and `GOTCHAS_SUMMARY.txt` contain external-framework gotcha notes gathered during analysis.
- Treat them as supplemental guidance; `raw_requirements.md` remains the canonical local spec.
