# MultiClicker

MultiClicker is a simple GUI tool for capturing multiple mouse coordinates and replaying them as a configurable click sequence.

## Compatibility

- **X11:** Full functionality (recommended).
- **Wayland:** Global click capture / automation is limited by design (Wayland security model). For full functionality, log into an **X11 session**.

## Run locally (Python)

```bash
python3 multiclicker.py
```

## Install on X11 Linux

### Dependencies

- Python 3
- Tk (tkinter)
- `xdotool`
- `pynput`

On Debian/Ubuntu:

```bash
sudo apt install -y python3 python3-tk python3-pip xdotool
python3 -m pip install --user pynput
```

### Run from the repo

```bash
python3 multiclicker.py
```

### Optional desktop entry (per-user)

```bash
install -d ~/.local/bin
install -m755 multiclicker.py ~/.local/bin/multiclicker
install -d ~/.local/share/applications ~/.local/share/icons/hicolor/scalable/apps
install -m644 multiclicker.desktop ~/.local/share/applications/multiclicker.desktop
install -m644 multiclicker.svg ~/.local/share/icons/hicolor/scalable/apps/multiclicker.svg
```

If you move the repo, update `Exec=` in `multiclicker.desktop` to point at the correct path.

## Included desktop integration files

- Desktop file: `multiclicker.desktop`
- AppStream metadata: `multiclicker.metainfo.xml`
- App icon: `multiclicker.svg`
- License: `LICENSE`

## License

MIT (see [LICENSE](LICENSE)).
