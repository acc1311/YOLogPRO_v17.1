# 📻 YO Log PRO v17.1 — Full Edition

**Logger Profesional Multi-Concurs pentru Radioamatori**  
**Professional Multi-Contest Amateur Radio Logger**

Dezvoltat de / Developed by: **Ardei Constantin-Cătălin (YO8ACR)**  
📧 yo8acr@gmail.com

[![Build](https://github.com/acc1311/YOLogPRO_v17.1/actions/workflows/build.yml/badge.svg)](https://github.com/acc1311/YOLogPRO_v17.1/actions/workflows/build.yml)
![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%207%2B%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-Free%20Ham%20Radio-green)

---

> 📖 **[Manual de utilizare — Română](docs/MANUAL_RO.md)** &nbsp;|&nbsp; **[User Manual — English](docs/MANUAL_EN.md)**

---

## 🚀 Descărcare rapidă / Quick Download

| Fișier | Descriere |
|---|---|
| **[⬇ YOLogPRO_v17.1.exe](https://github.com/acc1311/YOLogPRO_v17.1/releases/latest)** | Executabil Windows — fără instalare |
| **[yo_log_pro_v171.py](yo_log_pro_v171.py)** | Sursă Python — cross-platform |

---

## ✨ Funcționalități / Features

| Modul | RO | EN |
|---|---|---|
| 📝 **Log Editor** | Editor dedicat cu filtrare, undo, context menu | Standalone editor with filter, undo, right-click |
| 🌐 **Callbook** | Căutare radioamator.ro + QRZ.com | Search radioamator.ro + QRZ.com |
| 📡 **Band Map** | Hartă vizuală benzi cu activitate live | Visual band activity map, live |
| 🌍 **DXCC / cty.dat** | Bază de date internă + suport BigCTY | Built-in DB + BigCTY external support |
| 📊 **Scor Live** | Panou scor contest: QSO, mults, DXCC | Live contest score: QSO, mults, DXCC |
| 🔊 **Alert Mult** | Beep + flash la multiplicator nou | Beep + flash on new multiplier |
| 📡 **DX Cluster** | Client telnet GUI, filtrare, click-to-log | Telnet cluster GUI, filter, click-to-log |
| 📈 **Rate Stats** | Grafic QSO/h pe 24h, top DXCC, per bandă | QSO/h chart 24h, top DXCC, per band |
| 📻 **CAT Radio** | Yaesu / Icom / Kenwood / Elecraft / Hamlib | Full bidirectional CAT control |
| 🎨 **Teme** | 6 teme de culori + editor personalizat | 6 colour themes + custom editor |
| 🏆 **Concursuri** | 7 preconfigurate + editor nelimitat | 7 built-in + unlimited custom contests |
| 🪟 **Win 7** | Compatibil Windows 7 SP1 x86/x64 | Compatible with Windows 7 SP1 x86/x64 |

---

## 📋 Formate / Formats

**Export:** Cabrillo 2.0 · ADIF 3.1 · EDI · CSV · TXT  
**Import:** Cabrillo 2.0/3.0 · ADIF · CSV

---

## ⌨️ Scurtături / Shortcuts

| Tastă | Funcție |
|---|---|
| `Enter` | Log QSO |
| `Ctrl+S` | Salvare / Save |
| `Ctrl+Z` | Undo |
| `Ctrl+F` | Căutare / Search |
| `F2` | Bandă / Band cycle |
| `F3` | Mod / Mode cycle |

---

## 🔧 Cerințe sistem / Requirements

- **Python 3.6+** (3.8 recomandat pentru Windows 7)
- `tkinter` — inclus pe Windows; Linux: `sudo apt install python3-tk`
- `pyserial` — opțional CAT: `pip install pyserial`

---

## 📁 Structura repo

```
YOLogPRO_v17.1/
├── yo_log_pro_v171.py
├── README.md
├── docs/
│   ├── MANUAL_RO.md
│   └── MANUAL_EN.md
└── .github/workflows/build.yml
```

---

## 📜 Changelog

### v17.1
- `ADDED` Log Editor dedicat — fereastră separată completă
- `ADDED` Callbook — radioamator.ro + QRZ.com
- `ADDED` Band Map · Scor Live · Alert Multiplicator
- `ADDED` DX Cluster GUI · Rate QSO Stats
- `ADDED` CAT Radio complet bidirecțional
- `FIXED` Compatibilitate Windows 7

### v17.0
- `FIXED` Freq / Bandă / Mod / RST persistă între QSO-uri

### v16.x
- `ADDED` Cabrillo 2.0 · Import · Preview · Soapbox

---

**73 de YO8ACR! 📻**
