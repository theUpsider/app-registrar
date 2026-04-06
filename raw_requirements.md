## Platform & Runtime
- Target: Ubuntu with GNOME/Nautilus file manager
- Language: Python 3 (for Nautilus extension support via `python3-nautilus`)
- GUI toolkit: GTK 4 (via PyGObject / `gi.repository.Gtk`)
- Packaging: installable as a `.deb` or via a setup script that places the Nautilus extension in `~/.local/share/nautilus-python/extensions/`

## Context Menu Integration
- Register a Nautilus extension that adds a **"Register as App"** context menu item
- The item must appear only when right-clicking a **file that is executable** (`os.access(path, os.X_OK)`)
- A second menu item **"Unregister App"** should appear when the selected file already has an associated `.desktop` entry in `~/.local/share/applications/`

## Registration GUI Dialog
When "Register as App" is clicked, a GTK dialog must open with the following fields:
- **Name** (text input, required) — display name in the app menu
- **Comment** (text input, optional) — tooltip/description shown in the launcher
- **Exec** (pre-filled with the full path to the selected executable, editable)
- **Icon** (file picker, optional, accepts `.png` / `.svg`) — with a preview thumbnail
- **Categories** (dropdown or multi-select, optional) — e.g. Utility, Development, Game, etc.
- **Run in Terminal** (checkbox) — sets `Terminal=true` in the `.desktop` file
- **Startup Notify** (checkbox, default on) — sets `StartupNotify=true`
- Confirm (**Register**) and **Cancel** buttons

## `.desktop` File Generation
- On confirm, write a valid `.desktop` file to `~/.local/share/applications/<sanitized-name>.desktop`
- File must follow the [freedesktop.org Desktop Entry Spec](https://specifications.freedesktop.org/desktop-entry-spec/latest/) (Type=Application, Version=1.0, etc.)
- Run `update-desktop-database ~/.local/share/applications/` after writing to refresh the launcher index
- Show a success/error toast or dialog after the operation

## Unregistration
- When "Unregister App" is clicked, show a confirmation dialog ("Remove '[Name]' from app menu?")
- On confirm, delete the associated `.desktop` file from `~/.local/share/applications/`
- Run `update-desktop-database ~/.local/share/applications/` afterwards

## Validation
- Reject registration if **Name** is empty
- Warn (but don't block) if no icon is selected
- Validate that the `Exec` path still exists and is executable before writing
- Sanitize the `.desktop` filename (lowercase, spaces → hyphens, strip special chars)

## Installation / Uninstallation
- Provide an `install.sh` script that:
  - Installs Python dependencies (`python3-nautilus`, `python3-gi`)
  - Copies the extension to `~/.local/share/nautilus-python/extensions/`
  - Restarts Nautilus (`nautilus -q`)
- Provide an `uninstall.sh` that reverses all of the above
- Optionally: a `.deb` package or a Makefile with `make install` / `make uninstall`

## Non-Functional Requirements
- No root/sudo required — all operations in user space (`~/.local/`)
- Works on Ubuntu 22.04 LTS and 24.04 LTS
- No background daemon — extension is loaded by Nautilus on demand
- All UI strings must be translatable (i18n-ready, using `gettext`)

## Standalone App Mode

- The app must register **itself** as a launchable application during installation (its own `.desktop` entry in `~/.local/share/applications/`)
- Launching it opens a **main window** (GTK 4, `Adw.ApplicationWindow` via libadwaita preferred) independently of Nautilus
- The window must have a proper **app icon**, title bar, and GNOME HIG-compliant layout

## App Registry List View

- On launch, display a **list/grid of all `.desktop` files** managed by this app (tracked via a metadata tag, e.g. `X-RegisteredBy=nautilus-app-registrar` in each generated `.desktop` file)
- Each entry in the list shows: **app icon thumbnail**, name, exec path, categories, and registration date
- The list must support **search/filter** by name or category
- The list must handle the **empty state** gracefully (e.g., "No apps registered yet. Right-click an executable in Nautilus to get started.")

## CRUD Operations in the List

- **Create**: An "Add New" button that opens the same registration dialog used from the context menu, but with a file picker for the executable instead of pre-filling from context
- **Read**: Clicking an entry opens a **read-only detail view** with all fields displayed cleanly
- **Update (Edit)**: An edit button/action per entry that opens the registration dialog pre-filled with existing values; saving overwrites the existing `.desktop` file
- **Delete (Unregister)**: A delete button per entry with a confirmation dialog before removing the `.desktop` file and refreshing the list
- All CRUD operations must **immediately reflect** in the list without requiring a manual refresh

## UX & Interaction Polish

- Keyboard shortcut `Ctrl+N` to open the Add New dialog
- `Delete` key or `Ctrl+Backspace` to trigger delete on the selected entry
- `Ctrl+E` or `F2` to open the edit dialog for the selected entry
- Clicking the icon thumbnail in the edit form opens the file picker directly
- After any write operation, run `update-desktop-database` in the background (non-blocking subprocess)
- Undo support for delete: show a **timed snackbar/toast** ("App removed. Undo") with a 5-second window to restore the `.desktop` file before permanent deletion

## Settings Panel

- Accessible via a gear icon or hamburger menu in the header
- **Default icon**: fallback icon path/name used when no icon is specified during registration
- **Default categories**: pre-check a set of categories by default in the registration dialog
- **Default Terminal**: whether "Run in Terminal" is checked by default
- **Confirm before delete**: toggle to enable/disable the confirmation dialog on delete
- **Show system apps**: toggle to include `.desktop` files *not* created by this tool in the list view (read-only for those)
- Settings must be **persisted** to `~/.config/nautilus-app-registrar/settings.json` (no root required)
- A **"Reset to defaults"** button at the bottom of the settings panel

## Data Integrity & Edge Cases

- If the executable referenced in a registered `.desktop` file **no longer exists**, mark the entry in the list with a warning badge ("Executable not found") and offer an option to re-point it or delete the entry
- If two `.desktop` files share the same name, display both but warn the user of the conflict
- On app launch, **validate all managed entries** in the background and surface broken ones at the top of the list with a dismissible warning banner

## Window & State Management

- Remember **window size and position** between sessions (stored in settings.json)
- Support **dark mode** automatically following the system GNOME theme (`Adw.StyleManager`)
- The main window must be **responsive**: on narrow widths (<700px), collapse the detail panel into a full-screen detail view rather than a side panel
- Only **one instance** of the app may run at a time (use `Gio.Application` with a unique app ID like `io.github.yourname.AppRegistrar`)
