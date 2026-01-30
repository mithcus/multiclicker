# MultiClicker

MultiClicker is a simple GUI tool for capturing multiple mouse coordinates and replaying them
as a configurable click sequence.

## Run locally

```bash
python3 multiclicker.py
```

## Flatpak (Flathub) packaging

This repository includes a Flatpak manifest and metadata aimed at Flathub submission.
X11-only support is intentional; Wayland is not enabled.

### Build & run (local Flatpak test)

```bash
flatpak-builder --force-clean --user build-dir org.multiclicker.MultiClicker.yml
flatpak-builder --run build-dir org.multiclicker.MultiClicker.yml multiclicker
```

### Included metadata

- Flatpak manifest: `org.multiclicker.MultiClicker.yml`
- Desktop file: `org.multiclicker.MultiClicker.desktop`
- AppStream metadata: `org.multiclicker.MultiClicker.metainfo.xml`
- App icon: `org.multiclicker.MultiClicker.svg`
- License: `LICENSE` (MIT)

### Flathub submission checklist (verified here)

- [x] App ID uses reverse-DNS format (`org.multiclicker.MultiClicker`).
- [x] Desktop file and AppStream metadata IDs match the App ID.
- [x] Metadata includes summary, description, license, categories, keywords, and content rating.
- [x] Icon is provided in scalable SVG format.
- [x] License file is included at the repository root.
- [x] X11-only permissions configured (`--socket=x11`), Wayland not enabled.
- [x] Dependencies are bundled (xdotool + Python dependency `pynput`).

### Items to verify before publishing

- [ ] Replace the AppStream homepage URL with the real project URL.
- [ ] Consider adding screenshots to AppStream metadata for Flathub listing.
- [ ] Confirm the icon and summary match your branding expectations.
