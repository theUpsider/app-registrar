# Framework Gotchas for App Registrar (Nautilus Extension + GTK 4 + libadwaita)

## Overview
This project combines three major framework domains: Nautilus Python extensions, GTK 4/libadwaita UI, and XDG desktop standards. Each has subtle gotchas that can break agent-assisted development workflows.

---

## 1. NAUTILUS PYTHON EXTENSION LOADING & CACHING

### Gotcha: Extensions don't hot-reload without Nautilus restart
**Reference:** https://gnome.pages.gitlab.gnome.org/nautilus-python/nautilus-python-overview-example.html

**Why it matters for agents:** 
- Agents may modify `.py` files in `~/.local/share/nautilus-python/extensions/` and expect immediate effect
- Changes require explicit `nautilus -q` (kill + restart) to take effect
- File monitoring/watching does NOT work for extensions; the extension is only loaded at Nautilus startup

**Workflow impact:**
- Install/test loops MUST include: modify → `nautilus -q` → right-click test
- No incremental testing in running Nautilus instance
- Agents must wait for Nautilus to fully restart before testing context menu changes

**Action for agents:** 
Always kill and restart Nautilus after modifying the extension file:
```bash
nautilus -q && sleep 1 && nautilus &
```

---

## 2. NAUTILUS FILEINFO CACHING & STALE DATA

### Gotcha: `Nautilus.FileInfo` properties can return stale data without refresh
**Reference:** https://gnome.pages.gitlab.gnome.org/nautilus-python/nautilus-python-overview-example.html

**Why it matters:**
- When a file's permissions change (e.g., `chmod +x`), `FileInfo` may still report old permissions
- The extension receives `FileInfo` objects passed by Nautilus; you don't control refresh timing
- Rapid permission changes (write .desktop → delete → recreate) can cause state sync issues

**Workflow impact:**
- Validation checks (`os.access(path, os.X_OK)`) on the filesystem are MORE reliable than `FileInfo` queries
- Agents should NOT trust FileInfo properties in multi-step operations
- Always re-stat the filesystem directly for critical checks (executable, exists)

**Action for agents:**
```python
# ❌ WRONG - relies on Nautilus cache
is_exec = file.is_executable()

# ✅ RIGHT - re-stat from filesystem
is_exec = os.access(file.get_location().get_path(), os.X_OK)
```

---

## 3. GIO.APPLICATION SINGLE INSTANCE & D-BUS REQUIREMENTS

### Gotcha: `Gio.Application` single-instance enforcement requires proper flags + D-Bus naming
**Reference:** https://docs.gtk.org/gio/type_func.Application.get_default.html | https://discourse.gnome.org/t/gio-single-instance-logic/27005

**Why it matters:**
- Setting `Gio.ApplicationFlags.DEFAULT_FLAGS` or `NON_UNIQUE` changes whether multiple instances are allowed
- The app ID MUST follow reverse-DNS format (`io.github.user.AppRegistrar`) for D-Bus
- If D-Bus name doesn't match, single-instance enforcement silently fails → duplicate windows possible
- `Gio.Application.get_default()` returns the PRIMARY instance only; in multi-instance mode, returns None or first instance

**Workflow impact:**
- Agents may not realize duplicate instances are running if they don't check flags
- Window state can be lost if instances aren't properly deduplicated
- App launch from `.desktop` file may spawn new instance instead of activating existing

**Action for agents:**
```python
# ✅ Enforce single instance
app = Adw.Application(application_id='io.github.yourname.AppRegistrar',
                      flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
# DO NOT use: Gio.ApplicationFlags.NON_UNIQUE

# Check instance count before launching
if Gio.Application.get_default() is not None:
    print("App already running")
```

---

## 4. ADW.APPLICATION STYLESHEET & RESOURCE LOADING

### Gotcha: libadwaita stylesheets loaded ONLY if using `Gio.Resource` correctly
**Reference:** https://gnome.pages.gitlab.gnome.org/pygobject/tutorials/libadwaita/application.html

**Why it matters:**
- `Adw.Application` auto-loads stylesheets from app resource paths
- If resources are NOT registered via `Gio.Resource`, custom CSS is silently ignored
- Dark mode detection works automatically via `Adw.StyleManager`, but CSS theming breaks if resources aren't bundled

**Workflow impact:**
- UI may look wrong (missing theme) without clear error message
- Agents may spend time debugging logic when the issue is missing CSS resource
- Build/packaging steps MUST include resource compilation

**Action for agents:**
- For development (no packaging), manually load CSS:
```python
provider = Gtk.CssProvider()
provider.load_from_path("style.css")
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)
```

