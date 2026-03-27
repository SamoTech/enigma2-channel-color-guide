# 📺 Enigma 2 Channel Color Configuration Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Enigma2-blue.svg)](https://github.com/E2OpenPlugins)
[![Images](https://img.shields.io/badge/Images-OpenATV%20%7C%20OpenPLi%20%7C%20BlackHole-green.svg)](#)
[![Servers](https://img.shields.io/badge/Servers-OSCam%20%7C%20CCcam-orange.svg)](#)
[![Plugin](https://img.shields.io/badge/Plugin-Python%203-lightblue.svg)](./plugin/)
[![GitHub Stars](https://img.shields.io/github/stars/SamoTech/enigma2-channel-color-guide?style=social)](https://github.com/SamoTech/enigma2-channel-color-guide)

> A complete reference **and installable plugin** for configuring channel list colors in Enigma 2 to visually distinguish **encrypted** vs. **decrypted** channels via sharing servers (OSCam / CCcam).

---

## 🚀 One-Line Install

Run this directly on your Enigma 2 receiver via **Telnet or SSH**:

```sh
wget -qO- https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh | sh
```

Or with `curl`:

```sh
curl -fsSL https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh | sh
```

> ✅ The script will download all plugin files, set permissions, and restart the GUI automatically.

### Uninstall

```sh
wget -qO- https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/uninstall.sh | sh
```

---

## 📁 Repository Contents

| Path | Description |
|------|-------------|
| [`install.sh`](./install.sh) | One-line installer script |
| [`uninstall.sh`](./uninstall.sh) | Clean uninstaller script |
| [`plugin/`](./plugin/) | Installable Enigma 2 plugin source code |
| [`enigma2-channel-colors-guide.md`](./enigma2-channel-colors-guide.md) | Full walkthrough of all 5 configuration methods |
| [`enigma2-color-agent-prompt.md`](./enigma2-color-agent-prompt.md) | Reusable AI agent prompt for Enigma 2 color queries |
| [`LICENSE`](./LICENSE) | MIT License |

---

## 🎯 What This Guide Covers

- 5 methods to change channel colors — from beginner to advanced
- Exact skin XML properties (`cryptedForegroundColor`, `decryptedForegroundColor`)
- Recommended hex color codes for gold, green, and red states
- Compatibility table: OpenATV, OpenPLi, BlackHole, VTi
- Troubleshooting for common issues
- **Installable plugin** with GUI settings screen

---

## ⚡ Quick Start (Manual)

### Beginner (2-3 min)
```
Menu → Setup → User Interface → Channel Selection
→ Color of crypto channels: #FF0000
→ Color of decrypted channels: #FFD700
```

### Advanced — skin.xml edit
```xml
<widget name="ServiceList"
  cryptedForegroundColor="#FF0000"
  decryptedForegroundColor="#FFD700"
  foregroundColor="#FFFFFF" />
```
**File path:** `/usr/share/enigma2/[skin_name]/skin.xml`

---

## 🎨 Color Reference

| Color | Hex Code | Suggested Use |
|-------|----------|---------------|
| 🟡 Gold | `#FFD700` | Decrypted channels |
| 🟢 Green | `#00FF00` | Active/working channels |
| 🔴 Red | `#FF0000` | Encrypted/locked channels |
| ⚪ White | `#FFFFFF` | Free-to-air channels |

---

## 🛠 Requirements

- ✅ Enigma 2 receiver
- ✅ Modern image (OpenATV / OpenPLi / BlackHole)
- ✅ Active sharing server (OSCam / CCcam)
- ✅ Settings backup before editing

---

## 📜 License

[MIT License](./LICENSE) — Copyright © 2026 [Ossama Hashim](https://github.com/SamoTech)
