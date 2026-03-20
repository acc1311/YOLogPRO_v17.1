# 📻 YO Log PRO v17.1 — Full Edition

**Dezvoltat de:** Ardei Constantin-Cătălin (YO8ACR)  
**Versiune:** 17.1  
**Compatibilitate:** Windows 7 / 8 / 10 / 11 (x64)  
**Limbă interfață:** Română / Engleză  

[![Build Status](https://github.com/acc1311/YOLogPRO_v17.1/actions/workflows/build.yml/badge.svg)](https://github.com/acc1311/YOLogPRO_v17.1/actions)

---

## 📥 Descărcare

| Fișier | Descriere |
|--------|-----------|
| `YO_Log_PRO_v17.1_Setup.exe` | ⭐ **Installer recomandat** — instalează în Program Files, creează scurtătură Desktop + meniu Start |
| `YO_Log_PRO_v17.1.exe` | Versiune portabilă — rulează direct, fără instalare |
| `YO_Log_PRO_v17.1_Windows.zip` | Pachet complet (installer + portabil + manuale RO/EN) |

> Disponibile în tab-ul **[Releases](../../releases)**

---

## 📋 Descriere

YO Log PRO este un program complet de logare pentru radioamatori, destinat concursurilor naționale și internaționale. Suportă toate formatele standard de export/import, control CAT pentru transceivere, callbook online și multe altele.

---

## ✅ Istoric modificări

### v17.1 — Versiunea curentă

#### 🆕 Funcționalități noi

**1. Opțiune format dată la export Cabrillo 2.0**

La exportul Cabrillo 2.0, utilizatorul poate alege acum formatul datei din dialog:
- `YYYY-MM-DD` — format standard Cabrillo, compatibil cu toate programele de arbitraj ✅ *(implicit)*
- `YYYYMMDD` — format fără liniuțe, pentru compatibilitate cu programe mai vechi ✅

Preferința se salvează automat și este reținută la exporturile următoare.

**Fișier modificat:** `yo_log_pro_v171.py`  
**Locații modificate:**
- `class Cab2ConfigDialog` — adăugat dropdown „Format dată QSO" în dialog
- `def _ok()` — returnează `date_fmt` în result
- `def _exp_cab2()` — salvează preferința în `config.json` și aplică formatul ales

```python
# Logică normalizare dată — acceptă ambele formate stocate intern:
d_raw = q.get("d", "").replace("-", "")   # normalizează la YYYYMMDD
if len(d_raw) == 8:
    date = f"{d_raw[:4]}-{d_raw[4:6]}-{d_raw[6:8]}" if date_fmt == "with_dash" else d_raw
```

---

**2. Installer Windows (NSIS)**

Adăugat installer profesional pentru Windows:
- Instalare în `C:\Program Files\YO Log PRO\` ✅
- Scurtătură pe **Desktop** cu icon ✅
- Folder în **meniul Start** ✅
- Apare în **Add/Remove Programs** (dezinstalare curată) ✅
- Detectează versiunea existentă și oferă dezinstalare înainte de reinstalare ✅
- La dezinstalare, întreabă dacă se șterg și datele salvate (loguri, configurații) ✅

**Fișier nou:** `installer.nsi`

---

**3. Build automat GitHub Actions**

Workflow complet de build automat:
- ✅ Verificare sintaxă Python la fiecare push
- ✅ Build EXE Windows cu PyInstaller (compatibil Win7+)
- ✅ Build Installer cu NSIS
- ✅ Generare ZIP complet (installer + portabil + docs)
- ✅ Upload artifacts (disponibile 90 zile)
- ✅ Creare automată GitHub Release la `workflow_dispatch` cu opțiunea activată

**Fișier modificat:** `.github/workflows/build.yml`

---

**4. UI Scroll & Responsive**

- Funcție `_responsive_geometry()` — ferestre popup adaptate la rezoluția și scalarea DPI (21 ferestre)
- Funcție `_make_scrollable_dialog()` — scroll bidirectional (vertical + orizontal) în popup-uri
- Opțiune în Setări: „Activează scroll la ferestre popup"
- Fereastra principală responsivă — se adaptează la orice rezoluție
- Bara de butoane cu scroll orizontal automat pe ecrane mici
- Scrollbar-uri adăugate la Treeview-urile din statistici

**5. Callbook Lookup**

- Căutare radioamator.ro și QRZ.com cu extragere date
- Previzualizare web integrată

**6. DXCC Database**

- Loader `cty.dat` cu suport extern + fallback intern

**7. Live Contest Score Panel**

- Scor în timp real cu rata QSO/h afișată grafic

**8. CAT Radio complet**

- Suport Yaesu, Icom, Kenwood, Elecraft, Hamlib
- Polling configurabil, control frecvență și mod

**9. Cabrillo 2.0 Export**

- Export cu dialog configurabil pentru exchange
- Preview înainte de salvare
- Import Cabrillo 2.0 și 3.0

**10. Log Editor dedicat**

- Editare completă a QSO-urilor din log
- Undo/Redo

---

## 🔧 Compatibilitate

| Sistem | Status |
|--------|--------|
| Windows 7 (x64) | ✅ Testat |
| Windows 8 / 8.1 | ✅ |
| Windows 10 | ✅ Testat |
| Windows 11 | ✅ Testat |
| Scalare DPI 100% | ✅ |
| Scalare DPI 125% | ✅ |
| Scalare DPI 150% | ✅ |
| Scalare DPI 200% | ✅ |
| Python 3.8+ | ✅ (doar sursă) |

---

## 📁 Formate suportate

### Import
| Format | Extensie | Note |
|--------|----------|-------|
| Cabrillo 2.0 / 3.0 | `.log`, `.cbr` | Detectare automată versiune |
| ADIF | `.adi`, `.adif` | Standard internațional |
| CSV | `.csv` | Auto-detectare separator |
| JSON | `.json` | Format intern YO Log PRO |
| EDI | `.edi` | Concursuri VHF/UHF |

### Export
| Format | Note |
|--------|-------|
| Cabrillo 2.0 | Cu opțiune format dată: `YYYY-MM-DD` sau `YYYYMMDD` |
| Cabrillo 3.0 | Format standard internațional |
| ADIF | `.adi` |
| CSV | `.csv` |
| PDF | Raport rezultate |

---

## 🏆 Concursuri suportate

- Maratonul Ion Creangă (IC)
- Cupa 1 Decembrie
- Cupa Moldovei
- Cupa Tomis
- Lucian Blaga
- Memorial YO
- Simple Log (logare generală)
- Field Day, Sprint, QSO Party, SOTA, POTA
- Concursuri custom (editor reguli inclus)

---

## 📂 Structura fișierelor

```
YOLogPRO_v17.1/
├── yo_log_pro_v171.py          # Sursă principală
├── installer.nsi               # Script installer NSIS
├── icon.ico                    # Icon aplicație
├── requirements.txt            # Dependențe Python
├── README.md                   # Acest fișier
├── docs/
│   ├── MANUAL_RO.md            # Manual utilizare română
│   └── MANUAL_EN.md            # Manual utilizare engleză
└── .github/
    └── workflows/
        └── build.yml           # Workflow build automat
```

---

## 🚀 Rulare din sursă

```bash
# Instalare dependențe
pip install -r requirements.txt

# Rulare
python yo_log_pro_v171.py
```

**Dependențe principale:**
- `tkinter` — inclusă în Python standard
- `pyserial` — pentru CAT radio
- `tkinterweb` — pentru previzualizare web callbook (opțional)

---

## 📞 Contact & Suport

**Autor:** Ardei Constantin-Cătălin  
**Indicativ:** YO8ACR  
**GitHub:** [acc1311/YOLogPRO_v17.1](https://github.com/acc1311/YOLogPRO_v17.1)

---

*73 de YO8ACR! 📻*