---

## 5. DESKTOP ENTRY SPECIFICATION: STRICT PARSING & INVALID SYNTAX

### Gotcha: `.desktop` files must follow exact Desktop Entry Spec 1.5 format
**Reference:** https://xdg-specs-technobaboo-f55ac9d85e73073a0c8831695ba0fb110849811c0.pages.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html

**Why it matters:**
- Filenames must be valid D-Bus names: `[A-Za-z0-9-_]` only, no spaces (use hyphens)
- Keys are case-sensitive (`Name` ≠ `name`)
- Required fields for `Type=Application`: `Type`, `Name`, `Version`, `Exec` (if not DBusActivatable)
- Semicolon-delimited values must end with `;` (trailing semicolon required for lists)
- Escaping rules: `\n` (newline), `\t` (tab), `\s` (space), `\\` (backslash), `\;` (semicolon)
- Comments must start with `#` at line beginning; inline comments are NOT valid

**Workflow impact:**
- Malformed `.desktop` files won't appear in app launchers without error message
- Agents may create syntactically invalid files that won't parse
- Desktop database (`update-desktop-database`) will silently ignore bad entries

**Action for agents:**
```python
# ✅ CORRECT
Name=My App Registrar
Exec=/home/user/bin/app-registrar
Categories=Utility;System;
Version=1.0

# ❌ WRONG - missing trailing semicolon, inline comment
Categories=Utility;System # This is invalid
Version = 1.0  # Spaces around = are stripped

# ✅ CORRECT filename
io.github.user.AppRegistrar.desktop

# ❌ WRONG - spaces, uppercase extension
io.github.user.app registrar.DESKTOP
```

---

## 6. UPDATE-DESKTOP-DATABASE: ASYNC SUBPROCESS TIMING

### Gotcha: `update-desktop-database` must complete before app launchers see new entries
**Reference:** https://github.com/TheAssassin/AppImageLauncher/issues/445

**Why it matters:**
- Running `update-desktop-database ~/.local/share/applications/` is NOT instantaneous
- Background subprocess completion isn't guaranteed before app queries the database
- File descriptor issues can cause subprocess to hang if not properly detached
- GNOME application cache may be stale even after `update-desktop-database` finishes

**Workflow impact:**
- Agents may create `.desktop` file, run update-db in background, then immediately test app launcher
- App won't appear until: (1) update-db finishes, (2) launcher cache refreshes (sometimes requires wait)
- Race condition: new entry created → update-db starts → cache still shows old list

**Action for agents:**
```python
import subprocess
import time

# ✅ Run update-desktop-database synchronously
subprocess.run([
    'update-desktop-database',
    os.path.expanduser('~/.local/share/applications/')
], check=True)
time.sleep(0.5)  # Allow cache flush

# ❌ WRONG - doesn't wait
subprocess.Popen(['update-desktop-database', ...])  # Returns immediately
```

---

## 7. XDG_CONFIG_HOME & JSON PERSISTENCE: DIRECTORY CREATION

### Gotcha: `~/.config/nautilus-app-registrar/` may not exist; must create with proper permissions
**Reference:** https://developer.gnome.org/documentation/tutorials/save-state.html

**Why it matters:**
- XDG spec says configs go in `$XDG_CONFIG_HOME` (default `~/.config`)
- Directory MUST be created manually; `json.dump()` to non-existent parent fails silently
- Parent directory permissions affect write ability
- No automatic directory creation in GTK/GLib for user-space configs

**Workflow impact:**
- Agents may assume `~/.config/app-id/` exists without creating it
- Settings persistence fails silently if directory doesn't exist
- First run creates no config file, second run still fails

**Action for agents:**
```python
import os
import json

config_dir = os.path.expanduser('~/.config/nautilus-app-registrar')
os.makedirs(config_dir, exist_ok=True, mode=0o700)

config_file = os.path.join(config_dir, 'settings.json')
with open(config_file, 'w') as f:
    json.dump(settings, f)
```

---

## 8. GTK.APPLICATIONWINDOW STATE PERSISTENCE: GIO.SETTINGS vs. FILE

### Gotcha: GSettings requires schema file installation; raw JSON is simpler for uninstalled apps
**Reference:** https://developer.gnome.org/documentation/tutorials/save-state.html

**Why it matters:**
- GSettings (`Gio.Settings`) requires `.gschema.xml` compiled at system level
- For uninstalled dev code, GSettings will fail unless schema is registered
- Recommended approach for apps with custom configs: use JSON file in `$XDG_CONFIG_HOME`
- GSettings is better for window geometry (automatic binding), but overkill for custom app settings

