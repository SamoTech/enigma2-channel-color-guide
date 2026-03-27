# 🔌 Channel Colors Plugin — Installation & Usage

## Overview

This Enigma 2 plugin adds a **GUI settings screen** that lets you configure the channel list colors for:

- 🔴 **Encrypted** channels (locked, no active card/server)
- 🟡 **Decrypted** channels (unlocked via OSCam / CCcam sharing server)
- ⚪ **Free-to-Air** channels (no encryption)

---

## File Structure

```
plugin/
├── __init__.py              # Package init
├── plugin.py                # Plugin entry point & descriptor
├── ChannelColorsSetup.py    # GUI settings screen
├── ColorApplier.py          # Runtime color logic
├── icon.png                 # Plugin icon (48x48)
└── README.md                # This file
```

---

## Installation

### Method 1 — FTP (Recommended)

1. Connect to your receiver via FTP (FileZilla, etc.)
2. Navigate to `/usr/lib/enigma2/python/Plugins/Extensions/`
3. Create folder `ChannelColors`
4. Upload all files from this `plugin/` directory into it
5. Restart Enigma 2 GUI (`telnet` → `init 4 && init 3`)

### Method 2 — Telnet / SSH

```bash
# On your receiver:
mkdir -p /usr/lib/enigma2/python/Plugins/Extensions/ChannelColors
# Then SCP files:
scp plugin/* root@[RECEIVER_IP]:/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors/
init 4 && init 3
```

---

## Usage

1. After installation, go to **Menu → Plugins**
2. Open **Channel Colors**
3. Set your preferred colors using the color picker
4. Press **Green (Save)**
5. The colors apply immediately to the channel list

---

## Default Colors

| State | Default Color | Hex |
|-------|--------------|-----|
| Encrypted | 🔴 Red | `#FF0000` |
| Decrypted | 🟡 Gold | `#FFD700` |
| Free-to-Air | ⚪ White | `#FFFFFF` |

---

## Compatibility

| Image | Status |
|-------|--------|
| OpenATV 7.0+ | ✅ Fully supported |
| OpenPLi 9.0+ | ✅ Fully supported |
| BlackHole 3.1+ | ✅ Supported |
| VTi 14.0+ | ⚠️ Partial (test recommended) |

---

## Troubleshooting

**Colors not showing?**
→ Restart GUI: `init 4 && init 3`

**Plugin not in menu?**
→ Check folder name is exactly `ChannelColors` (case-sensitive)

**Import errors in log?**
→ Verify you're on Python 3 image (OpenATV 7+ / OpenPLi 9+)
