# MultiClicker

MultiClicker is a simple GUI tool for capturing multiple mouse coordinates and replaying them as a configurable click sequence.

## Compatibility

- **X11:** Full functionality (recommended).
- **Wayland:** Global click capture / automation is limited by design (Wayland security model). For full functionality, log into an **X11 session**.

## Run locally (Python)

```bash
python3 multiclicker.py
```

## Flatpak packaging

This repository includes a Flatpak manifest and metadata intended for Flathub-style packaging.

### Prerequisites

- Flatpak installed
- Flathub remote enabled
- Flatpak Builder installed

Install Builder (from Flathub):

```bash
flatpak install -y flathub org.flatpak.Builder
```

### Build a local Flatpak repo (recommended local test path)

From the project directory:

```bash
rm -rf builddir repo .flatpak-builder

flatpak run org.flatpak.Builder --force-clean   --repo=repo --install-deps-from=flathub   builddir org.multiclicker.MultiClicker.yml

flatpak build-update-repo repo
```

### Install & run from the local repo (user)

```bash
flatpak remote-delete --user multiclicker-local 2>/dev/null || true
flatpak remote-add --user --no-gpg-verify multiclicker-local file://$PWD/repo

flatpak install --user -y multiclicker-local org.multiclicker.MultiClicker
flatpak run org.multiclicker.MultiClicker
```

### Create a single-file bundle (.flatpak)

```bash
flatpak build-bundle repo multiclicker.flatpak org.multiclicker.MultiClicker master
```

Install/run the bundle:

```bash
flatpak install --user -y ./multiclicker.flatpak
flatpak run org.multiclicker.MultiClicker
```

## Included packaging files

- Flatpak manifest: `org.multiclicker.MultiClicker.yml`
- Desktop file: `org.multiclicker.MultiClicker.desktop`
- AppStream metadata: `org.multiclicker.MultiClicker.metainfo.xml`
- App icon: `org.multiclicker.MultiClicker.svg`
- License: `LICENSE`

## Flatpak permissions

The manifest is intentionally **X11-only**:

- `--socket=x11`
- `--share=ipc`

## Flathub notes / checklist

Before submitting to Flathub, verify:

- [ ] **App ID policy:** Flathub commonly expects `io.github.<user>.<repo>` for GitHub-hosted projects unless you control a matching domain/org.
- [ ] AppStream homepage/contact URLs are correct.
- [ ] Add screenshots (optional but recommended) and reference them in `metainfo.xml`.
- [ ] Ensure all downloaded sources in the manifest are pinned (stable URL + correct sha256) for reproducible builds.

## License

MIT (see [LICENSE](LICENSE)).