**Workflow impact:**
- Agents building a dynamic-config app may try GSettings, find schema missing, settings fail
- Recommended: Use `json` module for settings persistence (simpler, no schema needed)
- Window geometry SHOULD use GSettings IF app is installed; otherwise use JSON

**Action for agents:**
```python
# ✅ For installed app with schema: use GSettings
# ✅ For dev/uninstalled app: use JSON

import json
import os

def load_settings():
    config_file = os.path.expanduser('~/.config/app-id/settings.json')
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings(settings):
    config_file = os.path.expanduser('~/.config/app-id/settings.json')
    os.makedirs(os.path.dirname(config_file), exist_ok=True, mode=0o700)
    with open(config_file, 'w') as f:
        json.dump(settings, f)
```

---

## 9. GTK 4 RESPONSIVE LAYOUT & ADAPTIVE BREAKPOINTS

### Gotcha: `Adw.Breakpoint` triggers resize AFTER window layout; not during
**Reference:** https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.0/class.ApplicationWindow.html

**Why it matters:**
- Breakpoints are reactive, not predictive
- Layout doesn't adapt until window width crosses threshold
- Agents may set breakpoint at 700px, then resize window to 600px expecting immediate collapse → delay possible
- Current breakpoint is queryable via `get_current_breakpoint()`, but state is asynchronous

**Workflow impact:**
- Agents designing responsive UI must test actual resizing, not just set breakpoints
- Content may flicker during transition if not properly managed
- Detail panel collapse at narrow widths requires manual testing (can't be unit-tested easily)

**Action for agents:**
- Always test resize behavior interactively
- Define minimum window size appropriately:
```python
window.set_default_size(800, 600)  # Min usable size
```

---

## 10. FREEDESKTOP MIME TYPE DATABASE: CHANGES NOT IMMEDIATE

### Gotcha: Adding `.desktop` entries with new `MimeType=` requires `update-mime-database` AND launcher refresh
**Reference:** https://specifications.freedesktop.org/desktop-entry-spec/latest/

**Why it matters:**
- Updating `.desktop` file with new `MimeType=` requires TWO updates:
  1. `update-desktop-database` (for launcher)
  2. `update-mime-database` (for MIME association)
- File manager may cache MIME type → file icon association
- Changes not reflected in app chooser dialogs until cache flushes

**Workflow impact:**
- Agents adding MIME types to existing `.desktop` file must run BOTH utilities
- Just updating `.desktop` won't change file type associations in file manager
- Test requires file manager restart or cache clear

**Action for agents:**
```python
import subprocess

subprocess.run(['update-desktop-database', app_dir], check=True)
subprocess.run(['update-mime-database', app_dir], check=True)
```

---

## Summary Table: Quick Reference

| Framework | Gotcha | Fix/Workaround | Risk |
|-----------|--------|---|------|
| **Nautilus Python** | No hot-reload | `nautilus -q` after changes | Agent assumes instant reload |
| **Nautilus** | FileInfo caching | Use `os.access()`, not FileInfo | Stale permission checks |
| **Gio.Application** | Single-instance broken silently | Match app ID to D-Bus name | Duplicate windows |
| **libadwaita** | Stylesheet ignored if no resources | Manual CSS load for dev | UI looks unstyled |
| **.desktop files** | Syntax errors → silent ignore | Validate with desktop-file-validate | Agent creates invalid files |
| **update-desktop-database** | Async, can miss updates | Run synchronously, add delay | Settings not visible immediately |
| **XDG config** | Directory not auto-created | `os.makedirs(..., exist_ok=True)` | Settings persist fails silently |
| **GSettings** | Requires schema installation | Use JSON for dev, GSettings for installed | Config fails without schema |
| **GTK 4 breakpoints** | Layout delayed, not predictive | Test interactively | Agent assumes instant adapt |
| **MIME database** | Separate cache from desktop DB | Run both update tools | File type associations fail |

---

## For Agents: Testing Checklist

Before assuming a feature works:

- [ ] **Nautilus extension change:** Kill + restart Nautilus
- [ ] **Permission check:** Use `os.access()`, not FileInfo
- [ ] **App launch:** Verify single instance with `pgrep` or window manager
- [ ] **Settings save:** Check `~/.config/app-id/settings.json` file exists
- [ ] **`.desktop` file:** Validate with `desktop-file-validate`
- [ ] **App appears in menu:** Wait after `update-desktop-database`, then restart launcher
- [ ] **Responsive UI:** Manually resize window, verify layout adapts
- [ ] **Dark mode:** Check `Adw.StyleManager` follows system theme

