# 📻 YO Log PRO v17.1 — Manual de Utilizare

**Logger Profesional Multi-Concurs pentru Radioamatori**  
Autor: **Ardei Constantin-Cătălin (YO8ACR)** · yo8acr@gmail.com  
Versiune document: **v17.1** · Limba: 🇷🇴 Română

---

## Cuprins

1. [Introducere](#1-introducere)
2. [Instalare](#2-instalare)
3. [Prima pornire — configurare inițială](#3-prima-pornire)
4. [Interfața principală](#4-interfața-principală)
5. [Logarea unui QSO](#5-logarea-unui-qso)
6. [Editarea și ștergerea QSO-urilor](#6-editarea-și-ștergerea-qso-urilor)
7. [Log Editor dedicat](#7-log-editor-dedicat)
8. [Căutare Callbook — radioamator.ro și QRZ.com](#8-căutare-callbook)
9. [Band Map](#9-band-map)
10. [DX Cluster](#10-dx-cluster)
11. [Scor Live](#11-scor-live)
12. [Statistici Rate QSO](#12-statistici-rate-qso)
13. [Control Radio CAT](#13-control-radio-cat)
14. [Manager Concursuri](#14-manager-concursuri)
15. [Export log](#15-export-log)
16. [Import log](#16-import-log)
17. [DXCC și cty.dat](#17-dxcc-și-ctydat)
18. [Teme și culori](#18-teme-și-culori)
19. [Setări generale](#19-setări-generale)
20. [Backup și recuperare](#20-backup-și-recuperare)
21. [Scurtături tastatură](#21-scurtături-tastatură)
22. [Structura fișierelor](#22-structura-fișierelor)
23. [Depanare](#23-depanare)
24. [Concursuri preconfigurate](#24-concursuri-preconfigurate)

---

## 1. Introducere

**YO Log PRO v17.1** este un logger de radioamator complet, gratuit și open-source, scris în Python. Este proiectat pentru participanții la concursurile de radioamatorism românești și internaționale, oferind toate instrumentele necesare pentru logare rapidă, scoring live, export Cabrillo/ADIF și control radio CAT.

**Caracteristici principale:**
- Rulează din un singur fișier `.py` sau ca `.exe` — fără instalare
- Compatibil cu **Windows 7, 8, 10, 11**, Linux și macOS
- Bilingv: interfață în **română** și **engleză** comutabilă live
- 7 concursuri românești și internaționale preconfigurate
- Editor de concursuri personalizat nelimitat
- Control CAT bidirecțional: Yaesu, Icom, Kenwood, Elecraft, Hamlib

---

## 2. Instalare

### 2.1 Varianta executabil Windows (recomandat)

1. Descarcă `YO_Log_PRO_v17.1.exe` din [Releases](../../releases/latest)
2. Pune fișierul într-un folder dedicat (ex: `C:\YOLog\`)
3. Dublu-click pentru pornire — **nu este necesară instalarea Python**

> ⚠️ **Windows 7:** Dacă apare eroarea "VCRUNTIME140.dll lipsește", instalează [Visual C++ 2015 Redistributable](https://www.microsoft.com/download/details.aspx?id=52685)

### 2.2 Varianta Python (cross-platform)

**Cerințe:**
- Python 3.6 sau mai nou (3.8 recomandat pentru Windows 7)
- `tkinter` — inclus pe Windows; pe Linux: `sudo apt install python3-tk`
- `pyserial` — opțional, pentru CAT

```bash
# Instalare pyserial (opțional)
pip install pyserial

# Pornire
python yo_log_pro_v171.py
```

**Windows 7 specific:** Descarcă Python 3.8.x de la [python.org](https://www.python.org/downloads/release/python-3810/) — aceasta este ultima versiune care suportă Windows 7.

---

## 3. Prima pornire

La prima pornire apare automat **dialogul de configurare inițială**. Completează:

| Câmp | Descriere | Exemplu |
|---|---|---|
| **Indicativ** | Indicativul tău de radioamator | `YO8ACR` |
| **Locator** | Locatorul Maidenhead (6 caractere) | `KN37` |
| **Județ** | Codul județului pentru concursuri YO | `NT` |
| **Adresă** | Adresa poștală (pentru Cabrillo) | `Targu Neamț` |
| **Operator** | Numele tău | `Ardei Constantin` |
| **Putere (W)** | Puterea de emisie | `100` |
| **Email** | Email (pentru export Cabrillo) | `yo8acr@gmail.com` |
| **Limbă** | Limba interfeței: `ro` sau `en` | `ro` |

Apasă **Salvează** — configurarea se stochează în `config.json`.

> Poți modifica oricând setările din **meniu → ⚙ Setări**.

---

## 4. Interfața principală

```
┌─────────────────────────────────────────────────────────────────┐
│ ● Online UTC  YO8ACR | Log Simplu | QSO: 0   [contest ▼] [ro▼] │  ← Header
│                                   UTC 14:32:15  ⚡45 QSO/h      │
├─────────────────────────────────────────────────────────────────┤
│  [Indicativ] [Freq kHz] [Bandă▼] [Mod▼] [RST S] [RST R] [Notă] │  ← Formular
│  🌐 Callbook                                                     │
│  □ Manual    [  LOG  ]  [Reset]   Dată: ...  Oră: ...  Cat▼     │
├─────────────────────────────────────────────────────────────────┤
│  Bandă: [Toate▼]  Mod: [Toate▼]              Σ QSO×Mult=Scor   │  ← Filtre
├─────────────────────────────────────────────────────────────────┤
│  Nr │ Indicativ │ Freq │ Bandă │ Mod │ RST │ Notă │ Țara │ ...  │  ← LOG
│   1 │ YO8ACR    │14200 │  20m  │ SSB │  59 │ KN37 │Romania│ ... │
│   2 │ DL5ABC    │14200 │  20m  │ SSB │  59 │ JO31 │Germany│ ... │
├─────────────────────────────────────────────────────────────────┤
│[Setări][Concursuri][CAT][Log Nou][Teme][Stats][Export]...       │  ← Butoane
└─────────────────────────────────────────────────────────────────┘
```

### 4.1 Header (bara de sus)
- **LED verde** = orologiu UTC online · **LED roșu** = offline
- **Indicativ + concurs activ + număr QSO** — se actualizează live
- **UTC** — ceas în timp real
- **⚡ QSO/h** — rata de QSO-uri pe ultima oră
- **CAT indicator** — afișează frecvența și modul citite de la radio
- **Selector concurs** — schimbă concursul activ (logul se salvează automat)
- **Selector limbă** — `ro` / `en`, schimbat live fără restart

### 4.2 Formularul de intrare
Câmpurile persistă între QSO-uri (frecvență, bandă, mod, RST). La logare se șterg doar **Indicativ** și **Notă**.

---

## 5. Logarea unui QSO

### Pași rapid:
1. Tastează **indicativul** în câmpul Call (se autoconverteste la majuscule)
2. Verifică/modifică **frecvența** (kHz) — banda se setează automat
3. Verifică **banda, modul, RST S, RST R**
4. Completează **Nota/Locatorul** dacă este necesar
5. Apasă **`Enter`** sau butonul **LOG**

### Detecție automată:
- **⚠ DUP** — apare roșu sub câmpul Call dacă indicativul este deja în log pe aceeași bandă și mod
- **ℹ Lucrat alt QRG** — galben, dacă indicativul a fost lucrat pe altă bandă/mod
- **✦ MULT NOU!** — flash auriu în bara de scor + beep la multiplicator nou

### Date/Oră:
- Implicit: **UTC automat** de la sistem
- Bifează **□ Manual** pentru a introduce data/ora manual (concursuri cu dată fixă)

### Seriale:
Dacă concursul folosește numere seriale (`use_serial: true`), câmpurile **Nr S** și **Nr R** apar automat. Nr S se incrementează automat la fiecare QSO.

---

## 6. Editarea și ștergerea QSO-urilor

### Din fereastra principală:
- **Dublu-click** pe un rând din log → se încarcă în formular pentru editare
- **Click dreapta** → meniu context: Editează / Șterge
- **Ctrl+Z** → undo ultimul QSO adăugat
- Butonul **LOG** devine **ACTUALIZEAZĂ** când ești în modul editare

### Undo:
Stiva de undo reține ultimele 50 de operații. Funcționează atât pentru adăugare cât și pentru ștergere.

---

## 7. Log Editor dedicat

**Deschidere:** Butonul `📝 Log Editor` din bara de jos sau meniu **📡 v17.1 → 📝 Editor Log dedicat**

Log Editor este o fereastră independentă, completă, concepută pentru editarea post-concurs sau corectura detaliată a logului.

### Funcționalități:

#### Filtrare
- **Filtru rapid** (text liber) — caută în indicativ și notă simultan
- **Filtru bandă** — Toate / 160m / 80m / ... / 23cm
- **Filtru mod** — Toate / SSB / CW / FT8 / ...
- Toate filtrele funcționează simultan, live (fără Enter)

#### Treeview
- **Toate coloanele** vizibile: Nr, Indicativ, Freq, Bandă, Mod, RST S, RST R, Nr S, Nr R, Notă, Țara, Dată, Oră, Puncte
- **Sortare** pe orice coloană — click pe header, click din nou inversează
- Colorare: roșu = duplicat, verde = multiplicator, albastru = stație specială
- Indicatorul de rezultate: `Afișat: X/Y QSO`

#### Editare
1. **Dublu-click** pe un rând → câmpurile formularului din partea de jos se completează
2. Modifici ce dorești
3. Apasă **💾 Actualizează**
4. Modificarea e salvată pe disk automat + backup creat

#### Adăugare QSO nou
- Completează formularul fără a selecta niciun rând din treeview
- Apasă **💾 Salvează** — QSO-ul se adaugă la începutul logului

#### Undo local
- Butonul **↩ Undo** anulează ultima operație (adăugare, ștergere sau modificare)
- Stivă locală de 50 operații, independentă de undo-ul ferestrei principale

#### Meniu context (clic dreapta)
- **✏ Editează** — încarcă QSO în formular
- **🗑 Șterge** — șterge cu confirmare
- **🌐 Callbook** — deschide Callbook Lookup pentru indicativul selectat
- **📋 Copiază call** — copiază indicativul în clipboard
- **🔗 QRZ.com** — deschide pagina QRZ în browser
- **🔗 radioamator.ro** — deschide pagina callbook în browser

#### Sincronizare
Orice modificare din Log Editor se reflectă **instant** în fereastra principală și invers.

---

## 8. Căutare Callbook

**Deschidere:**
- Butonul `🌐 Callbook` din bara de jos a ferestrei principale
- Butonul mic `🌐` de sub câmpul Indicativ din formular
- Meniu **📡 v17.1 → 🌐 Callbook Lookup**
- Clic dreapta în Log Editor → **🌐 Callbook**

### Surse de date:

#### radioamator.ro
Baza de date națională a radioamatorilor din România. Conține:
- Nume complet
- QTH (localitate, județ)
- Locator Maidenhead
- Clasă de licență (A, B, C)
- Data expirării autorizației
- Zona ITU și CQ

#### QRZ.com
Baza de date internațională. Extrage din pagina publică (fără cont necessar):
- Nume
- QTH
- Locator (grid square)
- DXCC
- Zone ITU / CQ

### Utilizare:
1. Introduci indicativul în câmpul de căutare
2. Selectezi sursa: `radioamator.ro` sau `QRZ.com`
3. Apesi **🔍 Caută** sau `Enter`
4. Rezultatele apar în câmpurile de mai jos în câteva secunde
5. **✅ Folosește locatorul** → copiază automat locatorul în câmpul Notă din formular — util pentru concursuri VHF
6. **🌐 Deschide browser** → deschide pagina completă în browser

> **Notă:** Căutarea se face pe internet. Necesită conexiune activă. Căutarea rulează în fundal (thread separat) — interfața rămâne responsivă.

---

## 9. Band Map

**Deschidere:** Meniu **📡 v17.1 → 📡 Band Map**

Harta benzilor afișează activitatea QSO-urilor tale grupate pe fiecare bandă radioamatoristică.

### Cum se citește:
- Fiecare **coloană** = o bandă (160m, 80m, ..., 23cm)
- **Header colorat** al coloanei = culoarea specifică benzii
- **Numărul de QSO-uri** pe bandă
- Lista QSO-urilor recente per bandă (max 20 cele mai recente)
- **QSO-urile DX** (altă țară) sunt afișate cu **culoare cyan**
- Dacă ai locator completat în Setări, se afișează distanța în km

### Refresh:
- Automat la fiecare **30 de secunde**
- Manual cu butonul **↺ Refresh**

### Bara de statistici (jos):
`Total QSO: X | DXCC: Y | Benzi active: Z | Ultimul refresh: HH:MM:SS UTC`

---

## 10. DX Cluster

**Deschidere:** Meniu **📡 v17.1 → 📡 DX Cluster**

Client DX Cluster integrat cu conexiune telnet la clustere de radioamatori.

### Clustere preconfigurate:
- `dxc.yo8acr.ro:7300`
- `cluster.dl9gtb.de:7300`
- `dx.db0sue.de:7300`
- `www.dxsummit.fi:7300`
- `gb7mbc.spoo.org:7300`

Poți adăuga orice cluster în format `hostname:port`.

### Conectare:
1. Selectează un cluster din lista derulantă (sau tastează manual `host:port`)
2. Introdu **indicativul tău** în câmpul Call
3. Apasă **▶ Conectare**
4. Starea conexiunii apare în colțul din dreapta sus al ferestrei

### Spoturi DX:
- Tabelul central afișează spoturi cu: UTC, DX Call, Frecvență, Bandă, Mod, Țara, Comment, Spotter
- **DX-urile** (entități diferite) sunt marcate cu culoare specială

### Filtrare spoturi:
- **Filtru bandă** — afișează numai spoturi pe banda selectată
- **Filtru call** — caută în DX Call și Spotter simultan

### Click-to-Log:
**Dublu-click pe un spot** → indicativul și frecvența se completează automat în formularul ferestrei principale! Merge direct la logare.

### Fereastra Raw:
Afișează toate mesajele brute primite de la cluster (inclusiv anunțuri, WWV, etc.)

### Trimitere comenzi:
Câmpul de jos + butonul **Trimite** (sau `Enter`) permite trimiterea comenzilor direct la cluster:
- `SH/DX 20` — ultimele 20 de spoturi
- `SH/DX ON 20m` — spoturi pe 20m
- `SET/FILTER` — filtre server-side
- `BYE` — deconectare

---

## 11. Scor Live

**Deschidere:** Meniu **📡 v17.1 → 📊 Scor Live**

Panou dedicat cu scorul concursului actualizat în timp real.

### Informații afișate:
| Câmp | Descriere |
|---|---|
| **SCOR TOTAL** | Cifra mare centrală — scor complet (QSO × multiplicatori) |
| **Total QSO** | Numărul de QSO-uri din log |
| **Puncte QSO** | Suma punctelor QSO (înainte de multiplicatori) |
| **Multiplicatori** | Numărul de multiplicatori unici |
| **DXCC** | Entități DXCC distincte lucrate |
| **QSO/h (1h)** | Rate pe ultima oră completă |
| **QSO/h (10min)** | Rate pe ultimele 10 minute × 6 (proiectat/oră) |
| **Indicative unice** | Indicative distincte în log |
| **Țări lucrate** | Număr de țări distincte |

### Grafic per bandă:
Progress bars pentru fiecare bandă activă, proporționale cu numărul de QSO-uri.

### Refresh:
- Automat la **15 secunde**
- Manual cu butonul **↺ Refresh**

---

## 12. Statistici Rate QSO

**Deschidere:** Meniu **📡 v17.1 → 📈 Rate QSO Stats**

### Grafic QSO/h:
- Bar chart cu QSO-uri per oră pentru ultimele **24 de ore**
- Bara cu maximum este colorată diferit (cyan)
- Valoarea numerică afișată deasupra fiecărei bare
- Gridlines cu valori pe axa Y

### Tabel Top DXCC:
Top 20 entități DXCC lucrate, ordonate descrescător.

### Tabel Per Bandă:
Distribuție QSO-uri pe benzi cu procentaj din total.

### Statistici jos:
- Total QSO, Indicative unice, DXCC, Rate 1h, Interval ultimul QSO, Banda cea mai activă

### Refresh:
Automat la **60 de secunde**.

---

## 13. Control Radio CAT

**Configurare:** Meniu **CAT → Setări CAT**

### Protocoale suportate:

| Protocol | Radio-uri compatibile |
|---|---|
| **Yaesu CAT** | FT-817, FT-857, FT-897, FT-991, FT-DX101, FT-710, FT-5D... |
| **Icom CI-V** | IC-706, IC-718, IC-7200, IC-7300, IC-7610, IC-9700, IC-705... |
| **Kenwood CAT** | TS-480, TS-590, TS-850, TS-2000, TS-990... |
| **Elecraft CAT** | K3, K3S, KX3, KX2, K4... |
| **Hamlib/rigctld** | Orice radio suportat de Hamlib prin rigctld |
| **Manual** | Fără CAT — introducere manuală |

### Configurare Yaesu/Icom/Kenwood/Elecraft:
1. Conectează cablul CAT (COM/USB-serial)
2. Meniu **CAT → Setări CAT**
3. Selectează **protocolul** și **portul COM**
4. Setează **baud rate** (default per protocol)
5. Apasă **Test conexiune** — ar trebui să apară frecvența curentă
6. Bifează **✓ Activează CAT la pornire**

### Configurare Hamlib/rigctld:
1. Pornește rigctld: `rigctld -m MODEL -r PORT -s BAUD`
   - Ex: `rigctld -m 122 -r /dev/ttyUSB0 -s 19200` (Icom IC-706)
2. În YO Log PRO: Protocol = **Hamlib/rigctld**, Host = `localhost`, Port = `4532`

### Funcționare după conectare:
- **Frecvența** și **modul** se actualizează automat în formularul de logare la fiecare 2 secunde
- Indicatorul **CAT** din header afișează frecvența și modul curent
- Când modifici frecvența în câmpul Freq și apeși `Enter`, aceasta se **trimite spre radio**

### Portul CI-V pentru Icom:
Adresa hexadecimală a radioului (default `94`). Verifică în meniu-ul radioului tău (ex: IC-7300: `98`).

---

## 14. Manager Concursuri

**Deschidere:** Butonul **Concursuri** sau meniu **Concursuri**

### Adăugare concurs nou:
1. Click **➕ Adaugă**
2. Completează câmpurile:
   - **ID** — identificator unic (ex: `yo-hf-2025`), fără spații
   - **Nume RO / EN** — numele afișat în interfață
   - **Tip** — Simplu, Maraton, Stafeta, DX, VHF, Field Day etc.
   - **Sistem punctare** — none / per_qso / per_band / maraton / multiplicator / distanță
   - **Puncte/QSO** — valoarea per QSO
   - **Format Exchange** — none / county / grid / serial / zone
   - **Multiplicatori** — none / county / dxcc / band / grid
   - **Benzi permise** — bifează benzile valide
   - **Moduri permise** — bifează modurile valide
   - **Categorii** — o categorie per linie (ex: `Individual`, `Club`, `YL`)
   - **Stații obligatorii** — indicative pe câte o linie (vor fi marcate în log)
   - **Punctare specială** — `CALL=puncte` per linie (ex: `YO8KRR=10`)
   - **Puncte per bandă** — `BAND=puncte` per linie (ex: `20m=2`)

3. Click **Salvează**

### Duplicare concurs:
Click **📋 Duplică** pe un concurs existent — creează o copie cu sufixul `-copy` pe care o poți modifica.

### Export/Import concursuri JSON:
Poți exporta și importa definiții de concursuri în format JSON pentru a le partaja cu alți utilizatori YO Log PRO.

---

## 15. Export log

**Deschidere:** Butonul **Export** sau meniu **Export**

### Formate disponibile:

#### Cabrillo 2.0 (.log)
Format standard pentru trimiterea logurilor la organizatori de concursuri.
- Dialog de configurare Exchange (ce se trimite / ce se primește)
- **Preview** înainte de salvare
- Validare automată a logului înainte de export

**Configurare Exchange Trimis:**
- `Județ` — trimite codul județului tău
- `Locator` — trimite locatorul tău Maidenhead
- `Nr. Serial` — trimite numărul serial al QSO-ului
- `Nimic (--)` — pentru concursuri fără exchange

**Configurare Exchange Primit:**
- `Din log` — preia din câmpul Notă sau Nr Serial al QSO-ului
- `Nimic (--)` — nu exportă exchange primit

#### ADIF 3.1 (.adi)
Format universal pentru import în alte programe (DXKeeper, Logger32, Ham Radio Deluxe, etc.)

#### EDI (.edi)
Format REG1TEST pentru concursurile VHF europene (IARU, VERON, etc.)

#### CSV (.csv)
Format tabular pentru analiză în Excel sau LibreOffice Calc.

#### Print (.txt)
Raport text formatat, printabil sau trimis prin email.

---

## 16. Import log

**Deschidere:** Butonul **Import** sau meniu **Utilități → Import**

### Formate suportate:
- **ADIF** (.adi, .adif) — din orice alt program de logging
- **Cabrillo 2.0** (.log) — inclusiv loguri generate de alte programe
- **Cabrillo 3.0** (.log)
- **CSV** (.csv) — cu header: Call,Band,Mode,Date,Time,RST_S,RST_R,Note

> ⚠️ La import, QSO-urile noi se adaugă la logul curent (nu se suprascrie).

---

## 17. DXCC și cty.dat

### Baza de date internă
YO Log PRO include o bază de date DXCC cu prefixe pentru ~150 de entități, actualizată manual. Aceasta este suficientă pentru concursurile românești și europene comune.

### BigCTY extern (recomandat pentru DX)
Pentru o bază de date completă cu toate entitățile DXCC:
1. Descarcă `cty.dat` de la [country-files.com](https://www.country-files.com/)
2. Meniu **📡 v17.1 → 📂 Încarcă cty.dat**
3. Selectează fișierul `cty.dat` descărcat
4. Confirmă — prefixele se adaugă la baza internă

> Baza de date se resetează la cea internă la repornire. Pentru a folosi mereu BigCTY, pune `cty.dat` în același folder cu aplicația — se va încărca automat.

---

## 18. Teme și culori

**Deschidere:** Butonul **🎨 Teme** sau meniu **Teme**

### Teme preconfigurate:
- **Dark Blue (implicit)** — tema standard, albastru întunecat
- **Dark Green** — verde întunecat, stil CW/old school
- **Dark Red** — roșu întunecat
- **Dark Purple** — mov întunecat
- **Light (Zi)** — fundal deschis pentru utilizare la lumina zilei
- **Light Sepia** — sepia cald, confort vizual ridicat

### Aplicare rapidă din meniu:
Meniu **Teme** → alege direct o temă fără a deschide editorul.

### Editor de culori personalizate:
- Selectează o temă de bază
- Modifică culorile individuale: Fundal, Text, Accent, Câmpuri, Header, Clock/Score, OK, Eroare, Avertisment
- **Dublu-click** pe o culoare sau pe swatch-ul colorat → deschide color picker
- **✅ Salvează** → tema se aplică și se salvează în `config.json`

---

## 19. Setări generale

**Deschidere:** Butonul **⚙ Setări**

| Câmp | Descriere |
|---|---|
| Indicativ | Indicativul stației tale |
| Locator | Locatorul Maidenhead (ex: `KN37MB`) |
| Județ | Codul județului pentru exchange |
| Adresă | Adresa poștală completă |
| Operator | Numele operatorului |
| Putere (W) | Puterea de emisie în wați |
| Email | Email pentru export Cabrillo |
| Soapbox | Mesaj liber pentru Cabrillo |
| Limbă | `ro` / `en` |
| Font | Dimensiunea fontului (9-14) |
| Sunete | Activează/dezactivează alertele sonore |
| CAT | Setările de control radio |

---

## 20. Backup și recuperare

### Backup automat:
- La fiecare ieșire normală din program
- La fiecare export Cabrillo (înainte de export)
- Butonul **💾 Backup** din bara de butoane

### Locație backup:
Folderul `backups/` în același director cu aplicația.  
Format: `log_CONTESTID_YYYYMMDD_HHMMSS.json`  
Se păstrează ultimele **50 de backup-uri** per concurs.

### Recuperare backup:
1. Deschide folderul `backups/`
2. Găsește fișierul backup dorit
3. Copiază-l peste fișierul `log_CONTESTID.json` din directorul principal
4. Repornește aplicația

### Verificare integritate log:
Meniu **Utilități → Verificare log** — verifică hash MD5 al logului și afișează numărul de QSO-uri.

---

## 21. Scurtături tastatură

| Tastă | Acțiune |
|---|---|
| `Enter` | Adaugă / Actualizează QSO |
| `Ctrl+S` | Salvare manuală log |
| `Ctrl+Z` | Undo ultimul QSO |
| `Ctrl+F` | Deschide căutare în log |
| `F2` | Trece la banda următoare (ciclic) |
| `F3` | Trece la modul următor (ciclic) |
| `Double-Click` pe QSO | Editare QSO selectat |
| `Delete` (în Log Editor) | Șterge QSO selectat |

---

## 22. Structura fișierelor

```
📁 Directorul aplicației/
│
├── yo_log_pro_v171.py       ← Aplicația principală
│   sau YO_Log_PRO_v17.1.exe
│
├── config.json              ← Configurarea ta (creat automat)
├── contests.json            ← Definiții concursuri (creat automat)
│
├── log_simplu.json          ← Logul concursului "simplu"
├── log_maraton.json         ← Logul concursului "maraton"
├── log_yo-dx-hf.json        ← Logul concursului "yo-dx-hf"
├── log_[id].json            ← Un fișier per concurs activ
│
├── cty.dat                  ← (opțional) BigCTY database extern
│
└── 📁 backups/
    ├── log_simplu_20250306_143215.json
    ├── log_simplu_20250307_092011.json
    └── ...
```

> **Important:** Pune aplicația într-un folder în care ai drepturi de scriere (ex: `Documents\YOLog\`, **nu** în `C:\Program Files\`).

---

## 23. Depanare

### Aplicația nu pornește (Windows)
- **"Python nu este recunoscut"** → Python nu e în PATH; reinstalează cu bifă "Add to PATH"
- **"VCRUNTIME140.dll lipsește"** → Instalează Visual C++ 2015 Redistributable
- **"No module named tkinter"** → Pe Linux: `sudo apt install python3-tk`

### CAT nu funcționează
- Verifică că portul COM este corect și liber (nu folosit de alt program)
- Verifică baud rate — trebuie să coincidă cu setarea din radio
- Windows: verifică în Device Manager că portul apare și nu are erori (!)
- Încearcă să **dezactivezi** și **reactivezi** CAT din meniu
- Icom CI-V: verifică adresa CI-V a radioului (meniu radio → CI-V Address)

### Nu găsesc portul COM (Windows 7)
- Instalează driverele USB-Serial (FTDI sau Silicon Labs) pentru cablul tău CAT
- Repornește computerul după instalarea driverelor

### DX Cluster nu se conectează
- Verifică conexiunea la internet
- Unele clustere au perioadă de inactivitate; încearcă alt cluster din listă
- Verifică că portul 7300 nu este blocat de firewall

### Callbook nu găsește indicativul
- Indicativul poate să nu fie înregistrat pe sursa selectată
- Încearcă cealaltă sursă (radioamator.ro vs QRZ.com)
- Verifică conexiunea la internet
- Unele indicative sunt accesibile numai cu cont QRZ.com (pagini premium)

### Scorul nu se calculează
- Verifică că ai selectat un concurs cu sistem de punctare (nu "Log Simplu")
- Verifică setările concursului: `scoring_mode` trebuie să fie altceva decât `none`

### Logul s-a corupt / pierdut
- Verifică folderul `backups/` și restaurează ultimul backup valid
- Nu șterge manual fișierele `.json` în timp ce aplicația rulează

---

## 24. Concursuri preconfigurate

### Log Simplu (`simplu`)
Log general, fără reguli de concurs. Ideal pentru activitate curentă, SOTA, POTA.
- Toate benzile și modurile permise
- Fără punctare

### Maraton Ion Creangă (`maraton`)
- Categorii: Seniori YO, YL, Juniori, Club, DX, Receptori
- Punctare: maraton (stații speciale cu punctaj diferit)
- Multiplicatori: județe YO
- Exchange: județ

### Ștafetă (`stafeta`)
- 2 puncte/QSO
- Număr serial obligatoriu
- Multiplicatori: județe YO
- Exchange: județ + serial

### YO DX HF Contest (`yo-dx-hf`)
- Puncte per bandă: 160m=4, 80m=3, 40m=2, 20m=1, 15m=1, 10m=2
- Multiplicatori: DXCC
- Exchange: județ YO + serial

### YO VHF Contest (`yo-vhf`)
- Punctare pe distanță km
- Multiplicatori: grilă Maidenhead
- Benzi: 6m, 2m, 70cm, 23cm
- Exchange: locator

### Field Day (`field-day`)
- 2 puncte/QSO
- Categorii: 1A, 2A, 3A, 1B, 2B

### Sprint (`sprint`)
- 1 punct/QSO
- Număr serial obligatoriu
- Benzi: 40m, 20m, 15m, 10m
- Moduri: SSB, CW

---

*Manual actualizat pentru versiunea v17.1*  
*Autor: YO8ACR | yo8acr@gmail.com*  
*73! 📻*
