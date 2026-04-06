# Framework Gotchas Documentation

This folder contains comprehensive analysis of external framework gotchas relevant to the App Registrar project.

## Documents

### 1. **GOTCHAS_SUMMARY.txt** (5.8 KB) — START HERE
Executive summary with:
- Top 3 critical gotchas (will definitely cause issues)
- 7 secondary gotchas (subtle bugs)
- All 6 frameworks identified
- Quick verification checklist for agents
- Direct links to official documentation

**Use this when:** You need a 2-minute overview before debugging something that "should work"

---

### 2. **FRAMEWORK_GOTCHAS.md** (14 KB) — DETAILED REFERENCE
Comprehensive guide with:
- 10 detailed gotchas (one per section)
- Why each matters for agents
- Workflow impact analysis
- Code examples (✅ correct vs ❌ wrong)
- Reference URLs to official docs
- Summary table for quick lookup
- Testing checklist for verification

**Use this when:** 
- Implementing a specific feature (e.g., Nautilus extension, settings persistence)
- Debugging mysterious failures
- Designing test strategy
- Onboarding a new agent

---

## Quick Navigation

| Issue | Document Section | Reference |
|-------|-----------------|-----------|
| Extension not reloading | FRAMEWORK_GOTCHAS #1 | https://gnome.pages.gitlab.gnome.org/nautilus-python/nautilus-python-overview-example.html |
| FileInfo stale data | FRAMEWORK_GOTCHAS #2 | https://gnome.pages.gitlab.gnome.org/nautilus-python/nautilus-python-overview-example.html |
| Single instance broken | FRAMEWORK_GOTCHAS #3 | https://docs.gtk.org/gio/type_func.Application.get_default.html |
| CSS not loading | FRAMEWORK_GOTCHAS #4 | https://gnome.pages.gitlab.gnome.org/pygobject/tutorials/libadwaita/application.html |
| .desktop file ignored | FRAMEWORK_GOTCHAS #5 | https://xdg-specs-technobaboo-f55ac9d85e73073a0c8831695ba0fb110849811c0.pages.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html |
| App not in menu | FRAMEWORK_GOTCHAS #6 | https://github.com/TheAssassin/AppImageLauncher/issues/445 |
| Settings missing | FRAMEWORK_GOTCHAS #7, #8 | https://developer.gnome.org/documentation/tutorials/save-state.html |
| UI not responsive | FRAMEWORK_GOTCHAS #9 | https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.0/class.ApplicationWindow.html |
| MIME types not working | FRAMEWORK_GOTCHAS #10 | https://specifications.freedesktop.org/desktop-entry-spec/latest/ |

---

## Key Takeaways

### Critical Path Issues (Always Check First)
1. **Nautilus**: Must restart after every extension change
2. **FileInfo**: Use `os.access()`, never trust FileInfo permissions
3. **.desktop files**: Validate syntax, filename format critical

### Silent Failures (Hardest to Debug)
- GIO single-instance silently creates duplicates
- Config directories silently fail to create
- .desktop files silently disappear from menus
- CSS silently doesn't load
- Settings silently don't persist

### Async/Timing Issues
- `update-desktop-database` doesn't wait
- Breakpoint adaptations are delayed
- Extension reloads require full restart

---

## For Agents: Before You Debug...

```bash
# Check Nautilus extension loaded
nautilus -q && sleep 1 && nautilus &

# Validate .desktop file syntax
desktop-file-validate ~/.local/share/applications/your-app.desktop

# Verify settings file exists
cat ~/.config/nautilus-app-registrar/settings.json

# Check app instance
pgrep -f 'app-registrar' | wc -l  # Should be ≤ 1

# Verify update-desktop-database ran
update-desktop-database ~/.local/share/applications/ && sleep 1
```

---

## Documentation Sources

All references verified April 6, 2026:

- **Nautilus Python**: https://gnome.pages.gitlab.gnome.org/nautilus-python/
- **GTK 4**: https://docs.gtk.org/gtk4/
- **libadwaita**: https://gnome.pages.gitlab.gnome.org/libadwaita/
- **GIO**: https://docs.gtk.org/gio/
- **Desktop Entry Spec**: https://xdg-specs-technobaboo-f55ac9d85e73073a0c8831695ba0fb110849811c0.pages.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
- **XDG Base Directory**: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
- **GNOME Developer**: https://developer.gnome.org/

---

**Last Updated:** April 6, 2026  
**Scope:** Framework gotchas likely to cause agent mistakes  
**Audience:** AI agents and developers implementing features in App Registrar  

