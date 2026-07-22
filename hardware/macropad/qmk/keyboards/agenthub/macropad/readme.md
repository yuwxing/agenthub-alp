# AgentHub Macropad

Physical macropad for controlling AgentHub OS.

- 12 keys (3×4) — each triggers an AgentHub agent
- MCU: Raspberry Pi Pico (RP2040)
- Communication: Raw HID (custom protocol)
- Bridge software: `bridge.py` on host PC

## Keymap

| 🎯 goal C02 | 🌐 context C19 | 💾 data C09 | 🗺️ plan C24 |
| ✨ create A01 | ▶️ execute A06 | 📊 analyze A04 | 🔍 search A03 |
| 📝 输入 | 🤖 生成 | 🚀 执行 | ⚡ 清空 |

## Pinout

| Pico pin | GPIO | Function |
|----------|------|----------|
| 4 | GP2 | Row 0 |
| 5 | GP3 | Row 1 |
| 6 | GP4 | Row 2 |
| 7 | GP5 | Col 0 |
| 8 | GP6 | Col 1 |
| 9 | GP7 | Col 2 |
| 10 | GP8 | Col 3 |

## Build

```bash
qmk compile -kb agenthub/macropad -km default
```

Hold BOOTSEL on Pico, connect USB, copy `.uf2` file to `RPI-RP2` drive.
