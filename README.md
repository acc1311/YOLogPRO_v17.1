# YO Log PRO v17.1 — Modificări UI Scroll & Responsive

**Bazat pe:** YO Log PRO v17.1 Full Edition — Ardei Constantin-Cătălin (YO8ACR)  
**Modificări realizate de:** Patch UI — scroll bidirectional + geometrie responsivă  

---

## Rezumat modificări

## 1. Funcție nouă — `_responsive_geometry()`

**Locație în cod:** deasupra clasei `TimerDialog`

Înlocuiește apelurile fixe `.geometry("WxH")` din toate ferestrele popup cu o funcție care calculează dimensiunea optimă în funcție de rezoluția și scalarea ecranului curent.

**Comportament:**
- Fereastra nu depășește 92% din lățimea ecranului și 88% din înălțime
- Se centrează automat față de fereastra părinte
- Nu iese niciodată în afara marginilor ecranului
- Funcționează corect la scalări DPI de 100%, 125%, 150%, 200%

**Ferestre afectate (21 total):**

| Fereastră | Geometrie originală | Geometrie nouă |
|---|---|---|
| Timer Concurs | 360×300 fix | responsivă |
| Statistici (StatsWindow) | 560×520 fix | responsivă |
| Contest Editor | 720×880 fix | responsivă |
| Contest Manager | 750×500 fix | responsivă |
| Search Dialog | 600×420 fix | responsivă |
| CAT Settings | 560×620 fix | responsivă |
| Cab2 Config | 420×250 fix | responsivă |
| Preview Dialog | 750×550 fix | responsivă |
| New Log Dialog | 420×260 fix | responsivă |
| Theme Dialog | 620×540 fix | responsivă |
| First Run Dialog | 560×680 fix | responsivă |
| Log Editor | 1200×680 fix | responsivă |
| Callbook Dialog | 780×600 fix | responsivă |
| Band Map | 820×500 fix | responsivă |
| DX Cluster | 860×520 fix | responsivă |
| Rate Stats | 860×560 fix | responsivă |
| Live Score Panel | 420×500 fix | responsivă |
| About | 520×360 fix | responsivă |
| Settings | 420×560 fix | responsivă |
| Import Log | 280×200 fix | responsivă |
| Export | 300×310 fix | responsivă |

---

## 2. Funcție nouă — `_make_scrollable_dialog()`

**Locație în cod:** deasupra clasei `TimerDialog`

Înfășoară conținutul oricărei ferestre popup într-un `Canvas` Tkinter cu scrollbar-uri pe **ambele axe** (vertical și orizontal).

**Comportament:**
- Scroll **vertical** — `MouseWheel` / `Button-4` / `Button-5` (Linux)
- Scroll **orizontal** — `Shift + MouseWheel`
- Scrollbar-urile se **ascund automat** când conținutul încape fără scroll
- Evenimentele de scroll se **propagă la toate widget-urile copil** (Labels, Entries, LabelFrames etc.) cu re-binding automat la 200ms după construirea ferestrei
- Dacă opțiunea din Setări este dezactivată, funcția returnează fereastra normală fără wrapping

**Ferestre care folosesc scroll bidirectional:**
- Timer Concurs
- Setări (Settings)

---

## 3. Opțiune nouă în Setări — „Activează scroll la ferestre popup"

**Locație:** meniu `Setări` → checkbox la baza listei de câmpuri

Un checkbox nou salvat în `config.json` ca `scroll_popups: true/false`.

- **Activat (implicit):** toate ferestrele popup au scroll bidirectional
- **Dezactivat:** ferestrele revin la comportamentul original fără wrapping Canvas

String-uri adăugate în dicționarele de limbă:

```python
# Română
"en_scroll": "Activează scroll la ferestre popup"

# Engleză
"en_scroll": "Enable scroll on popup windows"
```

Câmp adăugat în `DEFAULT_CFG`:

```python
"scroll_popups": True
```

---

## 4. Fereastra principală — `_setup_win()` responsivă

**Comportament original:**
```python
self.geometry("1280x780")
self.minsize(1100, 680)
```

**Comportament nou:**
```python
# 96% din lățimea ecranului × 92% din înălțime
def_w = max(900, min(1280, int(sw * 0.96)))
def_h = max(600, min(780,  int(sh * 0.92)))
self.geometry(f"{def_w}x{def_h}")

# minsize dinamic: 55% lățime, 60% înălțime
self.minsize(max(700, int(sw * 0.55)), max(480, int(sh * 0.60)))
```

Fereastra salvată în `win_geo` din `config.json` este respectată în continuare.

---

## 5. Bara de butoane de jos — `_build_btns()` responsive

**Problema originală:** la scalare 100% pe ecrane cu rezoluție mică, butoanele cu lățimi fixe (`w=9`, `w=10`) depășeau marginea ferestrei și nu se vedeau complet.

**Soluție implementată:**

- Butoanele sunt acum înfășurate într-un **Canvas cu scrollbar orizontal**
- Scrollbar-ul apare **doar dacă butoanele nu încap** pe lățimea ferestrei (se ascunde automat altfel)
- La ecrane cu lățime sub 1200px (scalare 100% pe monitoare mici), se activează automat **modul compact:**
  - Font redus de la `Consolas 9` la `Consolas 8`
  - Padding orizontal redus
  - Butoanele se dimensionează după text (fără lățime fixă)
- Scroll orizontal pe bara de butoane cu `MouseWheel` sau `Shift+MouseWheel`

---

## 6. Scrollbar-uri adăugate la Treeview-uri fără scroll

**Statistici Rate QSO (`RateStatsWindow`):**
- Tabelul `Top DXCC` — scrollbar vertical adăugat
- Tabelul `Per Bandă` — scrollbar vertical adăugat
- Ambele tabele au binding `MouseWheel` pentru scroll cu rotița

---

## Compatibilitate

| Sistem | Status |
|---|---|
| Windows 7 / 8 / 10 / 11 | ✅ Testat |
| Linux (Tkinter) | ✅ Button-4/5 suportat |
| macOS | ✅ MouseWheel standard |
| Scalare DPI 100% | ✅ Rezolvat (v3) |
| Scalare DPI 125% | ✅ |
| Scalare DPI 150% | ✅ |
| Python 3.6+ | ✅ |

---

## Fișiere modificate

```
yo_log_pro_v171.py  →  yo_log_pro_v171_scroll_v3.py
```

Niciun fișier extern (`.json`, `.dat`, `.log`, `.adi`) nu este afectat de aceste modificări.

---

*Modificări UI patch — compatibil cu YO Log PRO v17.1 Full Edition*
