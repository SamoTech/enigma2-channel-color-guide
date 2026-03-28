# Enigma2 Channel Colors Plugin

> Colorize your Enigma2 channel list by encryption state — instantly see which channels are **FTA**, **encrypted**, or have **no signal**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Enigma2-green.svg)
![Tested](https://img.shields.io/badge/tested-OpenATV%207.6-brightgreen.svg)

## Visual Result

| Color | State |
|-------|-------|
| 🟢 Green `#00C800` | Free-to-Air (FTA) |
| 🔴 Red `#FF3232` | Encrypted |
| ⚫ Gray `#888888` | No Signal |

All colors are fully configurable via **Menu → Plugins → Channel Colors**.

---

## Compatibility

| Image | Status |
|-------|--------|
| OpenATV 7.x | ✅ Tested & Working |
| OpenPLi 9.x | ✅ Compatible |
| BlackHole 3.x | ⚠️ Untested |
| VTi 14.x | ⚠️ Untested |

---

## Installation

### Quick Install (Recommended)

```bash
cd /tmp
wget https://github.com/SamoTech/enigma2-channel-color-guide/archive/main.tar.gz
tar xzf main.tar.gz
cd enigma2-channel-color-guide-main
bash install.sh
killall -9 enigma2
```

> `install.sh` automatically detects your image path (live or ImageBoot),
> copies plugin files, patches the skin, and fixes any saved white FTA color.

### Manual Install

```bash
# For live image
BASE=""

# For ImageBoot (adjust version as needed)
BASE="/media/hdd/ImageBoot/openatv-7.6"

DEST="$BASE/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
mkdir -p "$DEST"
cp plugin/*.py "$DEST/"
killall -9 enigma2
```

### ⚠️ Required Skin Patch

If your skin has `foregroundColor="white"` hardcoded in the channel list widget
(e.g. **Fury-FHD**, and many others), colors will not show without this patch.
`install.sh` does it automatically. To apply manually:

```bash
# Replace YOUR_SKIN with your skin folder name, e.g. Fury-FHD
SKIN="/usr/share/enigma2/YOUR_SKIN/skin.xml"

# Backup first
cp "$SKIN" "$SKIN.bak"

# Apply patch
python3 << 'EOF'
path = '/usr/share/enigma2/YOUR_SKIN/skin.xml'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()
old = 'foregroundColor="white" foregroundColorSelected="#ffffff"'
new = 'foregroundColorSelected="#ffffff"'
if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Skin patched OK')
else:
    print('Pattern not found - check your skin manually')
EOF
```

---

## Uninstall

```bash
# Using script (auto-detects path and restores skin backup)
bash uninstall.sh
killall -9 enigma2
```

### Manual Uninstall

```bash
# For live image
BASE=""
# For ImageBoot
BASE="/media/hdd/ImageBoot/openatv-7.6"

# Remove plugin
rm -rf "$BASE/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"

# Restore skin backup (if patched)
SKIN="$BASE/usr/share/enigma2/YOUR_SKIN/skin.xml"
cp "$SKIN.bak" "$SKIN"

# Restart
killall -9 enigma2
```

---

## Restore Skin Backup

If anything looks wrong with the skin after patching, restore the original:

```bash
# Auto restore using script
bash restore.sh

# OR manually
SKIN="/usr/share/enigma2/YOUR_SKIN/skin.xml"
cp "$SKIN.bak" "$SKIN"
killall -9 enigma2
```

> The backup is saved as `skin.xml.bak` in the same skin folder.
> Always created automatically by `install.sh` before any changes.

---

## Configuration

Go to **Menu → Plugins → Channel Colors** to change colors:

| Setting | Default | Description |
|---------|---------|-------------|
| Plugin Enabled | Yes | Enable/disable without uninstalling |
| Encrypted Channel Color | `#FF3232` | Channels with CA/encryption |
| Decrypted Channel Color | `#FFD700` | Reserved for future NCam integration |
| Free-to-Air Channel Color | `#00C800` | Channels with no encryption |

**Color format:** `#RRGGBB` hex — e.g. `#FF0000` = red, `#00FF00` = bright green.

---

## Debug

```bash
# View live plugin log
cat /tmp/cc_debug.log

# Watch in real-time
tail -f /tmp/cc_debug.log
```

Expected healthy log output:
```
[ChannelColors] start
[ChannelColors] patched OK
[ChannelColors] mark error: ...   <- only on first load before list is ready
[ChannelColors] FTA=347 ENC=590   <- correct counts on channel list open
[ChannelColors] apply done
```

---

## How It Works

- Hooks into `ChannelSelectionBase.__init__` at enigma2 startup
- Uses `eServiceCenter.info().isCrypted()` to detect FTA vs encrypted (reads lamedb)
- Sets `eListbox.setForegroundColor(enc_col)` as base color for all rows
- Marks FTA channels with `addMarked()` → `markedForeground` colors them green
- Patches `applySkin()` to survive every `setRoot()` skin re-apply
- Works around skin's hardcoded `foregroundColor="white"` override

## Technical Notes

### `setColor(slot, color)` — Correct API

The correct API is `l.setColor(l.slotName, color)` **not** `l.setColor(index, color)`.
Slot constants are integer properties on the `eListboxServiceContent` object itself:

```python
l.setColor(l.markedForeground, parseColor("#00C800"))   # correct
l.setColor(0, parseColor("#00C800"))                    # WRONG
```

### Skin `foregroundColor="white"` Override

Many skins hardcode `foregroundColor="white"` on the service list widget.
This overrides all `setColor()` content slots. Solution: remove it from `skin.xml`
and use `eListbox.setForegroundColor()` directly on the widget instead.

### `applySkin` Hook

`setRoot()` triggers `applySkin()` which resets the listbox foreground back to
the skin's color. Patching `sl.applySkin` to reapply our colors after every call
survives this reset permanently.

---

## License

MIT © [Ossama Hashim (SamoTech)](https://github.com/SamoTech)
