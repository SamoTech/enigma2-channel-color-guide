# 📺 Enigma 2 Channel Color Configuration Guide

> A complete reference for configuring channel list colors in Enigma 2 to visually distinguish **encrypted** vs. **decrypted** channels via sharing servers (OSCam / CCcam).

---

## 📁 Repository Contents

| File | Description |
|------|-------------|
| [`enigma2-channel-colors-guide.md`](./enigma2-channel-colors-guide.md) | Full walkthrough of all 5 configuration methods |
| [`enigma2-color-agent-prompt.md`](./enigma2-color-agent-prompt.md) | Reusable AI agent prompt for Enigma 2 color queries |

---

## 🎯 What This Guide Covers

- 5 methods to change channel colors — from beginner to advanced
- Exact skin XML properties (`cryptedForegroundColor`, `decryptedForegroundColor`)
- Recommended hex color codes for gold, green, and red states
- Compatibility table: OpenATV, OpenPLi, BlackHole, VTi
- Troubleshooting for common issues

---

## ⚡ Quick Start

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

MIT License — free to use, share, and modify.
