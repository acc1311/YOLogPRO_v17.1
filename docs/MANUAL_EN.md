# 📻 YO Log PRO v17.1 — User Manual

**Professional Multi-Contest Amateur Radio Logger**  
Author: **Ardei Constantin-Cătălin (YO8ACR)** · yo8acr@gmail.com  
Document version: **v17.1** · Language: 🇬🇧 English

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [First Run — Initial Setup](#3-first-run)
4. [Main Interface](#4-main-interface)
5. [Logging a QSO](#5-logging-a-qso)
6. [Editing and Deleting QSOs](#6-editing-and-deleting-qsos)
7. [Dedicated Log Editor](#7-dedicated-log-editor)
8. [Callbook Search — radioamator.ro and QRZ.com](#8-callbook-search)
9. [Band Map](#9-band-map)
10. [DX Cluster](#10-dx-cluster)
11. [Live Score](#11-live-score)
12. [QSO Rate Statistics](#12-qso-rate-statistics)
13. [CAT Radio Control](#13-cat-radio-control)
14. [Contest Manager](#14-contest-manager)
15. [Log Export](#15-log-export)
16. [Log Import](#16-log-import)
17. [DXCC and cty.dat](#17-dxcc-and-ctydat)
18. [Themes and Colours](#18-themes-and-colours)
19. [General Settings](#19-general-settings)
20. [Backup and Recovery](#20-backup-and-recovery)
21. [Keyboard Shortcuts](#21-keyboard-shortcuts)
22. [File Structure](#22-file-structure)
23. [Troubleshooting](#23-troubleshooting)
24. [Built-in Contests](#24-built-in-contests)

---

## 1. Introduction

**YO Log PRO v17.1** is a complete, free, open-source amateur radio contest logger written in Python. It is designed for participants in Romanian and international amateur radio contests, providing all the tools needed for fast logging, live scoring, Cabrillo/ADIF export, and CAT radio control.

**Key features:**
- Runs from a single `.py` file or as a `.exe` — no installation required
- Compatible with **Windows 7, 8, 10, 11**, Linux and macOS
- Bilingual: interface in **Romanian** and **English**, switchable live
- 7 Romanian and international contests pre-configured
- Unlimited custom contest editor
- Bidirectional CAT control: Yaesu, Icom, Kenwood, Elecraft, Hamlib

---

## 2. Installation

### 2.1 Windows Executable (recommended)

1. Download `YO_Log_PRO_v17.1.exe` from [Releases](../../releases/latest)
2. Place the file in a dedicated folder (e.g. `C:\YOLog\`)
3. Double-click to start — **Python installation not required**

> ⚠️ **Windows 7:** If you get "VCRUNTIME140.dll is missing", install [Visual C++ 2015 Redistributable](https://www.microsoft.com/download/details.aspx?id=52685)

### 2.2 Python source (cross-platform)

**Requirements:**
- Python 3.6 or newer (3.8 recommended for Windows 7)
- `tkinter` — included on Windows; Linux: `sudo apt install python3-tk`
- `pyserial` — optional, for CAT control

```bash
# Install pyserial (optional)
pip install pyserial

# Start the application
python yo_log_pro_v171.py
```

**Windows 7 note:** Download Python 3.8.x from [python.org](https://www.python.org/downloads/release/python-3810/) — this is the last version that supports Windows 7.

---

## 3. First Run

On first launch, the **initial configuration dialog** appears automatically. Fill in:

| Field | Description | Example |
|---|---|---|
| **Callsign** | Your amateur radio callsign | `YO8ACR` |
| **Locator** | Maidenhead grid locator (6 chars) | `KN37` |
| **County** | County code for YO contests | `NT` |
| **Address** | Postal address (for Cabrillo) | `Targu Neamt` |
| **Operator** | Your name | `Constantin Ardei` |
| **Power (W)** | Transmit power in watts | `100` |
| **Email** | Email address (for Cabrillo export) | `yo8acr@gmail.com` |
| **Language** | Interface language: `ro` or `en` | `en` |

Click **Save** — the configuration is stored in `config.json`.

> You can change settings at any time via **Menu → ⚙ Settings**.

---

## 4. Main Interface

```
┌─────────────────────────────────────────────────────────────────┐
│ ● Online UTC  YO8ACR | Simple Log | QSO: 0  [contest ▼] [en▼]  │  ← Header
│                                   UTC 14:32:15  ⚡45 QSO/h      │
├─────────────────────────────────────────────────────────────────┤
│  [Callsign] [Freq kHz] [Band▼] [Mode▼] [RST S] [RST R] [Note]  │  ← Entry form
│  🌐 Callbook                                                     │
│  □ Manual    [  LOG  ]  [Reset]   Date: ...  Time: ...  Cat▼    │
├─────────────────────────────────────────────────────────────────┤
│  Band: [All▼]  Mode: [All▼]                Σ QSO×Mult=Score    │  ← Filters
├─────────────────────────────────────────────────────────────────┤
│  Nr │ Callsign  │ Freq │ Band  │ Mode │ RST │ Note │ Country │  │  ← LOG
│   1 │ YO8ACR    │14200 │  20m  │ SSB  │  59 │ KN37 │ Romania │  │
│   2 │ DL5ABC    │14200 │  20m  │ SSB  │  59 │ JO31 │ Germany │  │
├─────────────────────────────────────────────────────────────────┤
│[Settings][Contests][CAT][New Log][Themes][Stats][Export]...     │  ← Buttons
└─────────────────────────────────────────────────────────────────┘
```

### 4.1 Header (top bar)
- **Green LED** = UTC clock online · **Red LED** = offline
- **Callsign + active contest + QSO count** — updates live
- **UTC** — real-time clock
- **⚡ QSO/h** — QSO rate for the last hour
- **CAT indicator** — shows frequency and mode read from radio
- **Contest selector** — switches active contest (current log is saved automatically)
- **Language selector** — `ro` / `en`, changes live without restart

### 4.2 Entry Form
Fields persist between QSOs (frequency, band, mode, RST). Only **Callsign** and **Note** are cleared after logging.

---

## 5. Logging a QSO

### Quick steps:
1. Type the **callsign** in the Call field (auto-converts to upper case)
2. Check/modify **frequency** (kHz) — band is set automatically
3. Verify **band, mode, RST S, RST R**
4. Fill in **Note/Locator** if required
5. Press **`Enter`** or the **LOG** button

### Automatic detection:
- **⚠ DUP** — appears red below the Call field if the callsign is already in the log on the same band and mode
- **ℹ Worked other QRG** — yellow, if the callsign was worked on a different band/mode
- **✦ NEW MULT!** — golden flash in the score bar + beep when a new multiplier is logged

### Date/Time:
- Default: **automatic UTC** from system clock
- Check **□ Manual** to enter date/time manually (for contests with a fixed start date)

### Serial Numbers:
If the contest uses serial numbers (`use_serial: true`), the **Nr S** and **Nr R** fields appear automatically. Nr S increments automatically with each QSO.

---

## 6. Editing and Deleting QSOs

### From the main window:
- **Double-click** on a log row → loads into the form for editing
- **Right-click** → context menu: Edit / Delete
- **Ctrl+Z** → undo last added QSO
- The **LOG** button becomes **UPDATE** when in edit mode

### Undo:
The undo stack holds up to 50 operations. Works for both add and delete.

---

## 7. Dedicated Log Editor

**Open:** `📝 Log Editor` button in the bottom bar, or menu **📡 v17.1 → 📝 Dedicated Log Editor**

The Log Editor is a fully independent window designed for post-contest editing or detailed log correction.

### Features:

#### Filtering
- **Quick filter** (free text) — searches callsign and note simultaneously
- **Band filter** — All / 160m / 80m / ... / 23cm
- **Mode filter** — All / SSB / CW / FT8 / ...
- All filters work simultaneously, live (no Enter needed)

#### Treeview
- **All columns** visible: Nr, Callsign, Freq, Band, Mode, RST S, RST R, Nr S, Nr R, Note, Country, Date, Time, Points
- **Sortable** on any column — click header, click again to reverse
- Colour coding: red = duplicate, green = multiplier, blue = special station
- Results indicator: `Shown: X/Y QSO`

#### Editing
1. **Double-click** on a row → form fields at the bottom populate
2. Make your changes
3. Click **💾 Update**
4. Change is saved to disk automatically + backup created

#### Adding a New QSO
- Fill in the form without selecting any row in the treeview
- Click **💾 Save** — the QSO is added to the top of the log

#### Local Undo
- **↩ Undo** button reverses the last operation (add, delete or modify)
- Local stack of 50 operations, independent from the main window undo

#### Context Menu (right-click)
- **✏ Edit** — loads QSO into the form
- **🗑 Delete** — deletes with confirmation
- **🌐 Callbook** — opens Callbook Lookup for the selected callsign
- **📋 Copy call** — copies callsign to clipboard
- **🔗 QRZ.com** — opens QRZ page in browser
- **🔗 radioamator.ro** — opens callbook page in browser

#### Synchronisation
Any change in the Log Editor is reflected **instantly** in the main window and vice versa.

---

## 8. Callbook Search

**Open:**
- `🌐 Callbook` button in the main window bottom bar
- Small `🌐` button below the Callsign field in the entry form
- Menu **📡 v17.1 → 🌐 Callbook Lookup**
- Right-click in Log Editor → **🌐 Callbook**

### Data Sources:

#### radioamator.ro
The Romanian national amateur radio database. Contains:
- Full name
- QTH (town, county)
- Maidenhead locator
- Licence class (A, B, C)
- Licence expiry date
- ITU and CQ zones

#### QRZ.com
International database. Extracts from the public page (no account required):
- Name
- QTH
- Grid locator
- DXCC entity
- ITU / CQ zones

### Usage:
1. Enter the callsign in the search field
2. Select the source: `radioamator.ro` or `QRZ.com`
3. Click **🔍 Search** or press `Enter`
4. Results appear in the fields below within a few seconds
5. **✅ Use Locator** → automatically copies the locator into the Note field in the form — useful for VHF contests
6. **🌐 Open in browser** → opens the full page in your browser

> **Note:** Callbook lookup requires an active internet connection. The search runs in a background thread — the interface remains responsive while searching.

---

## 9. Band Map

**Open:** Menu **📡 v17.1 → 📡 Band Map**

The Band Map displays your QSO activity grouped by each amateur radio band.

### How to read it:
- Each **column** = one band (160m, 80m, ..., 23cm)
- **Coloured header** = band-specific colour
- **QSO count** per band
- List of recent QSOs per band (up to 20 most recent)
- **DX QSOs** (different country) are highlighted in **cyan**
- If you have a locator in Settings, distance in km is shown

### Refresh:
- Automatic every **30 seconds**
- Manual with the **↺ Refresh** button

### Stats bar (bottom):
`Total QSO: X | DXCC: Y | Active bands: Z | Last refresh: HH:MM:SS UTC`

---

## 10. DX Cluster

**Open:** Menu **📡 v17.1 → 📡 DX Cluster**

Integrated DX Cluster client with telnet connection to amateur radio cluster nodes.

### Pre-configured clusters:
- `dxc.yo8acr.ro:7300`
- `cluster.dl9gtb.de:7300`
- `dx.db0sue.de:7300`
- `www.dxsummit.fi:7300`
- `gb7mbc.spoo.org:7300`

You can add any cluster in `hostname:port` format.

### Connecting:
1. Select a cluster from the dropdown (or type manually `host:port`)
2. Enter **your callsign** in the Call field
3. Click **▶ Connect**
4. Connection status appears in the top-right corner of the window

### DX Spots:
- The main table shows spots with: UTC, DX Call, Frequency, Band, Mode, Country, Comment, Spotter
- **DX entities** are highlighted with a special colour

### Filtering Spots:
- **Band filter** — shows only spots on the selected band
- **Call filter** — searches in DX Call and Spotter simultaneously

### Click-to-Log:
**Double-click on a spot** → the callsign and frequency are automatically filled into the main window entry form! Ready to log immediately.

### Raw Window:
Displays all raw messages received from the cluster (including announcements, WWV, etc.)

### Sending Commands:
The bottom field + **Send** button (or `Enter`) lets you send commands directly to the cluster:
- `SH/DX 20` — last 20 spots
- `SH/DX ON 20m` — spots on 20m
- `SET/FILTER` — server-side filters
- `BYE` — disconnect

---

## 11. Live Score

**Open:** Menu **📡 v17.1 → 📊 Live Score**

A dedicated panel with the contest score updated in real time.

### Information displayed:
| Field | Description |
|---|---|
| **TOTAL SCORE** | Large central number — full score (QSO pts × multipliers) |
| **Total QSO** | Number of QSOs in the log |
| **QSO Points** | Sum of QSO points (before multipliers) |
| **Multipliers** | Number of unique multipliers |
| **DXCC** | Distinct DXCC entities worked |
| **QSO/h (1h)** | Rate for the last full hour |
| **QSO/h (10min)** | Rate for last 10 minutes × 6 (projected/hour) |
| **Unique calls** | Distinct callsigns in log |
| **Countries** | Number of distinct countries |

### Per-band chart:
Progress bars for each active band, proportional to QSO count.

### Refresh:
- Automatic every **15 seconds**
- Manual with **↺ Refresh** button

---

## 12. QSO Rate Statistics

**Open:** Menu **📡 v17.1 → 📈 Rate QSO Stats**

### QSO/h Chart:
- Bar chart with QSOs per hour for the last **24 hours**
- The peak bar is highlighted differently (cyan)
- Numeric value shown above each bar
- Gridlines with values on Y axis

### Top DXCC Table:
Top 20 DXCC entities worked, sorted descending.

### Per Band Table:
QSO distribution by band with percentage of total.

### Summary stats:
- Total QSO, Unique calls, DXCC, Rate 1h, Last QSO gap, Most active band

### Refresh:
Automatic every **60 seconds**.

---

## 13. CAT Radio Control

**Configure:** Menu **CAT → CAT Settings**

### Supported protocols:

| Protocol | Compatible radios |
|---|---|
| **Yaesu CAT** | FT-817, FT-857, FT-897, FT-991, FT-DX101, FT-710, FT-5D... |
| **Icom CI-V** | IC-706, IC-718, IC-7200, IC-7300, IC-7610, IC-9700, IC-705... |
| **Kenwood CAT** | TS-480, TS-590, TS-850, TS-2000, TS-990... |
| **Elecraft CAT** | K3, K3S, KX3, KX2, K4... |
| **Hamlib/rigctld** | Any Hamlib-supported radio via rigctld |
| **Manual** | No CAT — manual entry |

### Setting up Yaesu/Icom/Kenwood/Elecraft:
1. Connect the CAT cable (COM/USB-serial)
2. Menu **CAT → CAT Settings**
3. Select the **protocol** and **COM port**
4. Set the **baud rate** (default per protocol)
5. Click **Test connection** — the current frequency should appear
6. Check **✓ Enable CAT on startup**

### Setting up Hamlib/rigctld:
1. Start rigctld: `rigctld -m MODEL -r PORT -s BAUD`
   - E.g.: `rigctld -m 122 -r /dev/ttyUSB0 -s 19200` (Icom IC-706)
2. In YO Log PRO: Protocol = **Hamlib/rigctld**, Host = `localhost`, Port = `4532`

### Once connected:
- **Frequency** and **mode** update automatically in the entry form every 2 seconds
- The **CAT** indicator in the header shows current frequency and mode
- When you modify frequency in the Freq field and press `Enter`, it is **sent to the radio**

### CI-V address for Icom:
Hexadecimal address of your radio (default `94`). Check in your radio's menu (e.g. IC-7300: `98`).

---

## 14. Contest Manager

**Open:** **Contests** button or menu **Contests**

### Adding a new contest:
1. Click **➕ Add**
2. Fill in the fields:
   - **ID** — unique identifier (e.g. `my-contest-2025`), no spaces
   - **Name RO / EN** — name displayed in the interface
   - **Type** — Simple, Marathon, Relay, DX, VHF, Field Day, etc.
   - **Scoring mode** — none / per_qso / per_band / maraton / multiplier / distance
   - **Points/QSO** — points value per QSO
   - **Exchange format** — none / county / grid / serial / zone
   - **Multipliers** — none / county / dxcc / band / grid
   - **Allowed bands** — tick the valid bands
   - **Allowed modes** — tick the valid modes
   - **Categories** — one category per line (e.g. `Single Op`, `Multi Op`, `QRP`)
   - **Required stations** — callsigns one per line (will be highlighted in log)
   - **Special scoring** — `CALL=points` per line (e.g. `YO8KRR=10`)
   - **Band points** — `BAND=points` per line (e.g. `20m=2`)

3. Click **Save**

### Duplicating a contest:
Click **📋 Duplicate** on an existing contest — creates a copy with `-copy` suffix that you can modify freely.

### Export/Import contests JSON:
You can export and import contest definitions in JSON format to share with other YO Log PRO users.

---

## 15. Log Export

**Open:** **Export** button or menu **Export**

### Available formats:

#### Cabrillo 2.0 (.log)
Standard format for submitting contest logs to organisers.
- Exchange configuration dialog (what you send / what you receive)
- **Preview** before saving
- Automatic log validation before export

**Exchange Sent options:**
- `County` — sends your county code
- `Locator` — sends your Maidenhead locator
- `Serial Nr.` — sends the QSO serial number
- `None (--)` — for contests without exchange

**Exchange Received options:**
- `From log` — takes from the Note or Serial field of the QSO
- `None (--)` — does not export received exchange

#### ADIF 3.1 (.adi)
Universal format for import into other programs (DXKeeper, Logger32, Ham Radio Deluxe, etc.)

#### EDI (.edi)
REG1TEST format for European VHF contests (IARU, VERON, etc.)

#### CSV (.csv)
Tabular format for analysis in Excel or LibreOffice Calc.

#### Print (.txt)
Formatted text report, printable or sendable by email.

---

## 16. Log Import

**Open:** **Import** button or menu **Tools → Import**

### Supported formats:
- **ADIF** (.adi, .adif) — from any other logging program
- **Cabrillo 2.0** (.log) — including logs from other programs
- **Cabrillo 3.0** (.log)
- **CSV** (.csv) — with header: Call,Band,Mode,Date,Time,RST_S,RST_R,Note

> ⚠️ On import, new QSOs are added to the current log (not overwritten).

---

## 17. DXCC and cty.dat

### Built-in database
YO Log PRO includes a DXCC database with prefixes for ~150 entities, manually maintained. This is sufficient for most Romanian and common European contests.

### BigCTY external (recommended for DX)
For a complete database with all DXCC entities:
1. Download `cty.dat` from [country-files.com](https://www.country-files.com/)
2. Menu **📡 v17.1 → 📂 Load cty.dat**
3. Select the downloaded `cty.dat` file
4. Confirm — prefixes are added to the internal database

> The database resets to the built-in one on restart. To always use BigCTY, place `cty.dat` in the same folder as the application — it will load automatically.

---

## 18. Themes and Colours

**Open:** **🎨 Themes** button or menu **Themes**

### Pre-configured themes:
- **Dark Blue (default)** — standard theme, dark blue
- **Dark Green** — dark green, CW/old-school style
- **Dark Red** — dark red
- **Dark Purple** — dark purple
- **Light (Day)** — light background for daytime use
- **Light Sepia** — warm sepia, high visual comfort

### Quick apply from menu:
Menu **Themes** → pick a theme directly without opening the editor.

### Custom colour editor:
- Select a base theme
- Modify individual colours: Background, Text, Accent, Fields, Header, Clock/Score, OK, Error, Warning
- **Double-click** on a colour or its colour swatch → opens colour picker
- **✅ Save** → theme is applied and saved in `config.json`

---

## 19. General Settings

**Open:** **⚙ Settings** button

| Field | Description |
|---|---|
| Callsign | Your station callsign |
| Locator | Maidenhead locator (e.g. `KN37MB`) |
| County | County code for exchange |
| Address | Full postal address |
| Operator | Operator name |
| Power (W) | Transmit power in watts |
| Email | Email for Cabrillo export |
| Soapbox | Free text message for Cabrillo |
| Language | `ro` / `en` |
| Font | Font size (9–14) |
| Sounds | Enable/disable audio alerts |
| CAT | Radio control settings |

---

## 20. Backup and Recovery

### Automatic backup:
- On every normal application exit
- Before every Cabrillo export
- **💾 Backup** button in the button bar

### Backup location:
The `backups/` folder in the same directory as the application.  
Format: `log_CONTESTID_YYYYMMDD_HHMMSS.json`  
Up to **50 backups** are retained per contest.

### Restoring a backup:
1. Open the `backups/` folder
2. Find the desired backup file
3. Copy it over the `log_CONTESTID.json` file in the main directory
4. Restart the application

### Log integrity check:
Menu **Tools → Verify Log** — checks the MD5 hash of the log and displays the QSO count.

---

## 21. Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Add / Update QSO |
| `Ctrl+S` | Manual log save |
| `Ctrl+Z` | Undo last QSO |
| `Ctrl+F` | Open log search |
| `F2` | Cycle to next band |
| `F3` | Cycle to next mode |
| `Double-Click` on QSO | Edit selected QSO |
| `Delete` (in Log Editor) | Delete selected QSO |

---

## 22. File Structure

```
📁 Application directory/
│
├── yo_log_pro_v171.py       ← Main application
│   or YO_Log_PRO_v17.1.exe
│
├── config.json              ← Your configuration (created automatically)
├── contests.json            ← Contest definitions (created automatically)
│
├── log_simplu.json          ← Log for contest "simplu"
├── log_maraton.json         ← Log for contest "maraton"
├── log_yo-dx-hf.json        ← Log for contest "yo-dx-hf"
├── log_[id].json            ← One file per active contest
│
├── cty.dat                  ← (optional) BigCTY external database
│
└── 📁 backups/
    ├── log_simplu_20250306_143215.json
    ├── log_simplu_20250307_092011.json
    └── ...
```

> **Important:** Place the application in a folder where you have write permissions (e.g. `Documents\YOLog\`), **not** in `C:\Program Files\`.

---

## 23. Troubleshooting

### Application won't start (Windows)
- **"Python is not recognised"** → Python not in PATH; reinstall with "Add to PATH" ticked
- **"VCRUNTIME140.dll is missing"** → Install Visual C++ 2015 Redistributable
- **"No module named tkinter"** → On Linux: `sudo apt install python3-tk`

### CAT not working
- Check the COM port is correct and not in use by another program
- Check baud rate — must match the radio's setting
- Windows: check Device Manager that the port shows with no errors (!)
- Try **disabling** and **re-enabling** CAT from the menu
- Icom CI-V: check the CI-V address of your radio (radio menu → CI-V Address)

### COM port not found (Windows 7)
- Install USB-Serial drivers (FTDI or Silicon Labs) for your CAT cable
- Restart after driver installation

### DX Cluster won't connect
- Check your internet connection
- Some clusters have downtime; try another cluster from the list
- Check that port 7300 is not blocked by your firewall

### Callbook not finding a callsign
- The callsign may not be registered in the selected database
- Try the other source (radioamator.ro vs QRZ.com)
- Check your internet connection
- Some callsigns are only accessible with a QRZ.com account (premium pages)

### Score not calculating
- Check that you have selected a contest with a scoring system (not "Simple Log")
- Check contest settings: `scoring_mode` must be something other than `none`

### Log corrupted / lost
- Check the `backups/` folder and restore the last valid backup
- Do not manually delete `.json` files while the application is running

---

## 24. Built-in Contests

### Simple Log (`simplu`)
General log, no contest rules. Ideal for regular activity, SOTA, POTA.
- All bands and modes allowed
- No scoring

### Maraton Ion Creangă (`maraton`)
Romanian marathon contest.
- Categories: Seniors YO, YL, Juniors, Club, DX, Receivers
- Scoring: marathon (special stations with different point values)
- Multipliers: YO counties
- Exchange: county code

### Relay / Ștafetă (`stafeta`)
- 2 points per QSO
- Serial numbers required
- Multipliers: YO counties
- Exchange: county + serial

### YO DX HF Contest (`yo-dx-hf`)
- Points by band: 160m=4, 80m=3, 40m=2, 20m=1, 15m=1, 10m=2
- Multipliers: DXCC entities
- Exchange: YO county + serial

### YO VHF Contest (`yo-vhf`)
- Scoring: km distance
- Multipliers: Maidenhead grid squares
- Bands: 6m, 2m, 70cm, 23cm
- Exchange: locator

### Field Day (`field-day`)
- 2 points per QSO
- Categories: 1A, 2A, 3A, 1B, 2B

### Sprint (`sprint`)
- 1 point per QSO
- Serial numbers required
- Bands: 40m, 20m, 15m, 10m
- Modes: SSB, CW

---

*Manual updated for version v17.1*  
*Author: YO8ACR | yo8acr@gmail.com*  
*73! 📻*
