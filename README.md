# Enigma2 Channel Colors Plugin

![Enigma2 Channel Color Guide](docs/assets/banner.svg)

> Colorize your Enigma2 channel list by encryption state — instantly see which channels are **FTA**, **decryptable via NCam**, **encrypted**, or have **no signal**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Enigma2-green.svg)
![Tested](https://img.shields.io/badge/tested-OpenATV%207.6-brightgreen.svg)

## Color Guide

| Color | State | Condition |
|-------|-------|-----------|
| ⬜ White `#FFFFFF` | Free-to-Air (FTA) | `isCrypted = False` |
| 🟢 Green `#00C800` | Decryptable via NCam | `isCrypted = True` + CAID found in NCam |
| 🔴 Red `#FF3232` | Encrypted (no key) | `isCrypted = True` + CAID not in NCam |
| ⚫ Gray `#888888` | No Signal | Service not available |

All colors configurable via **Menu → Plugins → Channel Colors**.

---

## Compatibility

| Image | Status |
|-------|--------|
| OpenATV 7.x | ✅ Tested & Working |
| OpenPLi 9.x | ✅ Compatible |
| BlackHole 3.x | ⚠️ Untested |
| VTi 14.x | ⚠️ Untested |

---

## Install

```sh
wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh
```

> Automatically detects your image path (live or ImageBoot), downloads plugin files,
> patches the skin, and restarts enigma2.

### ⚠️ Required Skin Patch

If your skin has `foregroundColor="white"` hardcoded in the channel list widget
(e.g. **Fury-FHD**), colors will not show without this patch.
`install.sh` applies it automatically. To apply manually:

```sh
# Replace Fury-FHD with your skin folder name
SKIN="/usr/share/enigma2/Fury-FHD/skin.xml"
cp "$SKIN" "$SKIN.bak"

python3 << 'EOF'
path = '/usr/share/enigma2/Fury-FHD/skin.xml'
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

```sh
wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/uninstall.sh -O - | sh
```

> Removes the plugin and automatically restores the skin backup.

---

## Restore Skin Backup

```sh
wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/restore.sh -O - | sh
```

> Lists available backups and lets you pick which one to restore.
> The backup `skin.xml.bak` is created automatically by `install.sh`.

---

## Configuration

Go to **Menu → Plugins → Channel Colors**:

| Setting | Default | Description |
|---------|---------|-------------|
| Plugin Enabled | Yes | Enable/disable without uninstalling |
| Encrypted Color (Red) | `#FF3232` | Encrypted channels with no NCam key |
| NCam Decryptable Color (Green) | `#00C800` | Encrypted but openable via NCam |
| Free-to-Air Color (White) | `#FFFFFF` | Channels with no encryption |

> 💛 **Yellow button** in settings → **Reload NCam** — forces re-read of `ncam.list`
> without restarting enigma2 (useful after changing NCam server).

**Color format:** `#RRGGBB` hex — e.g. `#FF0000` = red, `#00FF00` = bright green.

---

## NCam Integration

The plugin reads `/etc/ncam/ncam.list` (or `/var/etc/ncam/ncam.list`) at startup
and caches all available CAIDs. For each encrypted channel it checks
`getInfoList(sCAIDs)` against the NCam CAID cache:

- **Match found** → channel is colored **Green** (decryptable)
- **No match** → channel stays **Red** (no key available)

If `ncam.list` is not found, all encrypted channels fall back to **Red**.

---

## Debug

```sh
# View plugin log
cat /tmp/cc_debug.log

# Watch in real-time
tail -f /tmp/cc_debug.log
```

Expected healthy output:
```
[ChannelColors] start
[ChannelColors] NCam CAIDs loaded from /etc/ncam/ncam.list: 47 entries
[ChannelColors] patched OK
[ChannelColors] FTA=120 DEC=430 ENC=160
```

---

## How It Works

- Hooks into `ChannelSelectionBase.__init__` at enigma2 startup
- Reads NCam CAID list from `ncam.list` and caches it
- Uses `eServiceCenter.info().isCrypted()` to detect FTA vs encrypted
- For encrypted channels, calls `getInfoList(sCAIDs)` and checks against NCam cache
- Sets `eListbox.setForegroundColor(red)` as base for all rows
- Marks FTA + NCam-decryptable channels with `addMarked()` → colored green/white
- Patches `applySkin()` to survive skin re-applies on screen transitions
- Does **not** call `setRoot()` — avoids cursor jumping to first channel

## Technical Notes

### `setColor(slot, color)` — Correct API

```python
l.setColor(l.markedForeground, parseColor("#00C800"))   # correct
l.setColor(0, parseColor("#00C800"))                    # WRONG
```

Slot constants are integer properties on the `eListboxServiceContent` object itself.

### Why No `setRoot()`

Calling `setRoot()` reloads the service list and resets the cursor to the first
channel. `ServiceListLegacy` has no `moveToService()` method to restore position.
The fix: skip `setRoot()` entirely — enigma2 already loaded the list, we only
need to apply colors on top.

### Skin `foregroundColor="white"` Override

Many skins hardcode `foregroundColor="white"` on the service list widget.
This overrides all `setColor()` content slots. Must be removed from `skin.xml`.

---

## License

MIT © [Ossama Hashim (SamoTech)](https://github.com/SamoTech)
