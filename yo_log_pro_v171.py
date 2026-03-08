#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Log PRO v17.1 — Full Edition | Professional Multi-Contest Amateur Radio Logger
Developed by: Ardei Constantin-Cătălin (YO8ACR)
Email: yo8acr@gmail.com
Compatible: Python 2.7+ / Python 3.x | Windows 7, 8, 10, 11 | Linux | macOS

CHANGELOG v17.1:
- ADDED: Log Editor dedicat — fereastră separată cu editare completă, filtrare, undo, callbook
- ADDED: Callbook Lookup — căutare radioamator.ro și QRZ.com cu extragere date
- ADDED: Band Map visual (harta benzilor cu activitate in timp real)
- ADDED: DXCC database cty.dat loader (suport extern + fallback intern)
- ADDED: Live contest score panel cu QSO/h rate in timp real
- ADDED: Multiplier audio alert (beep + popup la multiplicator nou)
- ADDED: DX Cluster GUI integrat (telnet cluster, filtrare, click-to-log)
- ADDED: QSO Rate statistics (grafic QSO/h pe ore)
- ADDED: Full CAT radio control (frecventa bidirectionala, mod bidirectional)
- FIXED: Compatibilitate Windows 7 (ttk.Style, font fallback, encoding)
- FIXED: Frequency, band, mode and RST persist between QSOs (only call and note clear)

CHANGELOG v17.0:
- FIXED: Frequency, band, mode and RST persist between QSOs (only call and note clear)
- Keep all operating parameters until manually changed

CHANGELOG v16.x:
- ADDED: Cabrillo 2.0 export with configurable exchange dialog
- ADDED: Exchange options: County/Grid/Serial/None for sent, Log/None for received
- ADDED: Preview dialog before Cabrillo export
- ADDED: Import Cabrillo 2.0 and 3.0 formats
- ADDED: cabrillo_name field in contest editor
- ADDED: exchange_format field per contest
- ADDED: Email and Soapbox fields in settings
- ADDED: Validation + auto-backup before export
- ADDED: Save dialog for all exports
"""

import os, sys, re, csv, copy, json, math, datetime, io, hashlib
try:
    from pathlib import Path
except ImportError:
    import glob as _glob
    class Path(object):
        def __init__(self, p): self._p = str(p)
        def glob(self, pat): return [Path(f) for f in _glob.glob(os.path.join(self._p, pat))]
        def unlink(self): os.remove(self._p)
        def __str__(self): return self._p

from collections import Counter, deque
import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog, scrolledtext
import threading, socket, time
try:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode, quote_plus
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError
    from urllib import urlencode, quote_plus
import webbrowser

# ─── Windows 7 DPI fix ───
try:
    if sys.platform == "win32":
        import ctypes
        try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try: ctypes.windll.user32.SetProcessDPIAware()
            except Exception: pass
except Exception: pass

# ─── CAT: optional pyserial ───
try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

try:
    if sys.platform == "win32":
        import winsound; HAS_SOUND = True
    else: HAS_SOUND = False
except ImportError: HAS_SOUND = False

def get_data_dir():
    if getattr(sys,'frozen',False): return os.path.dirname(sys.executable)
    return os.path.abspath(".")

def beep(kind="info"):
    if not HAS_SOUND: return
    try: winsound.MessageBeep({"error":0x10,"warning":0x30,"success":0x40,"info":0x0}.get(kind,0x0))
    except: pass

def center_dialog(dialog, parent=None):
    dialog.update_idletasks()
    m = re.match(r'(\d+)x(\d+)', dialog.geometry())
    dw, dh = (int(m.group(1)), int(m.group(2))) if m else (dialog.winfo_reqwidth(), dialog.winfo_reqheight())
    if parent and parent.winfo_exists():
        x = parent.winfo_rootx() + (parent.winfo_width()-dw)//2
        y = parent.winfo_rooty() + (parent.winfo_height()-dh)//2
    else:
        x = (dialog.winfo_screenwidth()-dw)//2; y = (dialog.winfo_screenheight()-dh)//2
    dialog.geometry(f"{dw}x{dh}+{max(0,x)}+{max(0,y)}")

class Loc:
    @staticmethod
    def to_latlon(loc):
        loc = loc.upper().strip()
        if len(loc)<4: return None,None
        try:
            lon = (ord(loc[0])-65)*20-180; lat = (ord(loc[1])-65)*10-90
            lon += int(loc[2])*2; lat += int(loc[3])
            if len(loc)>=6: lon += (ord(loc[4])-65)*(2/24)+1/24; lat += (ord(loc[5])-65)*(1/24)+0.5/24
            else: lon += 1.0; lat += 0.5
            return lat, lon
        except: return None, None

    @staticmethod
    def dist(a, b):
        la1,lo1 = Loc.to_latlon(a); la2,lo2 = Loc.to_latlon(b)
        if None in (la1,lo1,la2,lo2): return 0
        d1=math.radians(la2-la1); d2=math.radians(lo2-lo1)
        a_=math.sin(d1/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(d2/2)**2
        return round(6371.0*2*math.atan2(math.sqrt(a_),math.sqrt(1-a_)),1)

    @staticmethod
    def valid(s):
        s = s.upper().strip()
        if len(s)==4: return s[0:2].isalpha() and s[2:4].isdigit() and 'A'<=s[0]<='R' and 'A'<=s[1]<='R'
        if len(s)==6: return s[0:2].isalpha() and s[2:4].isdigit() and s[4:6].isalpha() and 'A'<=s[0]<='R' and 'A'<=s[1]<='R' and 'A'<=s[4]<='X' and 'A'<=s[5]<='X'
        return False

class DXCC:
    DB = {
        "YO":"Romania","YP":"Romania","YQ":"Romania","YR":"Romania",
        "DL":"Germany","DJ":"Germany","DK":"Germany","DA":"Germany","DB":"Germany","DC":"Germany","DD":"Germany","DF":"Germany","DG":"Germany","DH":"Germany","DM":"Germany",
        "G":"England","M":"England","2E":"England","GW":"Wales","GM":"Scotland","GI":"N. Ireland","GD":"Isle of Man","GJ":"Jersey","GU":"Guernsey",
        "F":"France","TM":"France","HB9":"Switzerland","HB":"Switzerland",
        "I":"Italy","IK":"Italy","IZ":"Italy","IW":"Italy","IN3":"Italy",
        "EA":"Spain","EB":"Spain","EC":"Spain","EE":"Spain","CT":"Portugal","CS":"Portugal","CU":"Azores",
        "SP":"Poland","SQ":"Poland","SN":"Poland","SO":"Poland","3Z":"Poland",
        "HA":"Hungary","HG":"Hungary","OK":"Czech Rep.","OL":"Czech Rep.","OM":"Slovak Rep.","LZ":"Bulgaria",
        "UR":"Ukraine","US":"Ukraine","UT":"Ukraine","UX":"Ukraine","UY":"Ukraine",
        "UA":"Russia","RU":"Russia","RV":"Russia","RW":"Russia","RA":"Russia","OE":"Austria",
        "ON":"Belgium","OO":"Belgium","OR":"Belgium","OT":"Belgium",
        "PA":"Netherlands","PB":"Netherlands","PD":"Netherlands","PE":"Netherlands",
        "OZ":"Denmark","OU":"Denmark","5Q":"Denmark",
        "SM":"Sweden","SA":"Sweden","SB":"Sweden","SK":"Sweden",
        "LA":"Norway","LB":"Norway","LC":"Norway",
        "OH":"Finland","OF":"Finland","OG":"Finland","OI":"Finland",
        "ES":"Estonia","YL":"Latvia","LY":"Lithuania",
        "9A":"Croatia","S5":"Slovenia","E7":"Bosnia","Z3":"N. Macedonia","Z6":"Kosovo","ZA":"Albania",
        "SV":"Greece","SW":"Greece","SX":"Greece","SY":"Greece",
        "TA":"Turkey","TC":"Turkey","YM":"Turkey","4X":"Israel","4Z":"Israel",
        "SU":"Egypt","CN":"Morocco","7X":"Algeria","3V":"Tunisia",
        "ZS":"South Africa","ZR":"South Africa","ZU":"South Africa",
        "W":"USA","K":"USA","N":"USA","AA":"USA","AB":"USA","AC":"USA","AD":"USA","AE":"USA","AF":"USA","AG":"USA","AI":"USA","AK":"USA",
        "KH6":"Hawaii","KL7":"Alaska","KP4":"Puerto Rico",
        "VE":"Canada","VA":"Canada","VY":"Canada","VO":"Canada",
        "XE":"Mexico","XA":"Mexico","4A":"Mexico",
        "PY":"Brazil","PP":"Brazil","PR":"Brazil","PS":"Brazil","PT":"Brazil","PU":"Brazil",
        "LU":"Argentina","LW":"Argentina","LO":"Argentina","CE":"Chile","CA":"Chile","XQ":"Chile",
        "JA":"Japan","JH":"Japan","JR":"Japan","JE":"Japan","JF":"Japan","JG":"Japan","JI":"Japan","JJ":"Japan","JK":"Japan","JL":"Japan",
        "BY":"China","BA":"China","BD":"China","BG":"China","BI":"China",
        "HL":"S. Korea","DS":"S. Korea","6K":"S. Korea","DU":"Philippines","DX":"Philippines",
        "HS":"Thailand","E2":"Thailand","VK":"Australia","AX":"Australia","ZL":"New Zealand","ZM":"New Zealand",
        "VU":"India","AT":"India","VT":"India","AP":"Pakistan",
        "A4":"Oman","A6":"UAE","A7":"Qatar","A9":"Bahrain","9K":"Kuwait","HZ":"Saudi Arabia","7Z":"Saudi Arabia",
        "EK":"Armenia","4J":"Azerbaijan","4L":"Georgia","UN":"Kazakhstan","JT":"Mongolia",
        "XV":"Vietnam","3W":"Vietnam","TF":"Iceland","JW":"Svalbard","OX":"Greenland","OY":"Faroe Is.",
        "T7":"San Marino","3A":"Monaco","C3":"Andorra","HV":"Vatican","9H":"Malta","5B":"Cyprus","4O":"Montenegro",
    }
    @staticmethod
    def lookup(call):
        call = call.upper().strip().split("/")[0]
        for n in range(min(4,len(call)),0,-1):
            if call[:n] in DXCC.DB: return DXCC.DB[call[:n]], call[:n]
        if call and call[0] in DXCC.DB: return DXCC.DB[call[0]], call[0]
        return "Unknown", call[:2] if len(call)>=2 else call
    @staticmethod
    def prefix(call): return DXCC.lookup(call)[1]

    @staticmethod
    def load_cty_dat(filepath):
        """Încarcă cty.dat (BigCTY format) și adaugă prefixele în DXCC.DB"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            current_entity = None
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'): continue
                if not line.startswith(' ') and ':' in line:
                    # Linie entitate: Romania: EU  28  274  E6  20.8 ...
                    parts = [p.strip() for p in line.split(':')]
                    if len(parts) >= 1: current_entity = parts[0].strip()
                elif line.startswith(' ') and current_entity:
                    # Linie prefixe
                    prefixes = [p.strip().rstrip(',;').lstrip('=*') for p in line.split(',')]
                    for pfx in prefixes:
                        if pfx and pfx.replace('/','').isalnum():
                            DXCC.DB[pfx.upper()] = current_entity
            return True, f"CTY loaded: {filepath}"
        except Exception as e:
            return False, str(e)

FREQ_MAP = {(1800,2000):"160m",(3500,3800):"80m",(5351,5367):"60m",(7000,7200):"40m",(10100,10150):"30m",(14000,14350):"20m",(18068,18168):"17m",(21000,21450):"15m",(24890,24990):"12m",(28000,29700):"10m",(50000,54000):"6m",(144000,148000):"2m",(430000,440000):"70cm",(1240000,1300000):"23cm"}
BAND_FREQ = {"160m":1850,"80m":3700,"60m":5355,"40m":7100,"30m":10120,"20m":14200,"17m":18120,"15m":21200,"12m":24940,"10m":28500,"6m":50150,"2m":145000,"70cm":432200,"23cm":1296200}
RST_DEFAULTS = {"SSB":"59","AM":"59","FM":"59","SSTV":"59","CW":"599","RTTY":"599","PSK31":"599","DIGI":"599","FT8":"-10","FT4":"-10","JT65":"-15"}
CAB2_MODE_MAP = {"SSB":"PH","AM":"PH","FM":"PH","SSTV":"PH","CW":"CW","RTTY":"RY","PSK31":"RY","FT8":"DG","FT4":"DG","JT65":"DG","DIGI":"DG"}
CAB2_MODE_REV = {"PH":"SSB","CW":"CW","RY":"RTTY","DG":"FT8"}

def freq2band(f):
    try:
        f = float(f)
        for (lo,hi),b in FREQ_MAP.items():
            if lo<=f<=hi: return b
    except: pass
    return None

BANDS_HF = ["160m","80m","60m","40m","30m","20m","17m","15m","12m","10m"]
BANDS_VHF = ["6m","2m"]; BANDS_UHF = ["70cm","23cm"]; BANDS_ALL = BANDS_HF+BANDS_VHF+BANDS_UHF
MODES_ALL = ["SSB","CW","DIGI","FT8","FT4","RTTY","AM","FM","PSK31","SSTV","JT65"]
SCORING_MODES = ["none","per_qso","per_band","maraton","multiplier","distance","custom"]
EXCHANGE_FORMATS = ["none","county","grid","serial","zone","custom"]
CONTEST_TYPES = ["Simplu","Maraton","Stafeta","YO","DX","VHF","UHF","Field Day","Sprint","QSO Party","SOTA","POTA","Custom"]
YO_COUNTIES = ["AB","AR","AG","BC","BH","BN","BT","BV","BR","BZ","CS","CL","CJ","CT","CV","DB","DJ","GL","GR","GJ","HR","HD","IL","IS","IF","MM","MH","MS","NT","OT","PH","SM","SJ","SB","SV","TR","TM","TL","VS","VL","VN","B"]

EXCH_SENT_OPTIONS = {
    "ro": {"county":"Județ ({jud})","grid":"Locator ({loc})","serial":"Nr. Serial","none":"Nimic (--)"},
    "en": {"county":"County ({jud})","grid":"Locator ({loc})","serial":"Serial Nr.","none":"None (--)"}
}
EXCH_RCVD_OPTIONS = {
    "ro": {"log":"Din log (notă/serial)","none":"Nimic (--)"},
    "en": {"log":"From log (note/serial)","none":"None (--)"}
}

T = {
    "ro": {
        "app_title":"YO Log PRO v17.1","call":"Indicativ","band":"Bandă","mode":"Mod",
        "rst_s":"RST S","rst_r":"RST R","serial_s":"Nr S","serial_r":"Nr R",
        "freq":"Frecv (kHz)","note":"Notă/Locator","log":"LOG","update":"ACTUALIZEAZĂ",
        "search":"🔍 Caută","reset":"Reset","settings":"⚙ Setări",
        "stats":"📊 Statistici","validate":"✅ Validează","export":"📤 Export",
        "import_log":"📥 Import","delete":"Șterge","backup":"💾 Backup",
        "online":"Online UTC","offline":"Manual","category":"Categorie","county":"Județ",
        "req_st":"Stații Obligatorii","worked":"Stații Lucrate","total_score":"Scor Total",
        "val_result":"Validare","date_l":"Dată:","time_l":"Oră:","manual":"Manual",
        "confirm_del":"Confirmare","confirm_del_t":"Sigur ștergeți?",
        "bak_ok":"Backup creat!","bak_err":"Eroare backup!",
        "exit_t":"Ieșire","exit_m":"Salvați înainte de ieșire?",
        "help":"Ajutor","about":"Despre","save":"Salvează","close":"Închide",
        "credits":"Dezvoltat de:\nArdei Constantin-Cătălin (YO8ACR)\nyo8acr@gmail.com",
        "usage":"Ctrl+F=Caută  Ctrl+Z=Undo  Ctrl+S=Save  F2=Bandă+  F3=Mod+  Enter=LOG",
        "edit_qso":"Editează","delete_qso":"Șterge","data":"Data","ora":"Ora",
        "sel_fmt":"Format:","cancel":"Anulează","exp_ok":"Export reușit!","error":"Eroare",
        "sett_ok":"Setări salvate!","locator":"Locator:","address":"Adresă:",
        "font_size":"Font:","station_info":"Info Stație:",
        "contest_mgr":"Manager Concursuri","contests":"Concursuri",
        "add_c":"➕ Adaugă","edit_c":"✏ Editează","del_c":"🗑 Șterge",
        "dup_c":"📋 Duplică","exp_c":"📤 Export JSON","imp_c":"📥 Import JSON",
        "c_name":"Nume Concurs:","c_type":"Tip:","sc_mode":"Punctare:",
        "cats":"Categorii (o linie):","a_bands":"Benzi permise:","a_modes":"Moduri permise:",
        "req_st_c":"Stații Obligatorii (o linie):","sp_sc":"Punctare Specială (CALL=PTS):",
        "ppq":"Puncte/QSO:","min_qso":"Min QSO:","use_serial":"Nr. Seriale",
        "use_county":"Județ","county_list":"Județe (virgulă):","no_sel":"Neselectat!",
        "del_c_conf":"Ștergeți '{}'?","c_saved":"Salvat!","c_del":"Șters!",
        "c_exists":"ID existent!","c_default":"Protejat!","c_id":"ID Concurs:",
        "mults":"Multiplicatori:","band_pts":"Puncte/Bandă (BAND=PTS):",
        "nr":"Nr.","pts":"Pt",
        "dup_warn":"⚠ Duplicat!","dup_msg":"{} pe {} {}!\nQSO #{}\n\nAdăugați?",
        "search_t":"Căutare","search_l":"Caută:","results":"Rezultate",
        "no_res":"Nimic găsit.","undo":"↩ Undo","undo_ok":"Anulat.",
        "undo_empty":"Nimic de anulat.","rate":"QSO/h","timer":"⏱ Timer",
        "timer_t":"Timer Concurs","timer_start":"▶ Start","timer_stop":"⏸ Stop",
        "timer_reset":"⏹ Reset","elapsed":"Scurs:","remaining":"Rămas:",
        "dur_h":"Durată (ore):","band_sum":"Benzi",
        "distance":"Dist","country":"Țara","utc":"UTC","autosaved":"Salvat",
        "sounds":"Sunete","en_sounds":"Activează sunete",
        "qso_pts":"Puncte QSO","mult_c":"Multiplicatori","new_mult":"✦ MULT NOU!",
        "op":"Operator:","power":"Putere (W):","f_band":"Bandă:","f_mode":"Mod:",
        "all":"Toate","clear_log":"🗑 Golire log",
        "clear_conf":"Goliți COMPLET logul?\nSe va face backup automat!\nIREVERSIBIL!",
        "wb":"Lucrat alt QRG","imp_adif":"Import ADIF","imp_csv":"Import CSV",
        "imp_ok":"Importate {} QSO!","imp_err":"Eroare import!",
        "qso_total":"Total QSO","unique":"Unice","countries":"Țări",
        "print_log":"🖨 Print",
        "verify":"Verificare log","verify_ok":"Log integru: {} QSO, hash: {}",
        "score_f":"Scor","worked_all":"Status Complet",
        "worked_x":"Lucrate: {}/{}","missing_x":"Lipsesc: {}",
        "tools":"🛠 Utilități","clear_c":"Golire log curent",
        "save_cat":"💾 Salvează",
        "exp_edi":"EDI (.edi)","exp_print":"Print (.txt)",
        "hash_ok":"Hash MD5 OK","hash_err":"Eroare hash",
        "exp_cab2":"Cabrillo 2.0 (.log)",
        "email_l":"Email:","soapbox":"SOAPBOX:",
        "cab_name":"Nume Cabrillo:","exch_fmt":"Format Exchange:",
        "soapbox_l":"Soapbox:","imp_cab":"Import Cabrillo",
        "preview":"👁 Previzualizare","preview_t":"Previzualizare Export",
        "exp_warn":"⚠ Atenție!",
        "exp_warn_msg":"Logul are probleme:\n{}\n\nContinuați exportul?",
        "switch_conf":"Schimbați concursul?\nLogul curent va fi salvat.",
        "exch_sent_l":"Exchange TRIMIS:","exch_rcvd_l":"Exchange PRIMIT:",
        "cab2_config":"Configurare Cabrillo 2.0","cab2_export":"📤 Exportă",
    },
    "en": {
        "app_title":"YO Log PRO v17.1","call":"Callsign","band":"Band","mode":"Mode",
        "rst_s":"RST S","rst_r":"RST R","serial_s":"Nr S","serial_r":"Nr R",
        "freq":"Freq (kHz)","note":"Note/Locator","log":"LOG","update":"UPDATE",
        "search":"🔍 Search","reset":"Reset","settings":"⚙ Settings",
        "stats":"📊 Stats","validate":"✅ Validate","export":"📤 Export",
        "import_log":"📥 Import","delete":"Delete","backup":"💾 Backup",
        "online":"Online UTC","offline":"Manual","category":"Category","county":"County",
        "req_st":"Required Stations","worked":"Stations Worked","total_score":"Total Score",
        "val_result":"Validation","date_l":"Date:","time_l":"Time:","manual":"Manual",
        "confirm_del":"Confirm","confirm_del_t":"Delete selected?",
        "bak_ok":"Backup created!","bak_err":"Backup error!",
        "exit_t":"Exit","exit_m":"Save before exit?",
        "help":"Help","about":"About","save":"Save","close":"Close",
        "credits":"Developed by:\nArdei Constantin-Cătălin (YO8ACR)\nyo8acr@gmail.com",
        "usage":"Ctrl+F=Search  Ctrl+Z=Undo  Ctrl+S=Save  F2=Band+  F3=Mode+  Enter=LOG",
        "edit_qso":"Edit","delete_qso":"Delete","data":"Date","ora":"Time",
        "sel_fmt":"Format:","cancel":"Cancel","exp_ok":"Export done!","error":"Error",
        "sett_ok":"Settings saved!","locator":"Locator:","address":"Address:",
        "font_size":"Font:","station_info":"Station Info:",
        "contest_mgr":"Contest Manager","contests":"Contests",
        "add_c":"➕ Add","edit_c":"✏ Edit","del_c":"🗑 Delete",
        "dup_c":"📋 Duplicate","exp_c":"📤 Export JSON","imp_c":"📥 Import JSON",
        "c_name":"Contest Name:","c_type":"Type:","sc_mode":"Scoring:",
        "cats":"Categories (one per line):","a_bands":"Allowed Bands:",
        "a_modes":"Allowed Modes:",
        "req_st_c":"Required Stations (one per line):",
        "sp_sc":"Special Scoring (CALL=PTS):",
        "ppq":"Points/QSO:","min_qso":"Min QSO:","use_serial":"Serial Numbers",
        "use_county":"County","county_list":"Counties (comma sep):","no_sel":"Not selected!",
        "del_c_conf":"Delete '{}'?","c_saved":"Saved!","c_del":"Deleted!",
        "c_exists":"ID exists!","c_default":"Protected!","c_id":"Contest ID:",
        "mults":"Multipliers:","band_pts":"Band Points (BAND=PTS):",
        "nr":"Nr.","pts":"Pt",
        "dup_warn":"⚠ Duplicate!","dup_msg":"{} on {} {}!\nQSO #{}\n\nAdd anyway?",
        "search_t":"Search","search_l":"Search:","results":"Results",
        "no_res":"No results.","undo":"↩ Undo","undo_ok":"Undone.",
        "undo_empty":"Nothing to undo.","rate":"QSO/h","timer":"⏱ Timer",
        "timer_t":"Contest Timer","timer_start":"▶ Start","timer_stop":"⏸ Stop",
        "timer_reset":"⏹ Reset","elapsed":"Elapsed:","remaining":"Remaining:",
        "dur_h":"Duration (hours):","band_sum":"Bands",
        "distance":"Dist","country":"Country","utc":"UTC","autosaved":"Saved",
        "sounds":"Sounds","en_sounds":"Enable sounds",
        "qso_pts":"QSO Points","mult_c":"Multipliers","new_mult":"✦ NEW MULT!",
        "op":"Operator:","power":"Power (W):","f_band":"Band:","f_mode":"Mode:",
        "all":"All","clear_log":"🗑 Clear log",
        "clear_conf":"Clear ENTIRE log?\nAuto-backup will be created!\nIRREVERSIBLE!",
        "wb":"Worked other QRG","imp_adif":"Import ADIF","imp_csv":"Import CSV",
        "imp_ok":"Imported {} QSOs!","imp_err":"Import error!",
        "qso_total":"Total QSO","unique":"Unique","countries":"Countries",
        "print_log":"🖨 Print",
        "verify":"Verify Log","verify_ok":"Log OK: {} QSOs, hash: {}",
        "score_f":"Score","worked_all":"Completion Status",
        "worked_x":"Worked: {}/{}","missing_x":"Missing: {}",
        "tools":"🛠 Tools","clear_c":"Clear current log",
        "save_cat":"💾 Save",
        "exp_edi":"EDI (.edi)","exp_print":"Print (.txt)",
        "hash_ok":"Hash MD5 OK","hash_err":"Hash error",
        "exp_cab2":"Cabrillo 2.0 (.log)",
        "email_l":"Email:","soapbox":"SOAPBOX:",
        "cab_name":"Cabrillo Name:","exch_fmt":"Exchange Format:",
        "soapbox_l":"Soapbox:","imp_cab":"Import Cabrillo",
        "preview":"👁 Preview","preview_t":"Export Preview",
        "exp_warn":"⚠ Warning!",
        "exp_warn_msg":"Log has issues:\n{}\n\nContinue export?",
        "switch_conf":"Switch contest?\nCurrent log will be saved.",
        "exch_sent_l":"Exchange SENT:","exch_rcvd_l":"Exchange RECEIVED:",
        "cab2_config":"Cabrillo 2.0 Configuration","cab2_export":"📤 Export",
    }
}

DEFAULT_CONTESTS = {
    "simplu": {
        "name_ro":"Log Simplu","name_en":"Simple Log","contest_type":"Simplu",
        "cabrillo_name":"Simple Log",
        "categories":["Individual"],"scoring_mode":"none","points_per_qso":1,
        "min_qso":0,"allowed_bands":list(BANDS_ALL),"allowed_modes":list(MODES_ALL),
        "required_stations":[],"special_scoring":{},"use_serial":False,
        "use_county":False,"county_list":[],"multiplier_type":"none",
        "band_points":{},"exchange_format":"none","is_default":True
    },
    "maraton": {
        "name_ro":"Maraton Ion Creangă","name_en":"Marathon Ion Creanga",
        "contest_type":"Maraton","cabrillo_name":"MARATON ION CREANGA",
        "categories":["A. Seniori YO","B. YL","C. Juniori YO","D. Club","E. DX","F. Receptori"],
        "scoring_mode":"maraton","points_per_qso":1,"min_qso":100,
        "allowed_bands":BANDS_HF+BANDS_VHF,"allowed_modes":list(MODES_ALL),
        "required_stations":[],"special_scoring":{},"use_serial":False,
        "use_county":True,"county_list":list(YO_COUNTIES),
        "multiplier_type":"county","band_points":{},
        "exchange_format":"none","is_default":False
    },
    "stafeta": {
        "name_ro":"Ștafetă","name_en":"Relay","contest_type":"Stafeta",
        "cabrillo_name":"STAFETA",
        "categories":["A. Senior","B. YL","C. Junior"],
        "scoring_mode":"per_qso","points_per_qso":2,"min_qso":50,
        "allowed_bands":BANDS_HF,"allowed_modes":["SSB","CW"],
        "required_stations":[],"special_scoring":{},"use_serial":True,
        "use_county":True,"county_list":list(YO_COUNTIES),
        "multiplier_type":"county","band_points":{},
        "exchange_format":"county","is_default":False
    },
    "yo-dx-hf": {
        "name_ro":"YO DX HF Contest","name_en":"YO DX HF Contest","contest_type":"DX",
        "cabrillo_name":"YO DX HF",
        "categories":["A. SO AB High","B. SO AB Low","C. SO SB"],
        "scoring_mode":"per_band","points_per_qso":1,"min_qso":0,
        "allowed_bands":["160m","80m","40m","20m","15m","10m"],
        "allowed_modes":["SSB","CW"],
        "required_stations":[],"special_scoring":{},"use_serial":True,
        "use_county":True,"county_list":list(YO_COUNTIES),
        "multiplier_type":"dxcc",
        "band_points":{"160m":4,"80m":3,"40m":2,"20m":1,"15m":1,"10m":2},
        "exchange_format":"serial","is_default":False
    },
    "yo-vhf": {
        "name_ro":"YO VHF Contest","name_en":"YO VHF Contest","contest_type":"VHF",
        "cabrillo_name":"YO VHF",
        "categories":["A. Fixed","B. Mobile","C. Portable"],
        "scoring_mode":"distance","points_per_qso":1,"min_qso":0,
        "allowed_bands":["6m","2m","70cm","23cm"],"allowed_modes":["SSB","CW","FM"],
        "required_stations":[],"special_scoring":{},"use_serial":True,
        "use_county":False,"county_list":[],
        "multiplier_type":"grid","band_points":{},
        "exchange_format":"grid","is_default":False
    },
    "field-day": {
        "name_ro":"Field Day","name_en":"Field Day","contest_type":"Field Day",
        "cabrillo_name":"FIELD DAY",
        "categories":["1A","2A","3A","1B","2B"],
        "scoring_mode":"per_qso","points_per_qso":2,"min_qso":0,
        "allowed_bands":list(BANDS_HF),"allowed_modes":list(MODES_ALL),
        "required_stations":[],"special_scoring":{},"use_serial":False,
        "use_county":False,"county_list":[],
        "multiplier_type":"none","band_points":{},
        "exchange_format":"none","is_default":False
    },
    "sprint": {
        "name_ro":"Sprint","name_en":"Sprint","contest_type":"Sprint",
        "cabrillo_name":"SPRINT",
        "categories":["A. Single Op","B. Multi Op"],
        "scoring_mode":"per_qso","points_per_qso":1,"min_qso":0,
        "allowed_bands":["40m","20m","15m","10m"],"allowed_modes":["SSB","CW"],
        "required_stations":[],"special_scoring":{},"use_serial":True,
        "use_county":False,"county_list":[],
        "multiplier_type":"none","band_points":{},
        "exchange_format":"serial","is_default":False
    },
}

DEFAULT_CFG = {
    "call":"YO8ACR","loc":"KN37","jud":"NT","addr":"",
    "cat":0,"fs":11,"contest":"simplu","county":"NT",
    "lang":"ro","manual_dt":False,"sounds":True,
    "op_name":"","power":"100","win_geo":"",
    "email":"","soapbox":"73 GL",
    "cab2_exch_sent":"none","cab2_exch_rcvd":"log",
    "theme":"Dark Blue (implicit)",
    "cat_enabled":False,"cat_protocol":"Yaesu CAT",
    "cat_port":"","cat_baud":38400,"cat_poll":2000,
    "cat_civaddr":"94","cat_hamlib_host":"localhost","cat_hamlib_port":4532,
    "first_run":True
}




# ═══════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════
THEMES = {
    "Dark Blue (implicit)": {
        "bg":"#0d1117","fg":"#e6edf3","accent":"#1f6feb",
        "entry_bg":"#161b22","header_bg":"#010409",
        "btn_bg":"#21262d","btn_fg":"#f0f6fc",
        "led_on":"#3fb950","led_off":"#f85149",
        "warn":"#d29922","ok":"#3fb950","err":"#f85149",
        "dup_bg":"#3d1a1a","mult_bg":"#1a3d1a","spec_bg":"#1a1a3d",
        "alt":"#0d1f2d","gold":"#ffd700","cyan":"#58a6ff"
    },
    "Dark Green": {
        "bg":"#0a0f0a","fg":"#d0f0d0","accent":"#00aa44",
        "entry_bg":"#0f1a0f","header_bg":"#050a05",
        "btn_bg":"#1a2e1a","btn_fg":"#d0f0d0",
        "led_on":"#00ff66","led_off":"#ff4444",
        "warn":"#ccaa00","ok":"#00cc44","err":"#ff4444",
        "dup_bg":"#3d1a1a","mult_bg":"#1a3d1a","spec_bg":"#1a2a3d",
        "alt":"#0f200f","gold":"#aaff44","cyan":"#44ffaa"
    },
    "Dark Red": {
        "bg":"#0f0a0a","fg":"#f0d0d0","accent":"#cc2200",
        "entry_bg":"#1a0f0f","header_bg":"#0a0505",
        "btn_bg":"#2e1a1a","btn_fg":"#f0d0d0",
        "led_on":"#ff6644","led_off":"#888888",
        "warn":"#ff9900","ok":"#ff6600","err":"#ff2200",
        "dup_bg":"#3d1010","mult_bg":"#1a2a1a","spec_bg":"#1a1a3d",
        "alt":"#200f0f","gold":"#ffaa44","cyan":"#ff8844"
    },
    "Dark Purple": {
        "bg":"#0d0a14","fg":"#e0d0f0","accent":"#7c3aed",
        "entry_bg":"#160f22","header_bg":"#08050f",
        "btn_bg":"#221a30","btn_fg":"#e0d0f0",
        "led_on":"#a855f7","led_off":"#f85149",
        "warn":"#d29922","ok":"#a855f7","err":"#f85149",
        "dup_bg":"#3d1a2a","mult_bg":"#1a1a3d","spec_bg":"#2a1a3d",
        "alt":"#150a20","gold":"#d4a0ff","cyan":"#a78bfa"
    },
    "Light (Zi)": {
        "bg":"#f0f4f8","fg":"#1a1a2e","accent":"#1565c0",
        "entry_bg":"#ffffff","header_bg":"#dce8f5",
        "btn_bg":"#90a4ae","btn_fg":"#ffffff",
        "led_on":"#2e7d32","led_off":"#c62828",
        "warn":"#e65100","ok":"#2e7d32","err":"#c62828",
        "dup_bg":"#ffcdd2","mult_bg":"#c8e6c9","spec_bg":"#e3f2fd",
        "alt":"#e8f0f8","gold":"#e65100","cyan":"#0277bd"
    },
    "Light Sepia": {
        "bg":"#f5f0e8","fg":"#2c1a00","accent":"#8b4513",
        "entry_bg":"#fffdf5","header_bg":"#e8dcc8",
        "btn_bg":"#b8956a","btn_fg":"#ffffff",
        "led_on":"#4a7c2f","led_off":"#c0392b",
        "warn":"#e67e22","ok":"#4a7c2f","err":"#c0392b",
        "dup_bg":"#f5c6cb","mult_bg":"#c3e6cb","spec_bg":"#d4edda",
        "alt":"#ede8dc","gold":"#8b4513","cyan":"#5c6bc0"
    },
}
TH = dict(THEMES["Dark Blue (implicit)"])

# ═══════════════════════════════════════════════════════════
# CAT ENGINE — Computer Aided Transceiver
# Suportat: Yaesu CAT, Icom CI-V, Kenwood, Elecraft, Hamlib
# ═══════════════════════════════════════════════════════════

# Mapare mod CAT → mod logger
YAESU_MODE_MAP  = {b'\x00':"LSB",b'\x01':"USB",b'\x02':"CW",b'\x03':"CW",b'\x04':"AM",b'\x08':"FM",b'\x0a':"DIGI",b'\x0c':"DIGI",b'\x0e':"FT8"}
KENWOOD_MODE_MAP= {"LSB":"LSB","USB":"USB","CW":"CW","FM":"FM","AM":"AM","FSK":"RTTY","CWR":"CW","FSR":"RTTY"}
ICOM_MODE_MAP   = {0x00:"LSB",0x01:"USB",0x02:"AM",0x03:"CW",0x04:"RTTY",0x05:"FM",0x06:"CW",0x07:"DIGI",0x08:"FT8",0x11:"FT8"}

# Mapare mod logger → byte Yaesu
YAESU_MODE_REV  = {"LSB":0x00,"USB":0x01,"CW":0x02,"AM":0x04,"FM":0x08,"SSB":0x01,"DIGI":0x0a,"RTTY":0x0a,"FT8":0x0e,"FT4":0x0e}
ICOM_MODE_REV   = {"LSB":0x00,"USB":0x01,"AM":0x02,"CW":0x03,"RTTY":0x04,"FM":0x05,"DIGI":0x07,"FT8":0x08,"FT4":0x08,"SSB":0x01}
KENWOOD_MODE_REV= {"LSB":"LSB","USB":"USB","SSB":"USB","CW":"CW","FM":"FM","AM":"AM","RTTY":"FSK","DIGI":"FSK","FT8":"FSK","FT4":"FSK"}

# Baud-uri implicite per protocol
CAT_BAUD_DEFAULTS = {
    "Yaesu CAT":38400, "Icom CI-V":19200,
    "Kenwood CAT":9600, "Elecraft CAT":38400, "Hamlib/rigctld":4532
}

CAT_PROTOCOLS = ["Yaesu CAT","Icom CI-V","Kenwood CAT","Elecraft CAT","Hamlib/rigctld","Manual (fără CAT)"]


class CATEngine:
    """Motor CAT bidirecțional — polling 2s, thread separat, safe pentru Tkinter."""

    def __init__(self):
        self._ser    = None          # serial.Serial
        self._sock   = None          # socket pentru Hamlib
        self._thread = None
        self._stop   = threading.Event()
        self._lock   = threading.Lock()
        self.connected   = False
        self.protocol    = "Manual (fără CAT)"
        self.last_freq   = ""        # kHz string
        self.last_mode   = ""        # SSB/CW/etc
        self.last_error  = ""
        self.on_update   = None      # callback(freq_khz, mode)
        self.civ_addr    = 0x94      # Icom CI-V address

    # ── Conectare ──────────────────────────────────────────
    def connect(self, cfg):
        self.disconnect()
        self.protocol = cfg.get("cat_protocol","Manual (fără CAT)")
        if self.protocol == "Manual (fără CAT)":
            return True, "Manual — CAT dezactivat"
        if self.protocol == "Hamlib/rigctld":
            return self._connect_hamlib(cfg)
        else:
            return self._connect_serial(cfg)

    def _connect_serial(self, cfg):
        if not HAS_SERIAL:
            return False, "pyserial nu este instalat!\nInstalează: pip install pyserial"
        port  = cfg.get("cat_port","")
        baud  = int(cfg.get("cat_baud", CAT_BAUD_DEFAULTS.get(self.protocol,9600)))
        try:
            civ_hex = cfg.get("cat_civaddr","94")
            self.civ_addr = int(civ_hex, 16) if civ_hex else 0x94
        except: self.civ_addr = 0x94
        if not port:
            return False, "Port COM neselectat!"
        try:
            self._ser = serial.Serial(
                port=port, baudrate=baud,
                bytesize=8, parity='N', stopbits=2,
                timeout=0.5, write_timeout=1.0
            )
            self.connected = True
            self.last_error = ""
            self._stop.clear()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            return True, f"Conectat: {port} @ {baud} baud"
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            return False, f"Eroare port serial:\n{e}"

    def _connect_hamlib(self, cfg):
        host = cfg.get("cat_hamlib_host","localhost")
        port = int(cfg.get("cat_hamlib_port",4532))
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(3)
            self._sock.connect((host, port))
            self.connected = True
            self.last_error = ""
            self._stop.clear()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            return True, f"Hamlib conectat: {host}:{port}"
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            return False, f"Eroare Hamlib:\n{e}\n\nAsigură-te că rigctld rulează:\nrigctld -m MODEL -r PORT"

    # ── Deconectare ────────────────────────────────────────
    def disconnect(self):
        self._stop.set()
        self.connected = False
        time.sleep(0.1)
        with self._lock:
            if self._ser:
                try: self._ser.close()
                except: pass
                self._ser = None
            if self._sock:
                try: self._sock.close()
                except: pass
                self._sock = None
        self.last_freq = ""
        self.last_mode = ""

    # ── Poll loop (thread) ─────────────────────────────────
    def _poll_loop(self):
        while not self._stop.is_set():
            try:
                freq, mode = self._read_radio()
                if freq:
                    self.last_freq = freq
                    self.last_mode = mode or self.last_mode
                    if self.on_update:
                        self.on_update(self.last_freq, self.last_mode)
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
                break
            self._stop.wait(2.0)   # poll la 2 secunde

    # ── Citire frecvență și mod ─────────────────────────────
    def _read_radio(self):
        if self.protocol == "Yaesu CAT":    return self._yaesu_get()
        if self.protocol == "Icom CI-V":    return self._icom_get()
        if self.protocol == "Kenwood CAT":  return self._kenwood_get()
        if self.protocol == "Elecraft CAT": return self._elecraft_get()
        if self.protocol == "Hamlib/rigctld": return self._hamlib_get()
        return None, None

    # ── YAESU CAT ──────────────────────────────────────────
    # Comenzi 5-byte: CMD P1 P2 P3 P4
    def _yaesu_send(self, cmd, p1=0,p2=0,p3=0,p4=0):
        with self._lock:
            if not self._ser: return b""
            self._ser.reset_input_buffer()
            self._ser.write(bytes([p1,p2,p3,p4,cmd]))
            time.sleep(0.05)
            return self._ser.read(self._ser.in_waiting or 1)

    def _yaesu_get(self):
        # FA — Read Frequency (5 byte reply BCD)
        raw = self._yaesu_send(0x03)
        if len(raw) >= 5:
            # BCD decode: bytes 0-3 = 8 cifre BCD, byte 4 = mod
            bcd = ""
            for b in raw[:4]: bcd += f"{(b>>4)&0xF}{b&0xF}"
            try:
                hz = int(bcd)
                khz = str(hz // 1000)
                mode_byte = raw[4:5]
                mode = YAESU_MODE_MAP.get(mode_byte, "SSB")
                return khz, mode
            except: pass
        return None, None

    def _yaesu_set_freq(self, khz):
        """Trimite frecvență spre Yaesu (BCD encoding)"""
        with self._lock:
            if not self._ser: return False
            try:
                hz = int(float(khz) * 1000)
                hz_str = f"{hz:08d}"
                b = []
                for i in range(0, 8, 2):
                    b.append((int(hz_str[i])<<4) | int(hz_str[i+1]))
                b.append(0x01)  # CMD = Set Frequency
                self._ser.write(bytes(b))
                return True
            except: return False

    def _yaesu_set_mode(self, mode):
        """Trimite mod spre Yaesu"""
        with self._lock:
            if not self._ser: return False
            mb = YAESU_MODE_REV.get(mode.upper(), 0x01)
            self._ser.write(bytes([mb, 0,0,0, 0x07]))
            return True

    # ── ICOM CI-V ──────────────────────────────────────────
    def _icom_send(self, cmd, subcmd=None, data=b""):
        with self._lock:
            if not self._ser: return b""
            addr = self.civ_addr
            pkt = bytes([0xFE,0xFE,addr,0xE0,cmd])
            if subcmd is not None: pkt += bytes([subcmd])
            pkt += data + bytes([0xFD])
            self._ser.reset_input_buffer()
            self._ser.write(pkt)
            time.sleep(0.08)
            resp = b""
            t0 = time.time()
            while time.time()-t0 < 0.5:
                chunk = self._ser.read(self._ser.in_waiting or 1)
                resp += chunk
                if b'\xfd' in resp: break
                time.sleep(0.01)
            return resp

    def _icom_bcd_to_hz(self, data):
        hz = 0
        for i,b in enumerate(data):
            hz += (b&0xF) * (10**(2*i))
            hz += ((b>>4)&0xF) * (10**(2*i+1))
        return hz

    def _icom_get(self):
        resp = self._icom_send(0x03)   # Read operating frequency
        # Find response frame: FE FE E0 addr 03 [5 bytes freq] FD
        idx = resp.find(bytes([0xFE,0xFE,0xE0]))
        if idx >= 0:
            frame = resp[idx:]
            if len(frame) >= 11 and frame[4] == 0x03:
                freq_data = frame[5:10]
                hz = self._icom_bcd_to_hz(freq_data)
                khz = str(hz // 1000)
                # Read mode
                resp2 = self._icom_send(0x04)
                mode = "SSB"
                idx2 = resp2.find(bytes([0xFE,0xFE,0xE0]))
                if idx2 >= 0:
                    f2 = resp2[idx2:]
                    if len(f2) >= 8 and f2[4] == 0x04:
                        mode = ICOM_MODE_MAP.get(f2[5], "SSB")
                return khz, mode
        return None, None

    def _icom_set_freq(self, khz):
        with self._lock:
            if not self._ser: return False
            try:
                hz = int(float(khz) * 1000)
                data = bytes([(hz//(10**(2*i)))%100 for i in range(5)])
                # encode as BCD pairs
                bcd = bytes([((hz//(10**(2*i+1)))%10 <<4)|((hz//(10**(2*i)))%10) for i in range(5)])
                self._ser.write(bytes([0xFE,0xFE,self.civ_addr,0xE0,0x05])+bcd+bytes([0xFD]))
                return True
            except: return False

    def _icom_set_mode(self, mode):
        with self._lock:
            if not self._ser: return False
            mb = ICOM_MODE_REV.get(mode.upper(), 0x01)
            self._ser.write(bytes([0xFE,0xFE,self.civ_addr,0xE0,0x06,mb,0x00,0xFD]))
            return True

    # ── KENWOOD CAT ────────────────────────────────────────
    def _kenwood_cmd(self, cmd):
        with self._lock:
            if not self._ser: return ""
            self._ser.reset_input_buffer()
            self._ser.write((cmd+";").encode())
            time.sleep(0.05)
            resp = b""
            t0 = time.time()
            while time.time()-t0 < 0.5:
                chunk = self._ser.read(self._ser.in_waiting or 1)
                resp += chunk
                if b";" in resp: break
                time.sleep(0.01)
            return resp.decode(errors="ignore")

    def _kenwood_get(self):
        resp = self._kenwood_cmd("FA")   # FA = VFO-A frequency
        # Response: FA00014200000;
        if resp.startswith("FA") and len(resp) >= 13:
            try:
                hz = int(resp[2:13])
                khz = str(hz // 1000)
                resp2 = self._kenwood_cmd("MD")
                mode = "SSB"
                if resp2.startswith("MD") and len(resp2) >= 3:
                    mc = resp2[2]
                    km = {"1":"LSB","2":"USB","3":"CW","4":"FM","5":"AM","6":"RTTY","7":"CW","9":"DIGI"}
                    mode = km.get(mc,"SSB")
                return khz, mode
            except: pass
        return None, None

    def _kenwood_set_freq(self, khz):
        with self._lock:
            if not self._ser: return False
            try:
                hz = int(float(khz)*1000)
                cmd = f"FA{hz:011d};"
                self._ser.write(cmd.encode())
                return True
            except: return False

    def _kenwood_set_mode(self, mode):
        with self._lock:
            if not self._ser: return False
            km = {"LSB":"1","USB":"2","SSB":"2","CW":"3","FM":"4","AM":"5","RTTY":"6","DIGI":"9","FT8":"9","FT4":"9"}
            mc = km.get(mode.upper(),"2")
            self._ser.write(f"MD{mc};".encode())
            return True

    # ── ELECRAFT CAT (similar Kenwood) ─────────────────────
    def _elecraft_get(self):
        resp = self._kenwood_cmd("FA")
        if resp.startswith("FA") and len(resp) >= 13:
            try:
                hz = int(resp[2:13])
                khz = str(hz // 1000)
                resp2 = self._kenwood_cmd("MD")
                mode = "SSB"
                if resp2.startswith("MD") and len(resp2) >= 3:
                    mc = resp2[2]
                    km = {"1":"LSB","2":"USB","3":"CW","4":"FM","5":"AM","6":"RTTY","9":"DIGI"}
                    mode = km.get(mc,"SSB")
                return khz, mode
            except: pass
        return None, None

    # ── HAMLIB/rigctld ─────────────────────────────────────
    def _hamlib_cmd(self, cmd):
        try:
            if not self._sock: return ""
            self._sock.settimeout(2)
            self._sock.sendall((cmd+"\n").encode())
            resp = b""
            t0 = time.time()
            while time.time()-t0 < 2:
                try:
                    chunk = self._sock.recv(256)
                    if not chunk: break
                    resp += chunk
                    if b"RPRT" in resp or resp.count(b"\n") >= 2: break
                except socket.timeout: break
            return resp.decode(errors="ignore").strip()
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            return ""

    def _hamlib_get(self):
        resp = self._hamlib_cmd("f")   # get frequency
        freq_khz = None
        try:
            for line in resp.splitlines():
                line = line.strip()
                if line and not line.startswith("RPRT") and line.isdigit():
                    freq_khz = str(int(line)//1000)
                    break
        except: pass
        mode = None
        resp2 = self._hamlib_cmd("m")  # get mode
        try:
            lines = [l.strip() for l in resp2.splitlines() if l.strip() and not l.startswith("RPRT")]
            if lines:
                mode_str = lines[0].upper()
                mmap = {"USB":"USB","LSB":"LSB","CW":"CW","CWR":"CW","FM":"FM","AM":"AM",
                        "RTTY":"RTTY","RTTYR":"RTTY","PKTUSB":"FT8","PKTLSB":"DIGI",
                        "FT8":"FT8","FT4":"FT4","DIGI":"DIGI","DATA":"DIGI"}
                mode = mmap.get(mode_str, mode_str)
        except: pass
        return freq_khz, mode

    def _hamlib_set_freq(self, khz):
        hz = int(float(khz)*1000)
        resp = self._hamlib_cmd(f"F {hz}")
        return "RPRT 0" in resp or resp == ""

    def _hamlib_set_mode(self, mode):
        mmap = {"SSB":"USB","USB":"USB","LSB":"LSB","CW":"CW","FM":"FM","AM":"AM",
                "RTTY":"RTTY","DIGI":"PKTUSB","FT8":"PKTUSB","FT4":"PKTUSB"}
        hm = mmap.get(mode.upper(),"USB")
        resp = self._hamlib_cmd(f"M {hm} 0")
        return "RPRT 0" in resp or resp == ""

    # ── API PUBLIC: set freq/mode spre radio ───────────────
    def set_freq(self, khz):
        """Trimite frecvență spre radio. Returns True/False."""
        if not self.connected: return False
        try:
            if self.protocol == "Yaesu CAT":     return self._yaesu_set_freq(khz)
            if self.protocol == "Icom CI-V":     return self._icom_set_freq(khz)
            if self.protocol == "Kenwood CAT":   return self._kenwood_set_freq(khz)
            if self.protocol == "Elecraft CAT":  return self._kenwood_set_freq(khz)
            if self.protocol == "Hamlib/rigctld":return self._hamlib_set_freq(khz)
        except: pass
        return False

    def set_mode(self, mode):
        """Trimite mod spre radio. Returns True/False."""
        if not self.connected: return False
        try:
            if self.protocol == "Yaesu CAT":     return self._yaesu_set_mode(mode)
            if self.protocol == "Icom CI-V":     return self._icom_set_mode(mode)
            if self.protocol == "Kenwood CAT":   return self._kenwood_set_mode(mode)
            if self.protocol == "Elecraft CAT":  return self._kenwood_set_mode(mode)
            if self.protocol == "Hamlib/rigctld":return self._hamlib_set_mode(mode)
        except: pass
        return False

    # ── Utilitar: listare porturi COM ─────────────────────
    @staticmethod
    def list_ports():
        if not HAS_SERIAL: return []
        try:
            return [p.device for p in serial.tools.list_ports.comports()]
        except: return []


# Instanță globală
CAT = CATEngine()

class DM:
    @staticmethod
    def fp(fn): return os.path.join(get_data_dir(), fn)
    @staticmethod
    def save(fn, d):
        p=DM.fp(fn); t=p+".tmp"
        try:
            with open(t,"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
            if os.path.exists(p): os.remove(p)
            os.rename(t,p); return True
        except:
            try: os.remove(t)
            except: pass
            return False
    @staticmethod
    def load(fn, default=None):
        p=DM.fp(fn)
        if not os.path.exists(p):
            if default is not None: DM.save(fn,default)
            return copy.deepcopy(default) if default is not None else {}
        try:
            with open(p,"r",encoding="utf-8") as f: return json.load(f)
        except: return copy.deepcopy(default) if default is not None else {}
    @staticmethod
    def log_fn(cid): return f"log_{re.sub(r'[^a-zA-Z0-9_-]','_',cid)}.json"
    @staticmethod
    def load_log(cid):
        data = DM.load(DM.log_fn(cid),[]); return data if isinstance(data,list) else []
    @staticmethod
    def save_log(cid, d): return DM.save(DM.log_fn(cid), d)
    @staticmethod
    def backup(cid, d):
        try:
            bd=os.path.join(get_data_dir(),"backups"); os.makedirs(bd,exist_ok=True)
            ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); sid=re.sub(r'[^a-zA-Z0-9_-]','_',cid)
            with open(os.path.join(bd,f"log_{sid}_{ts}.json"),"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
            bks=sorted(Path(bd).glob(f"log_{sid}_*.json"))
            while len(bks)>50: bks[0].unlink(); bks.pop(0)
            return True
        except: return False

class L:
    _c = "ro"
    @classmethod
    def s(cls,lang):
        if lang in T: cls._c=lang
    @classmethod
    def g(cls): return cls._c
    @classmethod
    def t(cls,k): return T.get(cls._c,{}).get(k,k)

class Score:
    @staticmethod
    def qso(q,rules,cfg=None):
        if not rules: return 1
        sm=rules.get("scoring_mode","none")
        if sm=="none": return 0
        call=q.get("c","").upper(); sp=rules.get("special_scoring",{})
        if call in sp:
            try: return int(sp[call])
            except: pass
        if sm=="per_qso": return rules.get("points_per_qso",1)
        elif sm=="per_band": return int(rules.get("band_points",{}).get(q.get("b",""),rules.get("points_per_qso",1)))
        elif sm=="maraton": return int(rules.get("special_scoring",{}).get(call,rules.get("points_per_qso",1)))
        elif sm=="distance":
            n=q.get("n","").strip(); ml=(cfg or {}).get("loc","")
            if Loc.valid(n) and Loc.valid(ml): return max(1,int(Loc.dist(ml,n)))
        return rules.get("points_per_qso",1)

    @staticmethod
    def mults(data,rules):
        mt=rules.get("multiplier_type","none")
        if mt=="none": return 1,set()
        ms=set()
        for q in data:
            n=q.get("n","").upper().strip(); c=q.get("c","").upper(); b=q.get("b","")
            if mt=="county":
                for co in rules.get("county_list",[]):
                    if re.search(r'\b'+re.escape(co.upper())+r'\b',n): ms.add(co.upper()); break
            elif mt=="dxcc": ms.add(DXCC.prefix(c))
            elif mt=="band": ms.add(b)
            elif mt=="grid":
                if len(n)>=4 and Loc.valid(n[:4]): ms.add(n[:4].upper())
        return max(1,len(ms)),ms

    @staticmethod
    def total(data,rules,cfg=None):
        if not data or not rules or rules.get("scoring_mode","none")=="none": return 0,0,0
        qp=sum(Score.qso(q,rules,cfg) for q in data); mc,_=Score.mults(data,rules)
        return (qp,mc,qp*mc) if rules.get("multiplier_type","none")!="none" else (qp,mc,qp)

    @staticmethod
    def is_dup(data,call,band,mode,edit_idx=None):
        cu=call.upper()
        for i,q in enumerate(data):
            if edit_idx is not None and i==edit_idx: continue
            if q.get("c","").upper()==cu and q.get("b")==band and q.get("m")==mode: return True,i
        return False,-1

    @staticmethod
    def worked_other(data,call,band,mode):
        cu=call.upper()
        for q in data:
            if q.get("c","").upper()==cu and (q.get("b")!=band or q.get("m")!=mode): return True
        return False

    @staticmethod
    def is_new_mult(data,qso,rules):
        mt=rules.get("multiplier_type","none")
        if mt=="none": return False
        _,ex=Score.mults(data,rules); n=qso.get("n","").upper().strip(); c=qso.get("c","").upper(); nm=None
        if mt=="county":
            for co in rules.get("county_list",[]):
                if re.search(r'\b'+re.escape(co.upper())+r'\b',n): nm=co.upper(); break
        elif mt=="dxcc": nm=DXCC.prefix(c)
        elif mt=="band": nm=qso.get("b","")
        elif mt=="grid":
            if len(n)>=4 and Loc.valid(n[:4]): nm=n[:4].upper()
        return nm is not None and nm not in ex

    @staticmethod
    def validate(data,rules,cfg=None):
        if not data: return False,"Log gol / Empty log",0
        if not rules: return True,f"OK: {len(data)} QSO",len(data)
        msgs=[]
        mq=rules.get("min_qso",0)
        if mq>0 and len(data)<mq: msgs.append(f"⚠ Min {mq} QSO, aveți/you have {len(data)}")
        seen=set(); dc=0
        for q in data:
            k=(q.get("c","").upper(),q.get("b"),q.get("m"))
            if k in seen: dc+=1
            seen.add(k)
        if dc: msgs.append(f"⚠ {dc} duplicate(s)")
        req=rules.get("required_stations",[])
        if req:
            cl={q.get("c","").upper() for q in data}
            missing=[r for r in req if r.upper() not in cl]
            if missing: msgs.append(f"⚠ Lipsă/Missing: {', '.join(missing)}")
        ab=rules.get("allowed_bands",[]); am=rules.get("allowed_modes",[])
        if ab and sum(1 for q in data if q.get("b") not in ab): msgs.append(f"⚠ Benzi interzise")
        if am and sum(1 for q in data if q.get("m") not in am): msgs.append(f"⚠ Moduri interzise")
        if msgs: return False,"\n".join(msgs),0
        _,_,tot=Score.total(data,rules,cfg)
        return True,f"✓ OK! {len(data)} QSO — Scor: {tot}",tot

class Importer:
    @staticmethod
    def parse_adif(text):
        qsos=[]; eoh=text.upper().find("<EOH>")
        if eoh>=0: text=text[eoh+5:]
        for rec in re.split(r'<EOR>',text,flags=re.IGNORECASE):
            rec=rec.strip()
            if not rec: continue
            fields={}
            for m in re.finditer(r'<(\w+):(\d+)(?::[^>]*)?>(.{0,9999}?)',rec,re.IGNORECASE|re.DOTALL):
                fields[m.group(1).upper()]=m.group(3)[:int(m.group(2))]
            if "CALL" not in fields: continue
            q={"c":fields["CALL"].upper(),"b":fields.get("BAND","40m"),"m":fields.get("MODE","SSB"),
               "s":fields.get("RST_SENT","59"),"r":fields.get("RST_RCVD","59")}
            qd=fields.get("QSO_DATE","")
            q["d"]=f"{qd[:4]}-{qd[4:6]}-{qd[6:8]}" if len(qd)==8 else datetime.datetime.utcnow().strftime("%Y-%m-%d")
            qt=fields.get("TIME_ON",""); q["t"]=f"{qt[:2]}:{qt[2:4]}" if len(qt)>=4 else "00:00"
            fr=fields.get("FREQ","")
            if fr:
                try: fv=float(fr); q["f"]=str(int(round(fv*1000) if fv<1000 else fv))
                except: q["f"]=fr
            else: q["f"]=""
            q["n"]=fields.get("GRIDSQUARE",fields.get("COMMENT",""))
            q["ss"]=fields.get("STX",""); q["sr"]=fields.get("SRX","")
            qsos.append(q)
        return qsos

    @staticmethod
    def parse_csv(text):
        qsos=[]
        try:
            for row in csv.DictReader(io.StringIO(text)):
                call=(row.get("Call") or row.get("CALL") or row.get("call") or row.get("Callsign") or "").upper().strip()
                if not call: continue
                qsos.append({"c":call,"b":row.get("Band") or row.get("BAND") or "40m","m":row.get("Mode") or row.get("MODE") or "SSB",
                    "s":row.get("RST_Sent") or row.get("RST_S") or "59","r":row.get("RST_Rcvd") or row.get("RST_R") or "59",
                    "d":row.get("Date") or row.get("DATE") or datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                    "t":row.get("Time") or row.get("TIME") or "00:00","f":row.get("Freq") or row.get("FREQ") or "",
                    "n":row.get("Note") or row.get("NOTE") or row.get("Comment") or "",
                    "ss":row.get("Nr_S") or row.get("SS") or "","sr":row.get("Nr_R") or row.get("SR") or ""})
        except: pass
        return qsos

    @staticmethod
    def parse_cabrillo(text):
        qsos=[]; version="3.0"
        for line in text.strip().splitlines():
            line=line.strip()
            if line.upper().startswith("START-OF-LOG:"): version=line.split(":",1)[1].strip() or "3.0"
            if not line.upper().startswith("QSO:"): continue
            parts=line[4:].strip()
            q=Importer._parse_cab2_qso(parts) if version.startswith("2") else Importer._parse_cab3_qso(parts)
            if q: qsos.append(q)
        return qsos

    @staticmethod
    def _parse_cab2_qso(parts):
        try:
            tk=parts.split()
            if len(tk)<8: return None
            call=tk[7] if len(tk)>7 else ""
            if not call or call=="--": return None
            d=tk[2]; d=d if "-" in d else f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d)==8 else d
            t=f"{tk[3][:2]}:{tk[3][2:4]}" if len(tk[3])>=4 else tk[3]
            return {"c":call.upper(),"b":freq2band(tk[0]) or "40m","m":CAB2_MODE_REV.get(tk[1].upper(),"SSB"),
                    "s":tk[5] if len(tk)>5 else "59","r":tk[8] if len(tk)>8 else "59","d":d,"t":t,"f":tk[0],
                    "n":tk[9] if len(tk)>9 and tk[9]!="--" else "","ss":tk[6] if len(tk)>6 and tk[6]!="--" else "",
                    "sr":tk[9] if len(tk)>9 and tk[9]!="--" else ""}
        except: return None

    @staticmethod
    def _parse_cab3_qso(parts):
        try:
            tk=parts.split()
            if len(tk)<7: return None
            call=tk[7] if len(tk)>7 else ""
            if not call: return None
            d=tk[2]; d=f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d)==8 and "-" not in d else d
            t=f"{tk[3][:2]}:{tk[3][2:4]}" if len(tk[3])>=4 else tk[3]
            return {"c":call.upper(),"b":freq2band(tk[0]) or "40m","m":tk[1].upper(),
                    "s":tk[5] if len(tk)>5 else "59","r":tk[8] if len(tk)>8 else "59","d":d,"t":t,"f":tk[0],
                    "n":tk[9] if len(tk)>9 else "","ss":tk[6] if len(tk)>6 else "","sr":tk[9] if len(tk)>9 else ""}
        except: return None

class ContestEditor(tk.Toplevel):
    def __init__(self, parent, cid=None, cdata=None, all_c=None):
        super().__init__(parent)
        self.result=None; self.cid=cid; self.new=cid is None; self.all_c=all_c or {}
        self.d=copy.deepcopy(cdata) if cdata else {"name_ro":"","name_en":"","contest_type":"Simplu","cabrillo_name":"","categories":["Individual"],"scoring_mode":"none","points_per_qso":1,"min_qso":0,"allowed_bands":list(BANDS_ALL),"allowed_modes":list(MODES_ALL),"required_stations":[],"special_scoring":{},"use_serial":False,"use_county":False,"county_list":[],"multiplier_type":"none","band_points":{},"exchange_format":"none","is_default":False}
        self.title(L.t("edit_c") if not self.new else L.t("add_c")); self.geometry("720x880"); self.configure(bg=TH["bg"]); self.transient(parent); self.grab_set(); self._build(); center_dialog(self,parent)

    def _build(self):
        outer=tk.Frame(self,bg=TH["bg"]); outer.pack(fill="both",expand=True)
        canvas=tk.Canvas(outer,bg=TH["bg"],highlightthickness=0); vsb=ttk.Scrollbar(outer,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set); vsb.pack(side="right",fill="y"); canvas.pack(side="left",fill="both",expand=True)
        self._inner=tk.Frame(canvas,bg=TH["bg"],padx=15,pady=10); win_id=canvas.create_window((0,0),window=self._inner,anchor="nw")
        self._inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfig(win_id,width=e.width))
        canvas.bind("<MouseWheel>",lambda e:canvas.yview_scroll(int(-1*(e.delta/120)),"units"))
        eo={"bg":TH["entry_bg"],"fg":TH["fg"],"font":("Consolas",11),"insertbackground":TH["fg"]}
        lo={"bg":TH["bg"],"fg":TH["fg"],"font":("Consolas",11)}; f=self._inner; r=0; self._e={}
        if self.new:
            tk.Label(f,text=L.t("c_id"),**lo).grid(row=r,column=0,sticky="w",pady=3)
            self._e["id"]=tk.Entry(f,width=30,**eo); self._e["id"].grid(row=r,column=1,sticky="w",pady=3); r+=1
        for k,lb in [("name_ro",L.t("c_name")+" (RO)"),("name_en",L.t("c_name")+" (EN)"),("cabrillo_name",L.t("cab_name"))]:
            tk.Label(f,text=lb,**lo).grid(row=r,column=0,sticky="w",pady=3)
            e=tk.Entry(f,width=40,**eo); e.insert(0,self.d.get(k,"")); e.grid(row=r,column=1,sticky="w",pady=3); self._e[k]=e; r+=1
        tk.Label(f,text=L.t("c_type"),**lo).grid(row=r,column=0,sticky="w",pady=3)
        self._tv=tk.StringVar(value=self.d.get("contest_type","Simplu")); ttk.Combobox(f,textvariable=self._tv,values=CONTEST_TYPES,state="readonly",width=18).grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("sc_mode"),**lo).grid(row=r,column=0,sticky="w",pady=3)
        self._sv=tk.StringVar(value=self.d.get("scoring_mode","none")); ttk.Combobox(f,textvariable=self._sv,values=SCORING_MODES,state="readonly",width=18).grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("exch_fmt"),**lo).grid(row=r,column=0,sticky="w",pady=3)
        self._efv=tk.StringVar(value=self.d.get("exchange_format","none")); ttk.Combobox(f,textvariable=self._efv,values=EXCHANGE_FORMATS,state="readonly",width=18).grid(row=r,column=1,sticky="w",pady=3); r+=1
        for k,lb in [("points_per_qso",L.t("ppq")),("min_qso",L.t("min_qso"))]:
            tk.Label(f,text=lb,**lo).grid(row=r,column=0,sticky="w",pady=3)
            e=tk.Entry(f,width=10,**eo); e.insert(0,str(self.d.get(k,0))); e.grid(row=r,column=1,sticky="w",pady=3); self._e[k]=e; r+=1
        tk.Label(f,text=L.t("mults"),**lo).grid(row=r,column=0,sticky="w",pady=3)
        self._mv=tk.StringVar(value=self.d.get("multiplier_type","none")); ttk.Combobox(f,textvariable=self._mv,values=["none","county","dxcc","band","grid"],state="readonly",width=18).grid(row=r,column=1,sticky="w",pady=3); r+=1
        self._serv=tk.BooleanVar(value=self.d.get("use_serial",False))
        tk.Checkbutton(f,text=L.t("use_serial"),variable=self._serv,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"]).grid(row=r,column=0,columnspan=2,sticky="w",pady=3); r+=1
        self._couv=tk.BooleanVar(value=self.d.get("use_county",False))
        tk.Checkbutton(f,text=L.t("use_county"),variable=self._couv,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"]).grid(row=r,column=0,columnspan=2,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("cats"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        self._cats_t=tk.Text(f,width=38,height=4,**eo); self._cats_t.insert("1.0","\n".join(self.d.get("categories",[]))); self._cats_t.grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("a_bands"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        bf=tk.Frame(f,bg=TH["bg"]); bf.grid(row=r,column=1,sticky="w",pady=3); ab_set=set(self.d.get("allowed_bands",BANDS_ALL)); self._band_vars={}
        for i,b in enumerate(BANDS_ALL):
            v=tk.BooleanVar(value=b in ab_set); self._band_vars[b]=v
            tk.Checkbutton(bf,text=b,variable=v,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"],font=("Consolas",9)).grid(row=i//7,column=i%7,sticky="w")
        r+=1
        tk.Label(f,text=L.t("a_modes"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        mf=tk.Frame(f,bg=TH["bg"]); mf.grid(row=r,column=1,sticky="w",pady=3); am_set=set(self.d.get("allowed_modes",MODES_ALL)); self._mode_vars={}
        for i,m in enumerate(MODES_ALL):
            v=tk.BooleanVar(value=m in am_set); self._mode_vars[m]=v
            tk.Checkbutton(mf,text=m,variable=v,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"],font=("Consolas",9)).grid(row=i//4,column=i%4,sticky="w")
        r+=1
        tk.Label(f,text=L.t("req_st_c"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        self._req_t=tk.Text(f,width=38,height=3,**eo); self._req_t.insert("1.0","\n".join(self.d.get("required_stations",[]))); self._req_t.grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("sp_sc"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        self._sp_t=tk.Text(f,width=38,height=3,**eo); self._sp_t.insert("1.0","\n".join(f"{k}={v}" for k,v in self.d.get("special_scoring",{}).items())); self._sp_t.grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("band_pts"),**lo).grid(row=r,column=0,sticky="nw",pady=3)
        self._bp_t=tk.Text(f,width=38,height=3,**eo); self._bp_t.insert("1.0","\n".join(f"{k}={v}" for k,v in self.d.get("band_points",{}).items())); self._bp_t.grid(row=r,column=1,sticky="w",pady=3); r+=1
        tk.Label(f,text=L.t("county_list"),**lo).grid(row=r,column=0,sticky="w",pady=3)
        self._cl_e=tk.Entry(f,width=50,**eo); self._cl_e.insert(0,",".join(self.d.get("county_list",[]))); self._cl_e.grid(row=r,column=1,sticky="w",pady=3); r+=1
        bf2=tk.Frame(f,bg=TH["bg"]); bf2.grid(row=r,column=0,columnspan=2,pady=18)
        tk.Button(bf2,text=L.t("save"),command=self._save,bg=TH["accent"],fg="white",font=("Consolas",12,"bold"),width=12).pack(side="left",padx=8)
        tk.Button(bf2,text=L.t("cancel"),command=self.destroy,bg=TH["btn_bg"],fg="white",font=("Consolas",12),width=12).pack(side="left",padx=8)

    @staticmethod
    def _parse_kv(text):
        result={}
        for line in text.strip().splitlines():
            if "=" in line: k,_,v=line.partition("="); k=k.strip().upper();
            if k: result[k]=v.strip()
        return result

    def _save(self):
        if self.new:
            cid=self._e["id"].get().strip().lower().replace(" ","-")
            if not cid: messagebox.showerror(L.t("error"),"ID invalid!"); return
            if cid in self.all_c: messagebox.showerror(L.t("error"),L.t("c_exists")); return
            self.cid=cid
        self.d["name_ro"]=self._e["name_ro"].get().strip(); self.d["name_en"]=self._e["name_en"].get().strip()
        self.d["cabrillo_name"]=self._e["cabrillo_name"].get().strip(); self.d["contest_type"]=self._tv.get()
        self.d["scoring_mode"]=self._sv.get(); self.d["exchange_format"]=self._efv.get()
        try: self.d["points_per_qso"]=int(self._e["points_per_qso"].get())
        except: self.d["points_per_qso"]=1
        try: self.d["min_qso"]=int(self._e["min_qso"].get())
        except: self.d["min_qso"]=0
        self.d["multiplier_type"]=self._mv.get(); self.d["use_serial"]=self._serv.get(); self.d["use_county"]=self._couv.get()
        cats=[c.strip() for c in self._cats_t.get("1.0","end").splitlines() if c.strip()]; self.d["categories"]=cats or ["Individual"]
        self.d["allowed_bands"]=[b for b,v in self._band_vars.items() if v.get()] or list(BANDS_ALL)
        self.d["allowed_modes"]=[m for m,v in self._mode_vars.items() if v.get()] or list(MODES_ALL)
        self.d["required_stations"]=[s.strip().upper() for s in self._req_t.get("1.0","end").splitlines() if s.strip()]
        self.d["special_scoring"]=self._parse_kv(self._sp_t.get("1.0","end"))
        raw=self._parse_kv(self._bp_t.get("1.0","end")); self.d["band_points"]={k:int(v) for k,v in raw.items() if v.isdigit()}
        cl=self._cl_e.get().strip(); self.d["county_list"]=[c.strip().upper() for c in cl.split(",") if c.strip()] if cl else []
        self.d["is_default"]=False; self.result=(self.cid,self.d); self.destroy()

class ContestMgr(tk.Toplevel):
    def __init__(self,parent,contests):
        super().__init__(parent); self.c=copy.deepcopy(contests); self.result=None
        self.title(L.t("contest_mgr")); self.geometry("750x500"); self.configure(bg=TH["bg"]); self.transient(parent); self.grab_set()
        self._build(); self._fill(); center_dialog(self,parent)
    def _build(self):
        tb=tk.Frame(self,bg=TH["header_bg"],pady=6); tb.pack(fill="x")
        for txt,cmd in [(L.t("add_c"),self._add),(L.t("edit_c"),self._edit),(L.t("dup_c"),self._dup),(L.t("del_c"),self._del),(L.t("exp_c"),self._export),(L.t("imp_c"),self._import)]:
            tk.Button(tb,text=txt,command=cmd,bg=TH["accent"],fg="white",font=("Consolas",10)).pack(side="left",padx=3)
        tf=tk.Frame(self,bg=TH["bg"]); tf.pack(fill="both",expand=True,padx=6,pady=3)
        cols=("id","name","type","sc","mult","minq")
        self.tree=ttk.Treeview(tf,columns=cols,show="headings",selectmode="browse")
        for c,h,w in zip(cols,["ID",L.t("c_name"),L.t("c_type"),L.t("sc_mode"),L.t("mults"),L.t("min_qso")],[110,200,90,90,70,60]):
            self.tree.heading(c,text=h); self.tree.column(c,width=w,anchor="center")
        sb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y"); self.tree.bind("<Double-1>",lambda e:self._edit())
        bt=tk.Frame(self,bg=TH["bg"],pady=6); bt.pack(fill="x")
        tk.Button(bt,text=L.t("save"),command=self._onsave,bg=TH["ok"],fg="white",font=("Consolas",12,"bold"),width=12).pack(side="left",padx=12)
        tk.Button(bt,text=L.t("cancel"),command=self.destroy,bg=TH["btn_bg"],fg="white",font=("Consolas",12),width=12).pack(side="right",padx=12)
    def _fill(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for cid,cd in self.c.items():
            self.tree.insert("","end",iid=cid,values=(cid,cd.get("name_"+L.g(),cd.get("name_ro",cid)),cd.get("contest_type","?"),cd.get("scoring_mode","none"),cd.get("multiplier_type","none"),cd.get("min_qso",0)))
    def _sel(self):
        s=self.tree.selection(); return s[0] if s else None
    def _add(self):
        d=ContestEditor(self,all_c=self.c); self.wait_window(d)
        if d.result: self.c[d.result[0]]=d.result[1]; self._fill()
    def _edit(self):
        cid=self._sel()
        if not cid: return
        d=ContestEditor(self,cid=cid,cdata=self.c[cid],all_c=self.c); self.wait_window(d)
        if d.result: self.c[cid]=d.result[1]; self._fill()
    def _dup(self):
        cid=self._sel()
        if not cid: return
        nc=cid+"-copy"; i=2
        while nc in self.c: nc=f"{cid}-copy{i}"; i+=1
        self.c[nc]=copy.deepcopy(self.c[cid]); self.c[nc]["is_default"]=False; self.c[nc]["name_ro"]+=" (copie)"; self.c[nc]["name_en"]+=" (copy)"; self._fill()
    def _del(self):
        cid=self._sel()
        if not cid: return
        if self.c.get(cid,{}).get("is_default"): return
        if messagebox.askyesno(L.t("confirm_del"),L.t("del_c_conf").format(cid)): del self.c[cid]; self._fill()
    def _export(self):
        fp=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if fp:
            try:
                with open(fp,"w",encoding="utf-8") as f: json.dump(self.c,f,indent=2,ensure_ascii=False)
                messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _import(self):
        fp=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if fp:
            try:
                with open(fp,"r",encoding="utf-8") as f: imp=json.load(f)
                if isinstance(imp,dict):
                    for cid,cd in imp.items():
                        if cid not in self.c: self.c[cid]=cd
                    self._fill()
            except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _onsave(self): self.result=self.c; self.destroy()

class SearchDialog(tk.Toplevel):
    def __init__(self,parent,log_data):
        super().__init__(parent); self.log_data=log_data; self.title(L.t("search_t")); self.geometry("600x420"); self.configure(bg=TH["bg"]); self.transient(parent)
        eo={"bg":TH["entry_bg"],"fg":TH["fg"],"font":("Consolas",11),"insertbackground":TH["fg"]}
        tk.Label(self,text=L.t("search_l"),bg=TH["bg"],fg=TH["fg"],font=("Consolas",11)).pack(anchor="w",padx=10,pady=(10,0))
        self._sv=tk.StringVar(); e=tk.Entry(self,textvariable=self._sv,width=40,**eo); e.pack(padx=10,pady=4,anchor="w"); e.bind("<KeyRelease>",self._search); e.focus()
        self._lbl=tk.Label(self,text="",bg=TH["bg"],fg=TH["fg"],font=("Consolas",9)); self._lbl.pack(anchor="w",padx=10)
        tf=tk.Frame(self,bg=TH["bg"]); tf.pack(fill="both",expand=True,padx=10,pady=4)
        cols=("nr","call","band","mode","date","note")
        self.tree=ttk.Treeview(tf,columns=cols,show="headings",selectmode="browse")
        for c,h,w in zip(cols,[L.t("nr"),L.t("call"),L.t("band"),L.t("mode"),L.t("data"),L.t("note")],[40,110,55,55,85,180]):
            self.tree.heading(c,text=h); self.tree.column(c,width=w,anchor="center")
        sb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        tk.Button(self,text=L.t("close"),command=self.destroy,bg=TH["btn_bg"],fg="white").pack(pady=8); center_dialog(self,parent)
    def _search(self,e=None):
        q=self._sv.get().upper().strip()
        for i in self.tree.get_children(): self.tree.delete(i)
        if not q: self._lbl.config(text=""); return
        results=[(len(self.log_data)-i,qso) for i,qso in enumerate(self.log_data) if q in qso.get("c","").upper() or q in qso.get("n","").upper()]
        self._lbl.config(text=f"{L.t('results')}: {len(results)}")
        for nr,qso in results: self.tree.insert("","end",values=(nr,qso.get("c"),qso.get("b"),qso.get("m"),qso.get("d"),qso.get("n")))

class TimerDialog(tk.Toplevel):
    """Timer concurs cu avertizare sonoră la 5/3/1 min și final."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(L.t("timer_t"))
        self.geometry("360x300")
        self.configure(bg=TH["bg"])
        self.transient(parent)
        self.resizable(False, False)
        self._running = False
        self._end_time = None
        self._duration = 0
        self._elapsed_start = None
        self._elapsed_secs = 0
        self._alerted = set()   # seturi de alerte deja trase (5min,3min,1min,end)
        self._build()
        self._tick()
        center_dialog(self, parent)

    def _build(self):
        lo = {"bg": TH["bg"], "fg": TH["fg"], "font": ("Consolas", 11)}
        eo = {"bg": TH["entry_bg"], "fg": TH["fg"], "font": ("Consolas", 11),
              "justify": "center", "insertbackground": TH["fg"], "width": 6}

        # ─ Durată ─
        df = tk.Frame(self, bg=TH["bg"]); df.pack(pady=(14, 4))
        tk.Label(df, text="Ore:", **lo).pack(side="left", padx=4)
        self._h_e = tk.Entry(df, **eo); self._h_e.insert(0, "4"); self._h_e.pack(side="left")
        tk.Label(df, text="Min:", **lo).pack(side="left", padx=(10, 4))
        self._m_e = tk.Entry(df, **eo); self._m_e.insert(0, "0"); self._m_e.pack(side="left")

        # ─ Ceas scurs ─
        self._time_lbl = tk.Label(self, text="00:00:00",
                                   bg=TH["bg"], fg=TH["gold"],
                                   font=("Consolas", 34, "bold"))
        self._time_lbl.pack(pady=6)

        # ─ Rămas ─
        self._rem_lbl = tk.Label(self, text="", **lo)
        self._rem_lbl.pack()

        # ─ Avertizări sonore ─
        af = tk.LabelFrame(self, text=" 🔔 Avertizări sonore ",
                           bg=TH["bg"], fg=TH["fg"],
                           font=("Consolas", 9))
        af.pack(fill="x", padx=12, pady=6)
        self._alert_v = tk.BooleanVar(value=True)
        tk.Checkbutton(af, text="Activ (5 min / 3 min / 1 min / Final)",
                       variable=self._alert_v,
                       bg=TH["bg"], fg=TH["fg"],
                       activebackground=TH["bg"],
                       selectcolor=TH["entry_bg"],
                       font=("Consolas", 9)).pack(anchor="w", padx=6)

        # ─ Butoane ─
        bf = tk.Frame(self, bg=TH["bg"]); bf.pack(pady=8)
        self._start_btn = tk.Button(bf, text=L.t("timer_start"),
                                     command=self._start,
                                     bg=TH["ok"], fg="white",
                                     font=("Consolas", 11), width=9)
        self._start_btn.pack(side="left", padx=4)
        tk.Button(bf, text=L.t("timer_reset"),
                  command=self._reset,
                  bg=TH["warn"], fg="white",
                  font=("Consolas", 11), width=9).pack(side="left", padx=4)

    def _start(self):
        if self._running:
            self._running = False
            self._start_btn.config(text=L.t("timer_start"), bg=TH["ok"])
        else:
            try:
                h = int(self._h_e.get() or 0)
                m = int(self._m_e.get() or 0)
                self._duration = h * 3600 + m * 60
            except Exception:
                self._duration = 0
            self._alerted = set()
            self._running = True
            self._elapsed_start = datetime.datetime.utcnow()
            if self._duration > 0:
                self._end_time = self._elapsed_start + datetime.timedelta(seconds=self._duration)
            else:
                self._end_time = None
            self._start_btn.config(text=L.t("timer_stop"), bg=TH["err"])

    def _reset(self):
        self._running = False
        self._elapsed_secs = 0
        self._end_time = None
        self._elapsed_start = None
        self._alerted = set()
        self._time_lbl.config(text="00:00:00", fg=TH["gold"])
        self._rem_lbl.config(text="")
        self._start_btn.config(text=L.t("timer_start"), bg=TH["ok"])

    def _beep_alert(self, kind):
        """Alertă sonoră diferențiată: 5min=1beep, 3min=2beeps, 1min=3beeps, end=5beeps."""
        if not self._alert_v.get():
            return
        try:
            import winsound
            patterns = {
                "5min":  [(880, 200)],
                "3min":  [(880, 200), (880, 200)],
                "1min":  [(1200, 200), (1200, 200), (1200, 200)],
                "end":   [(1600, 300), (1600, 300), (1600, 300), (1600, 300), (1600, 500)],
            }
            for freq, dur in patterns.get(kind, []):
                winsound.Beep(freq, dur)
        except Exception:
            beep("warning")

    def _tick(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if self._running and self._elapsed_start:
            now = datetime.datetime.utcnow()
            elapsed = int((now - self._elapsed_start).total_seconds()) + self._elapsed_secs
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            try:
                self._time_lbl.config(text=f"{h:02d}:{m:02d}:{s:02d}")
                if self._end_time:
                    remaining = int((self._end_time - now).total_seconds())
                    if remaining <= 0:
                        if "end" not in self._alerted:
                            self._alerted.add("end")
                            self._beep_alert("end")
                        self._running = False
                        self._time_lbl.config(fg=TH["err"])
                        self._rem_lbl.config(text="⏰ TIME UP!", fg=TH["err"])
                        self._start_btn.config(text=L.t("timer_start"), bg=TH["ok"])
                    else:
                        rh, rr = divmod(remaining, 3600)
                        rm, rs = divmod(rr, 60)
                        # Culoare avertizare
                        if remaining <= 60:
                            col = TH["err"]
                        elif remaining <= 180:
                            col = TH["warn"]
                        elif remaining <= 300:
                            col = "#FF9800"
                        else:
                            col = TH["fg"]
                        self._rem_lbl.config(
                            text=f"{L.t('remaining')} {rh:02d}:{rm:02d}:{rs:02d}",
                            fg=col)
                        # Avertizări sonore
                        if remaining <= 60 and "1min" not in self._alerted:
                            self._alerted.add("1min")
                            self._beep_alert("1min")
                        elif remaining <= 180 and "3min" not in self._alerted:
                            self._alerted.add("3min")
                            self._beep_alert("3min")
                        elif remaining <= 300 and "5min" not in self._alerted:
                            self._alerted.add("5min")
                            self._beep_alert("5min")
            except Exception:
                return
        try:
            self.after(1000, self._tick)
        except Exception:
            pass

class StatsWindow(tk.Toplevel):
    def __init__(self,parent,log_data,rules,cfg):
        super().__init__(parent); self.title(L.t("stats")); self.geometry("560x520"); self.configure(bg=TH["bg"]); self.transient(parent); center_dialog(self,parent)
        txt=scrolledtext.ScrolledText(self,bg=TH["entry_bg"],fg=TH["fg"],font=("Consolas",10),wrap="word"); txt.pack(fill="both",expand=True,padx=10,pady=10)
        txt.tag_configure("h",foreground=TH["gold"],font=("Consolas",11,"bold")); txt.tag_configure("ok",foreground=TH["ok"]); txt.tag_configure("warn",foreground=TH["warn"])
        def w(t,tag=None): txt.insert("end",t,tag)
        nm=rules.get("name_"+L.g(),rules.get("name_ro","?")) if rules else "?"
        w(f"📊 {L.t('stats')} — {nm}\n\n","h"); w(f"Total QSO: {len(log_data)}\nUnice: {len({q.get('c','').upper() for q in log_data})}\n")
        if log_data:
            try:
                dts=sorted([datetime.datetime.strptime(q.get("d","")+" "+q.get("t",""),"%Y-%m-%d %H:%M") for q in log_data if q.get("d") and q.get("t")])
                if len(dts)>=2:
                    span_h=(dts[-1]-dts[0]).total_seconds()/3600
                    w(f"Duration: {span_h:.1f}h  Rate: {len(log_data)/span_h:.1f} QSO/h\n")
            except: pass
        w("\n─── Benzi ───\n","h")
        bc=Counter(q.get("b","?") for q in log_data)
        for b in BANDS_ALL:
            if b in bc: w(f"  {b:<6} QSO:{bc[b]:<5} Pts:{sum(Score.qso(q,rules,cfg) for q in log_data if q.get('b')==b)}\n")
        w("\n─── Scor ───\n","h")
        if rules and rules.get("scoring_mode","none")!="none":
            qp,mult,tot=Score.total(log_data,rules,cfg); w(f"  {qp}×{mult}={tot}\n","ok")
        else: w("  (no scoring)\n","warn")
        txt.config(state="disabled"); tk.Button(self,text=L.t("close"),command=self.destroy,bg=TH["btn_bg"],fg="white").pack(pady=6)

class Cab2ConfigDialog(tk.Toplevel):
    def __init__(self,parent,cfg):
        super().__init__(parent); self.result=None; self.cfg=cfg; self.title(L.t("cab2_config")); self.geometry("420x250"); self.configure(bg=TH["bg"]); self.transient(parent); self.grab_set()
        lo={"bg":TH["bg"],"fg":TH["fg"],"font":("Consolas",11)}; jud=cfg.get("county",cfg.get("jud","NT")); loc=cfg.get("loc","KN37")
        tk.Label(self,text=L.t("exch_sent_l"),**lo).pack(anchor="w",padx=15,pady=(15,0))
        sent_opts=EXCH_SENT_OPTIONS.get(L.g(),EXCH_SENT_OPTIONS["ro"]); self._sent_labels={}; self._sent_values=[]
        for k,lbl in sent_opts.items():
            display=lbl.format(jud=jud,loc=loc); self._sent_labels[display]=k; self._sent_values.append(display)
        saved=cfg.get("cab2_exch_sent","none"); default_sent=self._sent_values[-1]
        for d,k in self._sent_labels.items():
            if k==saved: default_sent=d; break
        self._sent_v=tk.StringVar(value=default_sent); ttk.Combobox(self,textvariable=self._sent_v,values=self._sent_values,state="readonly",width=30,font=("Consolas",11)).pack(padx=15,pady=4)
        tk.Label(self,text=L.t("exch_rcvd_l"),**lo).pack(anchor="w",padx=15,pady=(10,0))
        rcvd_opts=EXCH_RCVD_OPTIONS.get(L.g(),EXCH_RCVD_OPTIONS["ro"]); self._rcvd_labels={}; self._rcvd_values=[]
        for k,lbl in rcvd_opts.items(): self._rcvd_labels[lbl]=k; self._rcvd_values.append(lbl)
        saved_r=cfg.get("cab2_exch_rcvd","log"); default_rcvd=self._rcvd_values[0]
        for d,k in self._rcvd_labels.items():
            if k==saved_r: default_rcvd=d; break
        self._rcvd_v=tk.StringVar(value=default_rcvd); ttk.Combobox(self,textvariable=self._rcvd_v,values=self._rcvd_values,state="readonly",width=30,font=("Consolas",11)).pack(padx=15,pady=4)
        bf=tk.Frame(self,bg=TH["bg"]); bf.pack(pady=18)
        tk.Button(bf,text=L.t("cab2_export"),command=self._ok,bg=TH["ok"],fg="white",font=("Consolas",12,"bold"),width=14).pack(side="left",padx=8)
        tk.Button(bf,text=L.t("cancel"),command=self.destroy,bg=TH["btn_bg"],fg="white",font=("Consolas",12),width=10).pack(side="left",padx=8)
        center_dialog(self,parent)
    def _ok(self):
        self.result={"sent":self._sent_labels.get(self._sent_v.get(),"none"),"rcvd":self._rcvd_labels.get(self._rcvd_v.get(),"log")}; self.destroy()

class PreviewDialog(tk.Toplevel):
    def __init__(self,parent,title_str,content,save_callback):
        super().__init__(parent); self.title(title_str); self.geometry("750x550"); self.configure(bg=TH["bg"]); self.transient(parent)
        self._save_cb=save_callback; self._content=content
        txt=scrolledtext.ScrolledText(self,bg=TH["entry_bg"],fg=TH["fg"],font=("Consolas",10),wrap="none"); txt.pack(fill="both",expand=True,padx=10,pady=10)
        txt.insert("1.0",content); txt.config(state="disabled")
        bf=tk.Frame(self,bg=TH["bg"]); bf.pack(pady=8)
        tk.Button(bf,text=L.t("save"),command=self._on_save,bg=TH["ok"],fg="white",font=("Consolas",12,"bold"),width=12).pack(side="left",padx=8)
        tk.Button(bf,text=L.t("cancel"),command=self.destroy,bg=TH["btn_bg"],fg="white",font=("Consolas",12),width=12).pack(side="left",padx=8)
        center_dialog(self,parent)
    def _on_save(self): self._save_cb(self._content); self.destroy()


class CATSettingsDialog(tk.Toplevel):
    """Dialog complet pentru configurare si control CAT."""
    def __init__(self, parent, cfg, cat_engine):
        super().__init__(parent)
        self.result = None
        self.cfg = dict(cfg)
        self.cat = cat_engine
        self.title("CAT — Computer Aided Transceiver")
        self.geometry("560x620")
        self.configure(bg=TH["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        center_dialog(self, parent)
        # Focus pe câmpul indicativ — după grab_set trebuie explicit
        self.after(100, lambda: self._e["call"].focus_set())
        self.after(120, lambda: self._e["call"].select_range(0, "end"))
        self._sched_refresh()

    def _build(self):
        lo  = {"bg":TH["bg"], "fg":TH["fg"], "font":("Consolas",11)}
        lo9 = {"bg":TH["bg"], "fg":TH["fg"], "font":("Consolas",9)}
        eo  = {"bg":TH["entry_bg"], "fg":TH["fg"], "font":("Consolas",11),
               "insertbackground":TH["fg"]}

        # ── Titlu ──
        tk.Label(self, text="  CAT — Computer Aided Transceiver",
                 bg=TH["bg"], fg=TH["gold"],
                 font=("Consolas",13,"bold")).pack(fill="x", padx=0, pady=(10,4))

        # ── Status + Freq/Mod live ──
        sf = tk.Frame(self, bg=TH["entry_bg"], bd=1, relief="solid")
        sf.pack(fill="x", padx=16, pady=4)
        row0 = tk.Frame(sf, bg=TH["entry_bg"]); row0.pack(fill="x", padx=8, pady=4)
        self._status_led = tk.Label(row0, text="●", bg=TH["entry_bg"],
                                    fg=TH["err"], font=("Consolas",16))
        self._status_led.pack(side="left")
        self._status_lbl = tk.Label(row0, text="Deconectat / Disconnected",
                                    bg=TH["entry_bg"], fg=TH["fg"], font=("Consolas",11))
        self._status_lbl.pack(side="left", padx=6)
        row1 = tk.Frame(sf, bg=TH["entry_bg"]); row1.pack(fill="x", padx=8, pady=(0,6))
        self._freq_lbl = tk.Label(row1, text="Freq: ---", bg=TH["entry_bg"],
                                  fg=TH["gold"], font=("Consolas",13,"bold"))
        self._freq_lbl.pack(side="left", padx=(0,16))
        self._mode_lbl = tk.Label(row1, text="Mod: ---", bg=TH["entry_bg"],
                                  fg=TH["cyan"], font=("Consolas",12))
        self._mode_lbl.pack(side="left")

        # ── Separator ──
        tk.Frame(self, bg=TH["warn"], height=1).pack(fill="x", padx=16, pady=6)

        # ── Grid cu setari ──
        gf = tk.Frame(self, bg=TH["bg"]); gf.pack(fill="x", padx=16, pady=2)
        gf.columnconfigure(1, weight=1)

        # Protocol
        tk.Label(gf, text="Protocol:", **lo).grid(row=0, column=0, sticky="w", pady=5, padx=(0,10))
        self._prot_v = tk.StringVar(value=self.cfg.get("cat_protocol","Yaesu CAT"))
        self._prot_cb = ttk.Combobox(gf, textvariable=self._prot_v,
                                     values=CAT_PROTOCOLS, state="readonly",
                                     width=26, font=("Consolas",11))
        self._prot_cb.grid(row=0, column=1, sticky="w", pady=5)
        self._prot_cb.bind("<<ComboboxSelected>>", self._on_protocol_change)

        # Port COM
        tk.Label(gf, text="Port COM:", **lo).grid(row=1, column=0, sticky="w", pady=5, padx=(0,10))
        port_frame = tk.Frame(gf, bg=TH["bg"]); port_frame.grid(row=1, column=1, sticky="w", pady=5)
        ports = CATEngine.list_ports()
        if not ports: ports = [""]
        saved = self.cfg.get("cat_port","")
        if saved and saved not in ports: ports.insert(0, saved)
        self._port_v = tk.StringVar(value=saved or ports[0])
        self._port_cb = ttk.Combobox(port_frame, textvariable=self._port_v,
                                     values=ports, width=12, font=("Consolas",11))
        self._port_cb.pack(side="left")
        tk.Button(port_frame, text="Refresh", command=self._refresh_ports,
                  bg=TH["btn_bg"], fg="white", font=("Consolas",9),
                  width=7).pack(side="left", padx=6)

        # Baud
        tk.Label(gf, text="Baud Rate:", **lo).grid(row=2, column=0, sticky="w", pady=5, padx=(0,10))
        self._baud_v = tk.StringVar(value=str(self.cfg.get("cat_baud",38400)))
        ttk.Combobox(gf, textvariable=self._baud_v,
                     values=["1200","2400","4800","9600","19200","38400","57600","115200"],
                     state="readonly", width=12, font=("Consolas",11)).grid(row=2, column=1, sticky="w", pady=5)

        # CI-V Address
        self._civ_row_lbl = tk.Label(gf, text="CI-V Adresa (hex):", **lo)
        self._civ_row_lbl.grid(row=3, column=0, sticky="w", pady=5, padx=(0,10))
        civ_f = tk.Frame(gf, bg=TH["bg"]); civ_f.grid(row=3, column=1, sticky="w", pady=5)
        self._civ_e = tk.Entry(civ_f, width=6, **eo)
        self._civ_e.insert(0, self.cfg.get("cat_civaddr","94"))
        self._civ_e.pack(side="left")
        tk.Label(civ_f, text="  94=IC-7300  A2=IC-705  76=IC-7100",
                 **lo9).pack(side="left")

        # Hamlib host
        self._ham_row_lbl = tk.Label(gf, text="Hamlib Host:", **lo)
        self._ham_row_lbl.grid(row=4, column=0, sticky="w", pady=5, padx=(0,10))
        ham_f = tk.Frame(gf, bg=TH["bg"]); ham_f.grid(row=4, column=1, sticky="w", pady=5)
        self._ham_host_e = tk.Entry(ham_f, width=14, **eo)
        self._ham_host_e.insert(0, self.cfg.get("cat_hamlib_host","localhost"))
        self._ham_host_e.pack(side="left")
        tk.Label(ham_f, text=" Port:", **lo).pack(side="left")
        self._ham_port_e = tk.Entry(ham_f, width=6, **eo)
        self._ham_port_e.insert(0, str(self.cfg.get("cat_hamlib_port",4532)))
        self._ham_port_e.pack(side="left", padx=4)

        # Hamlib help text
        self._ham_help_lbl = tk.Label(gf,
            text="Porneste: rigctld -m 122 -r COM3 -s 38400 (FT-891)  |  rigctld -m 3061 -r COM4 (IC-7300)",
            bg=TH["bg"], fg=TH["warn"], font=("Consolas",8), justify="left")
        self._ham_help_lbl.grid(row=5, column=0, columnspan=2, sticky="w", pady=2)

        # ── Separator ──
        tk.Frame(self, bg=TH["accent"], height=1).pack(fill="x", padx=16, pady=8)

        # ── Butoane Conectare ──
        cb = tk.Frame(self, bg=TH["bg"]); cb.pack(pady=4)
        tk.Button(cb, text="  Conecteaza / Connect  ", command=self._connect,
                  bg=TH["ok"], fg="white",
                  font=("Consolas",11,"bold")).pack(side="left", padx=6)
        tk.Button(cb, text="  Deconecteaza  ", command=self._disconnect,
                  bg=TH["err"], fg="white",
                  font=("Consolas",11)).pack(side="left", padx=6)

        # ── Test frecventa spre radio ──
        tf2 = tk.Frame(self, bg=TH["bg"]); tf2.pack(pady=4)
        tk.Label(tf2, text="Test freq -> Radio:", **lo).pack(side="left")
        self._test_freq_e = tk.Entry(tf2, width=8, **eo)
        self._test_freq_e.insert(0, "14200")
        self._test_freq_e.pack(side="left", padx=6)
        tk.Button(tf2, text="Trimite / Send", command=self._test_set_freq,
                  bg=TH["accent"], fg="white",
                  font=("Consolas",10)).pack(side="left", padx=4)

        # ── Salvare / Inchide ──
        tk.Frame(self, bg=TH["btn_bg"], height=1).pack(fill="x", padx=16, pady=6)
        bf2 = tk.Frame(self, bg=TH["bg"]); bf2.pack(pady=8)
        tk.Button(bf2, text="  Salveaza / Save  ", command=self._save,
                  bg=TH["accent"], fg="white",
                  font=("Consolas",11,"bold")).pack(side="left", padx=8)
        tk.Button(bf2, text="  Inchide  ", command=self.destroy,
                  bg=TH["btn_bg"], fg="white",
                  font=("Consolas",11)).pack(side="left", padx=8)

        # Aplica vizibilitate initiala
        self._on_protocol_change()

    def _on_protocol_change(self, e=None):
        proto = self._prot_v.get()
        is_icom   = (proto == "Icom CI-V")
        is_hamlib = (proto == "Hamlib/rigctld")

        # CI-V row: show/hide
        if is_icom:
            self._civ_row_lbl.grid()
            self._civ_e.master.grid()
        else:
            self._civ_row_lbl.grid_remove()
            self._civ_e.master.grid_remove()

        # Hamlib rows: show/hide
        if is_hamlib:
            self._ham_row_lbl.grid()
            self._ham_host_e.master.grid()
            self._ham_help_lbl.grid()
        else:
            self._ham_row_lbl.grid_remove()
            self._ham_host_e.master.grid_remove()
            self._ham_help_lbl.grid_remove()

        # Baud default pentru protocol
        default_baud = CAT_BAUD_DEFAULTS.get(proto, 9600)
        self._baud_v.set(str(default_baud))

    def _refresh_ports(self):
        ports = CATEngine.list_ports()
        if not ports: ports = ["(niciun port)"]
        self._port_cb["values"] = ports
        if ports: self._port_v.set(ports[0])

    def _connect(self):
        self._collect_cfg()
        ok, msg = self.cat.connect(self.cfg)
        color = TH["ok"] if ok else TH["err"]
        self._status_led.config(fg=color)
        self._status_lbl.config(text=msg, fg=color)

    def _disconnect(self):
        self.cat.disconnect()
        self._status_led.config(fg=TH["err"])
        self._status_lbl.config(text="Deconectat / Disconnected", fg=TH["fg"])
        self._freq_lbl.config(text="Freq: ---")
        self._mode_lbl.config(text="Mod: ---")

    def _test_set_freq(self):
        khz = self._test_freq_e.get().strip()
        if self.cat.set_freq(khz):
            messagebox.showinfo("CAT", f"Frecventa trimisa: {khz} kHz")
        else:
            messagebox.showwarning("CAT", "Nu s-a putut trimite frecventa. Verifica conexiunea CAT.")

    def _collect_cfg(self):
        self.cfg["cat_protocol"]     = self._prot_v.get()
        self.cfg["cat_port"]         = self._port_v.get()
        self.cfg["cat_civaddr"]      = self._civ_e.get().strip()
        self.cfg["cat_hamlib_host"]  = self._ham_host_e.get().strip()
        try:    self.cfg["cat_hamlib_port"] = int(self._ham_port_e.get().strip())
        except: self.cfg["cat_hamlib_port"] = 4532
        try:    self.cfg["cat_baud"] = int(self._baud_v.get())
        except: self.cfg["cat_baud"] = 9600
        self.cfg["cat_enabled"] = self.cat.connected

    def _save(self):
        self._collect_cfg()
        self.result = self.cfg
        self.destroy()

    def _refresh_status(self):
        try:
            if not self.winfo_exists(): return
            if self.cat.connected:
                self._status_led.config(fg=TH["ok"])
                self._status_lbl.config(
                    text=f"Conectat: {self.cat.protocol}", fg=TH["ok"])
                if self.cat.last_freq:
                    self._freq_lbl.config(text=f"Freq: {self.cat.last_freq} kHz")
                if self.cat.last_mode:
                    self._mode_lbl.config(text=f"Mod: {self.cat.last_mode}")
            else:
                self._status_led.config(fg=TH["err"])
                if self.cat.last_error:
                    self._status_lbl.config(
                        text=f"Eroare: {self.cat.last_error[:40]}", fg=TH["err"])
        except: pass

    def _sched_refresh(self):
        try:
            if not self.winfo_exists(): return
            self._refresh_status()
            self.after(1000, self._sched_refresh)
        except: pass


class NewLogDialog(tk.Toplevel):
    def __init__(self, parent, contests):
        super().__init__(parent)
        self.result = None
        self.contests = contests
        self.title("📝 Log Nou / New Log")
        self.geometry("420x260")
        self.configure(bg=TH["bg"])
        self.transient(parent)
        self.grab_set()
        lo = {"bg":TH["bg"],"fg":TH["fg"],"font":("Consolas",11)}
        eo = {"bg":TH["entry_bg"],"fg":TH["fg"],"font":("Consolas",11),"insertbackground":TH["fg"]}
        tk.Label(self, text="📝 Creare Log Nou / New Log", bg=TH["bg"], fg=TH["gold"],
                 font=("Consolas",13,"bold")).pack(pady=(14,8))
        tk.Label(self, text="Concurs / Contest:", **lo).pack(anchor="w", padx=20)
        self._cid_v = tk.StringVar(value=list(contests.keys())[0])
        ttk.Combobox(self, textvariable=self._cid_v, values=list(contests.keys()),
                     state="readonly", width=28, font=("Consolas",11)).pack(padx=20, pady=4, anchor="w")
        tk.Label(self, text="Nume log / Log name:", **lo).pack(anchor="w", padx=20)
        self._name_e = tk.Entry(self, width=30, **eo)
        self._name_e.insert(0, datetime.datetime.now().strftime("%Y%m%d"))
        self._name_e.pack(padx=20, pady=4, anchor="w")
        tk.Label(self, text="⚠ Logul curent se salvează automat!",
                 bg=TH["bg"], fg=TH["warn"], font=("Consolas",9)).pack(pady=4)
        bf = tk.Frame(self, bg=TH["bg"]); bf.pack(pady=8)
        tk.Button(bf, text="✅ Crează", command=self._ok,
                  bg=TH["ok"], fg="white", font=("Consolas",11,"bold"), width=14).pack(side="left", padx=6)
        tk.Button(bf, text="✖ Anulează", command=self.destroy,
                  bg=TH["btn_bg"], fg="white", font=("Consolas",11), width=12).pack(side="left", padx=6)
        center_dialog(self, parent)

    def _ok(self):
        cid  = self._cid_v.get().strip()
        name = re.sub(r"[^a-zA-Z0-9_-]","_",self._name_e.get().strip()) or datetime.datetime.now().strftime("%Y%m%d_%H%M")
        self.result = {"contest":cid, "log_id":f"{cid}__{name}"}
        self.destroy()


class ThemeDialog(tk.Toplevel):
    def __init__(self, parent, current_theme, custom_colors):
        super().__init__(parent)
        self.result = None
        self.current_theme = current_theme
        self.custom = dict(custom_colors)
        self.title("🎨 Teme și Culori / Themes & Colors")
        self.geometry("620x540")
        self.configure(bg=TH["bg"])
        self.transient(parent)
        self.grab_set()
        self._build()
        center_dialog(self, parent)
        # Focus pe câmpul indicativ — după grab_set trebuie explicit
        self.after(100, lambda: self._e["call"].focus_set())
        self.after(120, lambda: self._e["call"].select_range(0, "end"))

    def _build(self):
        lo = {"bg":TH["bg"],"fg":TH["fg"],"font":("Consolas",11)}
        tk.Label(self, text="🎨 Teme / Themes", bg=TH["bg"], fg=TH["gold"],
                 font=("Consolas",13,"bold")).pack(pady=(12,4))
        tf = tk.Frame(self, bg=TH["bg"]); tf.pack(fill="x", padx=20, pady=4)
        tk.Label(tf, text="Temă predefinită:", **lo).pack(side="left")
        self._theme_v = tk.StringVar(value=self.current_theme)
        tcb = ttk.Combobox(tf, textvariable=self._theme_v, values=list(THEMES.keys()),
                           state="readonly", width=22, font=("Consolas",11))
        tcb.pack(side="left", padx=8)
        tk.Button(tf, text="↺ Aplică", command=self._apply_preset,
                  bg=TH["accent"], fg="white", font=("Consolas",10), width=10).pack(side="left", padx=4)
        self._prev_frame = tk.Frame(self, bg=TH["bg"], bd=1, relief="solid")
        self._prev_frame.pack(fill="x", padx=20, pady=6)
        self._draw_preview(self.custom if self.custom else THEMES.get(self.current_theme, TH))
        sep = tk.Frame(self, bg=TH["warn"], height=1); sep.pack(fill="x", padx=20, pady=4)
        tk.Label(self, text="✏ Personalizare culori:", bg=TH["bg"], fg=TH["cyan"],
                 font=("Consolas",11,"bold")).pack(anchor="w", padx=20)
        cf = tk.Frame(self, bg=TH["bg"]); cf.pack(fill="both", expand=True, padx=20, pady=4)
        self._color_entries = {}
        color_labels = {"bg":"Fundal","fg":"Text","accent":"Accent",
                        "entry_bg":"Câmpuri","header_bg":"Header",
                        "gold":"Clock/Score","ok":"OK","err":"Eroare","warn":"Avertisment"}
        base = self.custom if self.custom else THEMES.get(self.current_theme, TH)
        for i,(k,lbl) in enumerate(color_labels.items()):
            r,c = divmod(i,3)
            fr = tk.Frame(cf, bg=TH["bg"]); fr.grid(row=r, column=c, padx=6, pady=3, sticky="w")
            tk.Label(fr, text=lbl, bg=TH["bg"], fg=TH["fg"], font=("Consolas",9)).pack(anchor="w")
            ef = tk.Frame(fr, bg=TH["bg"]); ef.pack(fill="x")
            e = tk.Entry(ef, width=9, bg=TH["entry_bg"], fg=TH["fg"],
                         font=("Consolas",10), insertbackground=TH["fg"], justify="center")
            e.insert(0, base.get(k,"#ffffff")); e.pack(side="left")
            sw = tk.Label(ef, text="  ", bg=base.get(k,"#ffffff"), width=2); sw.pack(side="left", padx=2)
            def _pick(ev, key=k, entry=e, swatch=sw):
                from tkinter import colorchooser
                col = colorchooser.askcolor(color=entry.get(), title=f"Culoare: {key}")
                if col and col[1]:
                    entry.delete(0,"end"); entry.insert(0,col[1])
                    try: swatch.config(bg=col[1])
                    except: pass
            e.bind("<Double-Button-1>", _pick); sw.bind("<Button-1>", _pick)
            e.bind("<FocusOut>", lambda ev,s=sw,en=e: self._upd_sw(ev,s,en))
            self._color_entries[k] = e
        bf = tk.Frame(self, bg=TH["bg"]); bf.pack(pady=10)
        tk.Button(bf, text="✅ Salvează", command=self._save,
                  bg=TH["ok"], fg="white", font=("Consolas",11,"bold"), width=14).pack(side="left", padx=6)
        tk.Button(bf, text="↺ Reset", command=self._reset,
                  bg=TH["warn"], fg="white", font=("Consolas",10), width=10).pack(side="left", padx=6)
        tk.Button(bf, text="✖ Anulează", command=self.destroy,
                  bg=TH["btn_bg"], fg="white", font=("Consolas",11), width=10).pack(side="left", padx=6)

    def _upd_sw(self, ev, sw, e):
        try: sw.config(bg=e.get())
        except: pass

    def _draw_preview(self, colors):
        for w in self._prev_frame.winfo_children(): w.destroy()
        pf = tk.Frame(self._prev_frame, bg=colors.get("bg","#000"), pady=4); pf.pack(fill="x")
        tk.Label(pf, text=" YO Log PRO ", bg=colors.get("header_bg","#000"),
                 fg=colors.get("gold","#ffd700"), font=("Consolas",10,"bold")).pack(side="left", padx=6)
        rf = tk.Frame(self._prev_frame, bg=colors.get("bg","#000"), pady=2); rf.pack(fill="x", padx=6)
        tk.Entry(rf, width=10, bg=colors.get("entry_bg","#000"),
                 fg=colors.get("gold","#ffd700"), font=("Consolas",10)).pack(side="left", padx=4)
        tk.Button(rf, text="LOG", bg=colors.get("accent","#1f6feb"), fg="white",
                  font=("Consolas",9,"bold")).pack(side="left", padx=4)
        for lbl,col_k in [(" OK ","ok"),(" WARN ","warn"),(" ERR ","err")]:
            tk.Label(rf, text=lbl, bg=colors.get("bg","#000"),
                     fg=colors.get(col_k,"#fff"), font=("Consolas",9,"bold")).pack(side="left")

    def _apply_preset(self):
        preset = THEMES.get(self._theme_v.get(), {})
        for k,e in self._color_entries.items():
            e.delete(0,"end"); e.insert(0, preset.get(k, TH.get(k,"#ffffff")))
            for ch in e.master.winfo_children():
                if isinstance(ch, tk.Label):
                    try: ch.config(bg=preset.get(k,"#ffffff"))
                    except: pass
        self._draw_preview(preset)

    def _reset(self):
        self._theme_v.set("Dark Blue (implicit)"); self._apply_preset()

    def _save(self):
        colors = dict(THEMES.get(self._theme_v.get(), TH))
        for k,e in self._color_entries.items():
            v = e.get().strip()
            if v.startswith("#") and len(v) in (4,7): colors[k] = v
        self.result = {"theme":self._theme_v.get(), "colors":colors}
        self.destroy()


class FirstRunDialog(tk.Toplevel):
    """Dialog prima utilizare — apare automat la primul start."""
    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.cfg = cfg
        self.result = None
        self.title("YO Log PRO v17.1 — Configurare initiala / First Setup")
        self.geometry("560x680")
        self.configure(bg=TH["bg"])
        self.resizable(True, True)
        self.minsize(480, 580)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._save)  # nu permite inchidere fara salvare
        self._build()
        center_dialog(self, parent)
        # Focus pe câmpul indicativ — după grab_set trebuie explicit
        self.after(150, self._focus_first)

    def _build(self):
        lo  = {"bg":TH["bg"], "fg":TH["fg"],   "font":("Consolas",11)}
        lob = {"bg":TH["bg"], "fg":TH["gold"],  "font":("Consolas",12,"bold")}
        lo9 = {"bg":TH["bg"], "fg":TH["warn"],  "font":("Consolas",9)}
        eo  = {"bg":TH["entry_bg"], "fg":TH["gold"], "font":("Consolas",13,"bold"),
               "insertbackground":"white", "justify":"center",
               "relief":"solid", "bd":2, "highlightthickness":2,
               "highlightcolor":TH["accent"], "highlightbackground":TH["entry_bg"]}
        eon = {"bg":TH["entry_bg"], "fg":"white", "font":("Consolas",11),
               "insertbackground":"white", "relief":"solid", "bd":1}

        # ── Banner ──
        banner = tk.Frame(self, bg=TH["header_bg"], pady=12)
        banner.pack(fill="x")
        tk.Label(banner, text="📻  YO Log PRO v17.1",
                 bg=TH["header_bg"], fg=TH["gold"],
                 font=("Consolas",16,"bold")).pack()
        tk.Label(banner, text="Full Edition — Amateur Radio Logger",
                 bg=TH["header_bg"], fg=TH["cyan"],
                 font=("Consolas",10)).pack()
        tk.Label(banner, text="Developed by Ardei Constantin-Catalin (YO8ACR)",
                 bg=TH["header_bg"], fg=TH["fg"],
                 font=("Consolas",9)).pack(pady=(2,0))

        # ── Titlu sectiune ──
        tk.Label(self, text="  Configurare initiala / Initial Setup",
                 bg=TH["bg"], fg=TH["cyan"],
                 font=("Consolas",11,"bold")).pack(anchor="w", padx=16, pady=(12,4))

        tk.Frame(self, bg=TH["warn"], height=1).pack(fill="x", padx=16, pady=(0,8))

        # ── Grid campuri ──
        gf = tk.Frame(self, bg=TH["bg"])
        gf.pack(fill="x", padx=16)
        gf.columnconfigure(1, weight=1)

        def row(r, label, key, default, entry_opts, hint=None, upper=False):
            tk.Label(gf, text=label, **lo).grid(
                row=r*2, column=0, sticky="w", pady=(6,0), padx=(0,12))
            e = tk.Entry(gf, width=28, **entry_opts)
            e.insert(0, self.cfg.get(key, default))
            if upper:
                def _make_upper(en):
                    def _upper_cb(ev):
                        txt = en.get().upper()
                        pos = en.index(tk.INSERT)
                        en.delete(0, "end")
                        en.insert(0, txt)
                        try: en.icursor(min(pos, len(txt)))
                        except Exception: pass
                    en.bind("<KeyRelease>", _upper_cb)
                _make_upper(e)
            e.grid(row=r*2, column=1, sticky="ew", pady=(6,0))
            if hint:
                tk.Label(gf, text=hint, **lo9).grid(
                    row=r*2+1, column=1, sticky="w", pady=(0,2))
            return e

        self._e = {}
        self._e["call"]    = row(0, "Indicativ / Callsign *", "call",    "",  eo,
                                  "Indicativul tau de radioamator", upper=True)
        self._e["loc"]     = row(1, "Locator Maidenhead *",   "loc",     "KN37",    eo,
                                  "Grid locator (ex: KN37, JO21, ...)", upper=True)
        self._e["jud"]     = row(2, "Judet / County",         "jud",     "NT",      eo,
                                  "Cod judet 2 litere (ex: NT, IS, BV...)", upper=True)
        self._e["op_name"] = row(3, "Nume operator / Name",   "op_name", "",        eon,
                                  "Prenume si Nume (pentru exporturi)")
        self._e["addr"]    = row(4, "Adresa / Address",       "addr",    "",        eon,
                                  "Adresa postala (optional, pentru exporturi)")
        self._e["power"]   = row(5, "Putere TX / TX Power",   "power",   "100",     eon,
                                  "Putere in wati (ex: 100)")
        self._e["email"]   = row(6, "Email",                  "email",   "",        eon,
                                  "Email de contact (optional)")

        # ── Limba / Language ──
        tk.Label(gf, text="Limba / Language", **lo).grid(
            row=14, column=0, sticky="w", pady=(10,0), padx=(0,12))
        self._lang_v = tk.StringVar(value=self.cfg.get("lang","ro"))
        lf2 = tk.Frame(gf, bg=TH["bg"]); lf2.grid(row=14, column=1, sticky="w", pady=(10,0))
        for lcode, lname in [("ro","🇷🇴 Română"), ("en","🇬🇧 English")]:
            tk.Radiobutton(lf2, text=lname, variable=self._lang_v, value=lcode,
                           bg=TH["bg"], fg=TH["fg"], selectcolor=TH["entry_bg"],
                           activebackground=TH["bg"],
                           font=("Consolas",11)).pack(side="left", padx=8)

        # ── Nota obligatorie ──
        tk.Frame(self, bg=TH["accent"], height=1).pack(fill="x", padx=16, pady=(12,4))
        tk.Label(self,
                 text="* Indicativul si Locatorul sunt obligatorii pentru export corect.",
                 bg=TH["bg"], fg=TH["warn"], font=("Consolas",9)).pack(anchor="w", padx=16)

        # ── Butoane ──
        bf = tk.Frame(self, bg=TH["bg"]); bf.pack(pady=14)
        tk.Button(bf,
                  text="  ✅  Salveaza si Incepe / Save & Start  ",
                  command=self._save,
                  bg=TH["ok"], fg="white",
                  font=("Consolas",12,"bold")).pack()

    def _focus_first(self):
        """Focus pe primul câmp obligatoriu."""
        try:
            e = self._e.get("call")
            if e:
                e.focus_set()
                e.icursor("end")
        except Exception:
            pass

    def _save(self):
        call = self._e["call"].get().strip().upper()
        if not call:
            messagebox.showwarning("Atentie", "Indicativul este obligatoriu!")
            self._e["call"].focus_set(); return

        for k, e in self._e.items():
            v = e.get().strip()
            self.cfg[k] = v.upper() if k in {"call","loc","jud"} else v

        self.cfg["lang"] = self._lang_v.get()
        self.cfg["first_run"] = False
        self.result = self.cfg
        self.destroy()



# ═══════════════════════════════════════════════════════════
# LOG EDITOR — Editor dedicat log cu toate funcțiile
# ═══════════════════════════════════════════════════════════

class LogEditorWindow(tk.Toplevel):
    """Fereastră dedicată pentru editarea completă a logului.
    Independentă de fereastra principală — poate rula separat."""

    def __init__(self, parent, log_ref, contests_ref, cfg_ref,
                 on_change=None, cid_getter=None):
        super(LogEditorWindow, self).__init__(parent)
        self._log       = log_ref        # referință la lista log din App
        self._contests  = contests_ref
        self._cfg       = cfg_ref
        self._on_change = on_change      # callback când logul se modifică
        self._cid_getter = cid_getter    # lambda -> cid curent
        self._edit_idx  = None
        self._sort_col  = None
        self._sort_rev  = False

        self.title("📝 Log Editor — YO Log PRO v17.1")
        self.geometry("1200x680")
        self.configure(bg=TH["bg"])
        self.resizable(True, True)
        self._build()
        self._refresh()
        # Focus pe câmpul indicativ
        self.after(150, self._focus_call_field)

    # ── UI ──────────────────────────────────────────────────
    def _build(self):
        # ─ Toolbar ─
        tb = tk.Frame(self, bg=TH["header_bg"], pady=5)
        tb.pack(fill="x")
        tk.Label(tb, text="📝 Log Editor",
                 bg=TH["header_bg"], fg=TH["gold"],
                 font=("Consolas", 12, "bold")).pack(side="left", padx=10)

        # Butoane toolbar
        self._save_btn = tk.Button(tb, text="💾 Salvează",
                                    command=self._save_entry,
                                    bg=TH["ok"], fg="white",
                                    font=("Consolas", 10, "bold"), width=12)
        self._save_btn.pack(side="left", padx=2)

        for lbl, cmd, col, w in [
            ("🗑 Șterge",    self._delete_sel,  TH["err"],    10),
            ("↩ Undo",       self._undo,         TH["warn"],   8),
            ("🔍 Căutare",   self._do_search,    TH["accent"], 10),
            ("🌐 Callbook",  self._callbook_sel, "#1a5276",    10),
            ("↺ Refresh",    self._refresh,      TH["btn_bg"], 9),
        ]:
            tk.Button(tb, text=lbl, command=cmd,
                      bg=col, fg="white",
                      font=("Consolas", 10), width=w).pack(side="left", padx=2)

        # Status
        self._status = tk.Label(tb, text="", bg=TH["header_bg"],
                                 fg=TH["fg"], font=("Consolas", 9))
        self._status.pack(side="right", padx=8)

        # ─ Search bar ─
        sf = tk.Frame(self, bg=TH["bg"], pady=3)
        sf.pack(fill="x", padx=8)
        tk.Label(sf, text="🔍 Filtru rapid:",
                 bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="left")
        self._search_v = tk.StringVar()
        se = tk.Entry(sf, textvariable=self._search_v, width=20,
                      bg=TH["entry_bg"], fg=TH["gold"],
                      font=("Consolas", 10), insertbackground=TH["fg"])
        se.pack(side="left", padx=4)
        se.bind("<KeyRelease>", lambda e: self._refresh())

        tk.Label(sf, text="Bandă:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="left", padx=(8,0))
        self._fband_v = tk.StringVar(value="Toate")
        bb = ttk.Combobox(sf, textvariable=self._fband_v,
                          values=["Toate"] + BANDS_ALL,
                          state="readonly", width=7)
        bb.pack(side="left", padx=4)
        bb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(sf, text="Mod:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="left")
        self._fmode_v = tk.StringVar(value="Toate")
        mb2 = ttk.Combobox(sf, textvariable=self._fmode_v,
                           values=["Toate"] + MODES_ALL,
                           state="readonly", width=7)
        mb2.pack(side="left", padx=4)
        mb2.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        self._count_lbl = tk.Label(sf, text="", bg=TH["bg"],
                                    fg=TH["gold"], font=("Consolas", 9, "bold"))
        self._count_lbl.pack(side="right", padx=8)

        # ─ Treeview ─
        tf = tk.Frame(self, bg=TH["bg"])
        tf.pack(fill="both", expand=True, padx=8, pady=(0,4))

        cols = ("nr","call","freq","band","mode","rst_s","rst_r",
                "ss","sr","note","country","date","time","pts")
        hdrs = ["Nr","Indicativ","Freq","Bandă","Mod","RST S","RST R",
                "Nr S","Nr R","Notă","Țara","Dată","Oră","Pt"]
        wids = [38,110,75,55,55,48,48,45,45,95,95,88,50,45]

        self._tree = ttk.Treeview(tf, columns=cols, show="headings",
                                   selectmode="extended")
        for c, h, w in zip(cols, hdrs, wids):
            self._tree.heading(c, text=h,
                               command=lambda col=c: self._sort(col))
            self._tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal",  command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        self._tree.tag_configure("dup",  background=TH["dup_bg"])
        self._tree.tag_configure("alt",  background=TH["alt"])
        self._tree.tag_configure("spec", background=TH["spec_bg"])
        self._tree.tag_configure("sel",  background=TH["accent"])

        self._tree.bind("<Double-1>",  lambda e: self._load_into_form())
        self._tree.bind("<Delete>",    lambda e: self._delete_sel())
        self._tree.bind("<Button-3>",  self._ctx_menu)
        # Scroll cu rotița mouse-ului
        self._tree.bind("<MouseWheel>",
            lambda e: self._tree.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._tree.bind("<Button-4>",
            lambda e: self._tree.yview_scroll(-1,"units"))
        self._tree.bind("<Button-5>",
            lambda e: self._tree.yview_scroll(1,"units"))

        # ─ Edit Form — 2 rânduri grid clar ─
        ef = tk.LabelFrame(self,
                           text=" ✏ Editare QSO — dublu-click pe rând, modifică câmpurile și apasă Salvează ",
                           bg=TH["bg"], fg=TH["gold"],
                           font=("Consolas", 9, "bold"), pady=6, padx=10)
        ef.pack(fill="x", padx=8, pady=(0,6))

        EO = dict(bg=TH["entry_bg"], fg=TH["gold"],
                  font=("Consolas", 11), insertbackground="white",
                  relief="solid", bd=1, justify="center")
        LO = dict(bg=TH["bg"], fg="#aaaaaa", font=("Consolas", 8))

        self._ent = {}

        # Rândul 1: Call | Freq | Bandă | Mod | RST S | RST R | [Salvează] [Anulează]
        r1 = tk.Frame(ef, bg=TH["bg"]); r1.pack(fill="x", pady=(4,2))

        def _lbl_ent(parent, label, key, width, is_combo=False, combo_vals=None):
            """Helper: label deasupra + widget intrare."""
            frm = tk.Frame(parent, bg=TH["bg"])
            frm.pack(side="left", padx=4)
            tk.Label(frm, text=label, **LO).pack(anchor="w")
            if is_combo:
                v = tk.StringVar()
                w = ttk.Combobox(frm, textvariable=v,
                                 values=combo_vals or [], state="normal",
                                 width=width, font=("Consolas",11))
                w.pack()
                self._ent[key] = v
                return v, w
            else:
                e = tk.Entry(frm, width=width, **EO)
                e.pack()
                self._ent[key] = e
                return e, e

        # — Rândul 1 —
        ce, _ = _lbl_ent(r1, "Indicativ", "call", 12)
        ce.bind("<KeyRelease>", self._on_call_key)
        # Buton callbook lângă câmpul indicativ
        _cb_frm = tk.Frame(r1, bg=TH["bg"])
        _cb_frm.pack(side="left", padx=0)
        tk.Label(_cb_frm, text=" ", **dict(bg=TH["bg"], fg=TH["bg"], font=("Consolas",8))).pack()
        tk.Button(_cb_frm, text="🌐", command=self._callbook_form,
                  bg="#1a5276", fg="white",
                  font=("Consolas",9), width=2).pack()

        _lbl_ent(r1, "Freq (kHz)", "freq", 9)
        _lbl_ent(r1, "Bandă",  "band", 7, is_combo=True, combo_vals=BANDS_ALL)
        _lbl_ent(r1, "Mod",    "mode", 7, is_combo=True, combo_vals=MODES_ALL)
        _lbl_ent(r1, "RST S",  "rst_s", 5)
        _lbl_ent(r1, "RST R",  "rst_r", 5)

        # Butoane Salvează / Anulează în rândul 1, dreapta
        bf_r = tk.Frame(r1, bg=TH["bg"]); bf_r.pack(side="right", padx=8)
        self._save_btn2 = tk.Button(bf_r, text="💾 Salvează",
                                     command=self._save_entry,
                                     bg=TH["ok"], fg="white",
                                     font=("Consolas",10,"bold"), width=12)
        self._save_btn2.pack(pady=1)
        tk.Button(bf_r, text="✖ Anulează", command=self._cancel_edit,
                  bg=TH["btn_bg"], fg="white",
                  font=("Consolas",9), width=12).pack(pady=1)

        # — Rândul 2: Nr S | Nr R | Notă | Dată | Oră —
        r2 = tk.Frame(ef, bg=TH["bg"]); r2.pack(fill="x", pady=(2,4))
        _lbl_ent(r2, "Nr Serial S", "ss",   7)
        _lbl_ent(r2, "Nr Serial R", "sr",   7)
        _lbl_ent(r2, "Notă / Locator", "note", 22)
        _lbl_ent(r2, "Dată (YYYY-MM-DD)", "date", 12)
        _lbl_ent(r2, "Oră (HH:MM)", "time", 8)

        # Undo stack local
        self._undo_stack = deque(maxlen=50)

    # ── Context menu ───────────────────────────────────────
    def _ctx_menu(self, event):
        ctx = tk.Menu(self, tearoff=0)
        ctx.add_command(label="✏ Editează",    command=self._load_into_form)
        ctx.add_command(label="🗑 Șterge",      command=self._delete_sel)
        ctx.add_command(label="🌐 Callbook",    command=self._callbook_sel)
        ctx.add_separator()
        ctx.add_command(label="📋 Copiază call",command=self._copy_call)
        ctx.add_command(label="🔗 QRZ.com",     command=lambda: self._open_qrz(self._sel_call()))
        ctx.add_command(label="🔗 radioamator.ro", command=lambda: self._open_ro(self._sel_call()))
        ctx.post(event.x_root, event.y_root)

    def _sel_call(self):
        sel = self._tree.selection()
        if not sel: return ""
        try:
            idx = int(sel[0])
            return self._log[idx].get("c", "")
        except Exception:
            return ""

    def _copy_call(self):
        call = self._sel_call()
        if call:
            try:
                self.clipboard_clear()
                self.clipboard_append(call)
            except Exception:
                pass

    # ── Treeview ───────────────────────────────────────────
    def _refresh(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        fq   = self._search_v.get().upper().strip()
        fb   = self._fband_v.get()
        fm   = self._fmode_v.get()
        cc   = self._cc()
        hs   = cc.get("scoring_mode", "none") != "none"
        sp   = set((cc.get("special_scoring") or {}).keys())
        seen = set()
        shown = 0

        for i, q in enumerate(self._log):
            b, m, c = q.get("b",""), q.get("m",""), q.get("c","").upper()
            if fb != "Toate" and b != fb:   continue
            if fm != "Toate" and m != fm:   continue
            if fq and fq not in c and fq not in q.get("n","").upper(): continue

            nr      = len(self._log) - i
            key     = (c, b, m)
            tag     = ("dup",)  if key in seen else                       ("spec",) if c in sp     else                       ("alt",)  if i % 2 == 0  else ()
            seen.add(key)
            country, _ = DXCC.lookup(c)
            pts = Score.qso(q, cc, self._cfg) if hs else ""

            vals = (
                nr, c,
                q.get("f",""), b, m,
                q.get("s","59"), q.get("r","59"),
                q.get("ss",""), q.get("sr",""),
                q.get("n",""),
                country if country != "Unknown" else "",
                q.get("d",""), q.get("t",""),
                pts
            )
            self._tree.insert("", "end", iid=str(i), values=vals, tags=tag)
            shown += 1

        self._count_lbl.config(
            text=f"Afișat: {shown}/{len(self._log)} QSO")
        self._set_status(f"Log: {len(self._log)} QSO total")

    def _sort(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        items = [(self._tree.set(k, col), k)
                 for k in self._tree.get_children("")]
        try:
            items.sort(key=lambda x: float(x[0]) if x[0].lstrip("-").replace(".","").isdigit() else x[0],
                       reverse=self._sort_rev)
        except Exception:
            items.sort(key=lambda x: x[0], reverse=self._sort_rev)
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)

    # ── Form helpers ───────────────────────────────────────
    def _load_into_form(self):
        sel = self._tree.selection()
        if not sel: return
        try:
            idx = int(sel[0])
        except Exception:
            return
        if idx < 0 or idx >= len(self._log):
            return
        self._edit_idx = idx
        q = self._log[idx]

        def _set(key, val):
            w = self._ent.get(key)
            if w is None: return
            if isinstance(w, tk.StringVar):
                w.set(val)
            else:
                w.delete(0, "end")
                w.insert(0, val)

        _set("call",  q.get("c",""))
        _set("freq",  q.get("f",""))
        _set("band",  q.get("b",""))
        _set("mode",  q.get("m",""))
        _set("rst_s", q.get("s","59"))
        _set("rst_r", q.get("r","59"))
        _set("ss",    q.get("ss",""))
        _set("sr",    q.get("sr",""))
        _set("note",  q.get("n",""))
        _set("date",  q.get("d",""))
        _set("time",  q.get("t",""))

        if self._save_btn:
            self._save_btn.config(text="💾 Actualizează", bg=TH["warn"])
        if self._save_btn2:
            self._save_btn2.config(text="💾 Actualizează", bg=TH["warn"])
        self._set_status(f"Editezi QSO #{len(self._log)-idx}: {q.get('c','')}")

    def _get_form(self):
        def _get(key):
            w = self._ent.get(key)
            if w is None: return ""
            return w.get().strip() if not isinstance(w, tk.StringVar) else w.get()
        return {
            "c": _get("call").upper(),
            "f": _get("freq"),
            "b": _get("band"),
            "m": _get("mode"),
            "s": _get("rst_s") or "59",
            "r": _get("rst_r") or "59",
            "ss": _get("ss"),
            "sr": _get("sr"),
            "n": _get("note"),
            "d": _get("date"),
            "t": _get("time"),
        }

    def _focus_call_field(self):
        """Focus pe câmpul Indicativ din form."""
        try:
            w = self._ent.get("call")
            if w and hasattr(w, "focus_set"):
                w.focus_set()
        except Exception:
            pass

    def _cancel_edit(self):
        self._edit_idx = None
        for w in self._ent.values():
            if isinstance(w, tk.StringVar): w.set("")
            else: w.delete(0, "end")
        if self._save_btn:
            self._save_btn.config(text="💾 Salvează", bg=TH["ok"])
        if self._save_btn2:
            self._save_btn2.config(text="💾 Salvează", bg=TH["ok"])
        self.after(50, self._focus_call_field)

    def _save_entry(self):
        q = self._get_form()
        if not q["c"]:
            messagebox.showwarning("Log Editor", "Indicativul este obligatoriu!"); return
        if not q["b"] or not q["m"]:
            messagebox.showwarning("Log Editor", "Banda și modul sunt obligatorii!"); return

        if self._edit_idx is not None:
            # UPDATE
            self._undo_stack.append(("upd", self._edit_idx,
                                     copy.deepcopy(self._log[self._edit_idx])))
            self._log[self._edit_idx] = q
            self._set_status(f"✓ Actualizat QSO #{len(self._log)-self._edit_idx}: {q['c']}")
        else:
            # INSERT NOU (sus)
            self._undo_stack.append(("add", 0, q))
            self._log.insert(0, q)
            self._set_status(f"✓ Adăugat: {q['c']} {q['b']} {q['m']}")

        self._edit_idx = None
        if self._save_btn:
            self._save_btn.config(text="💾 Salvează", bg=TH["ok"])
        if self._save_btn2:
            self._save_btn2.config(text="💾 Salvează", bg=TH["ok"])

        self._save_to_disk()
        self._refresh()
        if self._on_change: self._on_change()

    def _delete_sel(self):
        sel = self._tree.selection()
        if not sel: return
        n = len(sel)
        if not messagebox.askyesno("Log Editor",
                                    f"Ștergeți {n} QSO selectat{'e' if n>1 else ''}?"): return
        for idx in sorted([int(x) for x in sel], reverse=True):
            if 0 <= idx < len(self._log):
                self._undo_stack.append(("del", idx,
                                         copy.deepcopy(self._log[idx])))
                self._log.pop(idx)
        self._save_to_disk()
        self._refresh()
        if self._on_change: self._on_change()
        self._set_status(f"✓ Șters {n} QSO.")

    def _undo(self):
        if not self._undo_stack:
            messagebox.showinfo("Undo", "Nimic de anulat."); return
        act, idx, q = self._undo_stack.pop()
        if act == "add" and 0 <= idx < len(self._log):
            self._log.pop(idx)
            self._set_status("↩ Undo: adăugare anulată")
        elif act == "del":
            self._log.insert(idx, q)
            self._set_status("↩ Undo: ștergere anulată")
        elif act == "upd":
            if 0 <= idx < len(self._log):
                self._log[idx] = q
            self._set_status("↩ Undo: modificare anulată")
        self._save_to_disk()
        self._refresh()
        if self._on_change: self._on_change()

    def _do_search(self):
        q = self._search_v.get().strip()
        if not q:
            self._search_v.set("")
        self._refresh()

    def _on_call_key(self, event=None):
        w = self._ent.get("call")
        if w is None: return
        c = w.get().upper()
        w.delete(0, "end"); w.insert(0, c)

    def _save_to_disk(self):
        try:
            cid = self._cid_getter() if self._cid_getter else "simplu"
            DM.save_log(cid, self._log)
            DM.backup(cid, self._log)
        except Exception as e:
            messagebox.showerror("Eroare salvare", str(e))

    def _cc(self):
        try:
            cid = self._cid_getter() if self._cid_getter else "simplu"
            return self._contests.get(cid, {})
        except Exception:
            return {}

    def _set_status(self, msg):
        try:
            self._status.config(text=msg)
        except Exception:
            pass

    # ── Callbook ───────────────────────────────────────────
    def _callbook_form(self):
        """Lookup din câmpul call din formular."""
        w = self._ent.get("call")
        call = w.get().strip().upper() if w and not isinstance(w, tk.StringVar) else ""
        if call:
            CallbookDialog(self, call, on_fill=self._fill_from_callbook)

    def _callbook_sel(self):
        """Lookup indicativ selectat din treeview."""
        call = self._sel_call()
        if not call:
            messagebox.showinfo("Callbook", "Selectați un QSO din log."); return
        CallbookDialog(self, call, on_fill=self._fill_from_callbook)

    def _fill_from_callbook(self, data):
        """Completează nota cu locatorul dacă e disponibil."""
        loc = data.get("loc","")
        if loc and self._ent.get("note"):
            self._ent["note"].delete(0,"end")
            self._ent["note"].insert(0, loc)
        self._set_status(
            f"Callbook: {data.get('call','')} — {data.get('name','')} — {data.get('qth','')}")

    @staticmethod
    def _open_qrz(call):
        if call:
            webbrowser.open(f"https://www.qrz.com/db/{call.upper()}")

    @staticmethod
    def _open_ro(call):
        if call:
            webbrowser.open(
                f"https://www.radioamator.ro/call-book/yocall.php?call={call.upper()}")


# ═══════════════════════════════════════════════════════════
# CALLBOOK DIALOG — Căutare radioamator.ro + QRZ.com
# ═══════════════════════════════════════════════════════════

class CallbookDialog(tk.Toplevel):
    """Dialog căutare callbook: radioamator.ro + QRZ.com
    
    Extrage date prin parsing HTML robust.
    Afișează pagina web randată (tkinterweb dacă disponibil, altfel iframe-like).
    """

    RADIOAMATOR_URL = "https://www.radioamator.ro/call-book/yocall.php?call={}"
    QRZ_URL         = "https://www.qrz.com/db/{}"

    # Headers browser-like pentru a evita blocarea
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, parent, call="", on_fill=None):
        super(CallbookDialog, self).__init__(parent)
        self._on_fill = on_fill
        self._result  = {}
        self._html_raw = ""
        self.title("🌐 Callbook Lookup — YO Log PRO v17.1")
        self.geometry("780x600")
        self.configure(bg=TH["bg"])
        self.transient(parent)
        self.resizable(True, True)
        self._build()
        center_dialog(self, parent)
        # Focus pe câmpul indicativ — după grab_set trebuie explicit
        self.after(100, lambda: self._e["call"].focus_set())
        self.after(120, lambda: self._e["call"].select_range(0, "end"))
        if call:
            self._call_e.delete(0, "end")
            self._call_e.insert(0, call.upper())
            self.after(150, self._search)

    # ── Build UI ──────────────────────────────────────────
    def _build(self):
        eo = {"bg": TH["entry_bg"], "fg": TH["gold"],
              "font": ("Consolas", 13, "bold"),
              "insertbackground": "white", "width": 12,
              "relief": "solid", "bd": 1, "justify": "center"}

        # ─ Search bar ─
        sf = tk.Frame(self, bg=TH["header_bg"], pady=8)
        sf.pack(fill="x")

        tk.Label(sf, text="Indicativ:", bg=TH["header_bg"],
                 fg=TH["fg"], font=("Consolas", 11)).pack(side="left", padx=(10,4))
        self._call_e = tk.Entry(sf, **eo)
        self._call_e.pack(side="left", padx=4)
        self._call_e.bind("<Return>", lambda e: self._search())

        self._src_v = tk.StringVar(value="radioamator.ro")
        for src in ("radioamator.ro", "QRZ.com"):
            tk.Radiobutton(sf, text=src, variable=self._src_v, value=src,
                           bg=TH["header_bg"], fg="white",
                           selectcolor=TH["entry_bg"],
                           activebackground=TH["header_bg"],
                           font=("Consolas", 10)).pack(side="left", padx=6)

        tk.Button(sf, text="🔍 Caută", command=self._search,
                  bg=TH["accent"], fg="white",
                  font=("Consolas", 11, "bold"), width=10).pack(side="left", padx=8)
        tk.Button(sf, text="🌐 Browser",
                  command=self._open_browser,
                  bg="#1a5276", fg="white",
                  font=("Consolas", 10), width=10).pack(side="left", padx=2)

        self._spin_lbl = tk.Label(sf, text="", bg=TH["header_bg"],
                                   fg=TH["warn"], font=("Consolas", 10, "bold"))
        self._spin_lbl.pack(side="right", padx=10)

        # ─ Info panel (câmpuri extrase) ─
        ip = tk.Frame(self, bg=TH["bg"], pady=4)
        ip.pack(fill="x", padx=10)

        self._info_labels = {}
        info_fields = [
            ("call",    "Indicativ"), ("name",    "Nume"),
            ("qth",     "QTH"),       ("loc",     "Locator"),
            ("dxcc",    "DXCC"),      ("class",   "Clasă"),
            ("itu",     "ITU"),       ("cq",      "CQ Zonă"),
            ("expires", "Expiră"),    ("email",   "Email"),
        ]
        for i, (key, lbl) in enumerate(info_fields):
            r, col = divmod(i, 5)
            frm = tk.Frame(ip, bg=TH["bg"])
            frm.grid(row=r, column=col, sticky="w", padx=8, pady=1)
            tk.Label(frm, text=f"{lbl}:",
                     bg=TH["bg"], fg="#888888",
                     font=("Consolas", 8), width=9, anchor="e").pack(side="left")
            val = tk.Label(frm, text="—", bg=TH["bg"],
                           fg=TH["gold"], font=("Consolas", 9, "bold"),
                           anchor="w", width=18)
            val.pack(side="left")
            self._info_labels[key] = val

        # ─ Tab: Pagina Web | Text brut ─
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=4)

        # Tab 1: Pagina web (tkinterweb sau ScrolledText cu HTML2Text)
        tab_web = tk.Frame(nb, bg=TH["bg"])
        nb.add(tab_web, text="  🌐 Pagina web  ")

        self._webview = None
        try:
            import tkinterweb
            self._webview = tkinterweb.HtmlFrame(tab_web, messages_enabled=False)
            self._webview.pack(fill="both", expand=True)
            self._webview.load_html("<p style='color:gray;font-family:monospace'>Caută un indicativ...</p>")
        except ImportError:
            try:
                from tkhtmlview import HTMLScrolledText
                self._webview = HTMLScrolledText(tab_web, height=12,
                    html="<p style='color:gray'>Caută un indicativ...</p>")
                self._webview.pack(fill="both", expand=True)
                self._webview_type = "tkhtmlview"
            except ImportError:
                self._webview = scrolledtext.ScrolledText(
                    tab_web, bg=TH["entry_bg"], fg="#cccccc",
                    font=("Consolas", 9), wrap="word")
                self._webview.pack(fill="both", expand=True)
                self._webview.insert("end", "Instalează tkinterweb pentru previzualizare web:\n"
                                     "  pip install tkinterweb\n\n"
                                     "sau tkhtmlview:\n  pip install tkhtmlview\n\n"
                                     "Caută un indicativ pentru a vedea datele text.")
                self._webview.config(state="disabled")
                self._webview_type = "text"
        else:
            self._webview_type = "tkinterweb"

        # Tab 2: Date parsate text
        tab_txt = tk.Frame(nb, bg=TH["bg"])
        nb.add(tab_txt, text="  📋 Date extrase  ")
        self._data_box = scrolledtext.ScrolledText(
            tab_txt, bg=TH["entry_bg"], fg=TH["ok"],
            font=("Consolas", 10), wrap="word", state="disabled")
        self._data_box.pack(fill="both", expand=True)
        self._data_box.bind("<MouseWheel>",
            lambda e: self._data_box.yview_scroll(int(-1*(e.delta/120)),"units"))

        # ─ Buttons ─
        bf = tk.Frame(self, bg=TH["bg"], pady=6)
        bf.pack(fill="x")
        tk.Button(bf, text="✅ Folosește locatorul",
                  command=self._use_loc,
                  bg=TH["ok"], fg="white",
                  font=("Consolas", 10), width=20).pack(side="left", padx=8)
        tk.Button(bf, text="📋 Copiază indicativ",
                  command=self._copy_call,
                  bg=TH["accent"], fg="white",
                  font=("Consolas", 10), width=18).pack(side="left", padx=4)
        tk.Button(bf, text="✖ Închide",
                  command=self.destroy,
                  bg=TH["btn_bg"], fg="white",
                  font=("Consolas", 10), width=10).pack(side="right", padx=8)

    # ── Search ────────────────────────────────────────────
    def _search(self):
        call = self._call_e.get().strip().upper()
        if not call:
            messagebox.showwarning("Callbook", "Introdu un indicativ!"); return
        src = self._src_v.get()
        self._set_loading(True)
        self._clear_fields()
        threading.Thread(target=self._fetch_thread,
                         args=(call, src), daemon=True).start()

    def _fetch_thread(self, call, src):
        try:
            if src == "radioamator.ro":
                data, html = self._fetch_radioamator(call)
            else:
                data, html = self._fetch_qrz(call)
            self.after(0, lambda: self._show_result(data, html, src))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    # ── Fetch radioamator.ro ──────────────────────────────
    # ── Fetch radioamator.ro ──────────────────────────────
    def _fetch_radioamator(self, call):
        """Fetch + parse www.radioamator.ro/call-book/yocall.php
        Parsează tabelul HTML rând cu rând: <td>Label</td><td>Valoare</td>
        """
        import html as hmod, gzip as gz
        url = self.RADIOAMATOR_URL.format(call.upper())
        try:
            req = Request(url, headers=self.HEADERS)
            resp = urlopen(req, timeout=12)
            raw = resp.read()
        except Exception as e:
            return {"call": call, "_error": str(e)}, ""
        try:
            html = gz.decompress(raw).decode("utf-8", errors="ignore")
        except Exception:
            try:   html = raw.decode("utf-8", errors="ignore")
            except Exception: html = raw.decode("latin-1", errors="ignore")

        h = hmod.unescape(html)
        data = {"call": call}

        def strip_tags(s):
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

        LABEL_MAP = {
            "indicativ":"call","callsign":"call","proprietar":"name","titular":"name",
            "denumire":"name","localitate":"qth","oras":"qth","adresa":"qth","qth":"qth",
            "judet":"county","locator":"loc","grid":"loc","clasa":"class","categorie":"class",
            "zona itu":"itu","itu":"itu","zona cq":"cq","cq":"cq",
            "expir":"expires","valabil":"expires","email":"email","dxcc":"dxcc",
        }

        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.IGNORECASE|re.DOTALL)
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.IGNORECASE|re.DOTALL)
            if len(cells) >= 2:
                lbl = strip_tags(cells[0]).lower().strip(" :.")
                val = strip_tags(cells[1]).strip()
                if not lbl or not val or val in ("-","—","N/A",""): continue
                for kw, fld in LABEL_MAP.items():
                    if kw in lbl and fld not in data:
                        data[fld] = val; break

        # Locator fallback
        if "loc" not in data:
            for m in re.finditer(r"\b([A-R]{2}\d{2}[A-X]{2})\b", h, re.IGNORECASE):
                cand = m.group(1).upper()
                if re.match(r"^[A-R]{2}\d{2}[A-X]{2}$", cand, re.IGNORECASE):
                    data["loc"] = cand; break

        # Email fallback
        if "email" not in data:
            m = re.search(r'mailto:([^\s"\'><]{5,60})', h)
            if m: data["email"] = m.group(1)

        if "dxcc" not in data:
            country, _ = DXCC.lookup(call)
            if country != "Unknown": data["dxcc"] = country

        if re.search(r"(nu a fost gasit|nu a fost găsit|not found|nu exista|nu există|"
                     r"indicativ invalid|no result|nu avem date|nu s-a gasit)",
                     h, re.IGNORECASE):
            if len(data) <= 2: data["_not_found"] = True

        return data, html

    # ── Fetch QRZ.com ─────────────────────────────────────
    def _fetch_qrz(self, call):
        """Fetch QRZ.com public page și extrage date."""
        import html as hmod, gzip as gz
        url = self.QRZ_URL.format(call.upper())
        try:
            req = Request(url, headers=self.HEADERS)
            resp = urlopen(req, timeout=12)
            raw = resp.read()
        except Exception as e:
            return {"call": call, "_error": str(e)}, ""
        try:
            html = gz.decompress(raw).decode("utf-8", errors="ignore")
        except Exception:
            try:   html = raw.decode("utf-8", errors="ignore")
            except Exception: html = raw.decode("latin-1", errors="ignore")

        h = hmod.unescape(html)
        data = {"call": call}

        def strip_tags(s):
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

        def fv(pats):
            for pat in pats:
                m = re.search(pat, h, re.IGNORECASE|re.DOTALL)
                if m:
                    v = strip_tags(m.group(1))
                    if v and len(v) > 1 and v not in ("-","—"): return v
            return ""

        v = fv([r'"name"\s+value="([^"]{2,60})"',
                r'"fname"\s+value="([^"]{2,40})"',
                r'<span[^>]*itemprop="name"[^>]*>([^<]{2,60})'])
        if v: data["name"] = v

        v = fv([r'"addr2"\s+value="([^"]{2,80})"',
                r'<span[^>]*id="addr2"[^>]*>([^<]{2,80})'])
        if v: data["qth"] = v

        v = fv([r'"grid"\s+value="([A-R]{2}\d{2}[A-Xa-x]{2})"'])
        if v: data["loc"] = v

        v = fv([r'"cqzone"\s+value="(\d+)"'])
        if v: data["cq"] = v

        v = fv([r'"ituzone"\s+value="(\d+)"'])
        if v: data["itu"] = v

        v = fv([r'"class"\s+value="([^"]{1,10})"'])
        if v: data["class"] = v

        v = fv([r'"dxcc"\s+value="([^"]{2,30})"',
                r'<span[^>]*itemprop="addressCountry"[^>]*>([^<]{2,30})'])
        if v: data["dxcc"] = v

        if "loc" not in data:
            for m in re.finditer(r"\b([A-R]{2}\d{2}[A-X]{2})\b", h):
                if re.match(r"^[A-R]{2}\d{2}[A-X]{2}$", m.group(1).upper()):
                    data["loc"] = m.group(1).upper(); break

        if "dxcc" not in data:
            country, _ = DXCC.lookup(call)
            if country != "Unknown": data["dxcc"] = country

        if re.search(r"(not found|no record|callsign not found|This callsign is not in)",
                     h, re.IGNORECASE):
            data["_not_found"] = True

        return data, html

    # ── Display ───────────────────────────────────────────
    def _show_result(self, data, html, src=""):
        self._set_loading(False)
        self._result = data
        self._html_raw = html

        if data.get("_error"):
            self._show_error(data["_error"]); return

        if data.get("_not_found"):
            for lbl in self._info_labels.values(): lbl.config(text="—")
            self._set_data_box(f"⚠ Indicativul {data.get('call','')} nu a fost găsit.")
            self._load_webview(html, src)
            return

        # Populează câmpuri
        for key in ("call","name","qth","loc","dxcc","class","itu","cq","expires","email"):
            val = data.get(key, "")
            if self._info_labels.get(key):
                self._info_labels[key].config(text=val or "—")

        # Tab "Date extrase"
        lines = []
        field_names = {"call":"Indicativ","name":"Nume","qth":"QTH","loc":"Locator",
                       "dxcc":"DXCC","class":"Clasă","itu":"ITU Zonă","cq":"CQ Zonă",
                       "expires":"Expiră","email":"Email"}
        for key, label in field_names.items():
            val = data.get(key, "—")
            lines.append(f"  {label:<14}: {val}")
        self._set_data_box("\n".join(lines))

        # Încarcă pagina web
        self._load_webview(html, src)

    def _show_error(self, msg):
        self._set_loading(False)
        self._set_data_box(f"⚠ Eroare: {msg}\n\nVerificați conexiunea la internet.")
        self._load_webview("", "")

    def _load_webview(self, html, src):
        """Afișează pagina în tab-ul web."""
        if not html:
            html = "<p style='color:gray;font-family:monospace'>Nu există date de afișat.</p>"
        try:
            if self._webview_type == "tkinterweb":
                self._webview.load_html(html)
            elif self._webview_type == "tkhtmlview":
                self._webview.set_html(html)
            else:
                # Text fallback: strip HTML tags
                import html as hm
                txt = hm.unescape(re.sub(r'<[^>]+>', ' ', html))
                txt = re.sub(r'\s+', ' ', txt).strip()
                self._webview.config(state="normal")
                self._webview.delete("1.0","end")
                self._webview.insert("end", txt[:6000])
                self._webview.config(state="disabled")
        except Exception:
            pass

    def _reload_webview(self):
        if self._html_raw:
            src = self._src_v.get()
            self._load_webview(self._html_raw, src)

    def _set_data_box(self, text):
        try:
            self._data_box.config(state="normal")
            self._data_box.delete("1.0","end")
            self._data_box.insert("end", text)
            self._data_box.config(state="disabled")
        except Exception: pass

    def _set_loading(self, state):
        try: self._spin_lbl.config(text="⏳ Se caută..." if state else "")
        except Exception: pass

    def _clear_fields(self):
        for lbl in self._info_labels.values(): lbl.config(text="—")
        self._set_data_box("")

    def _use_loc(self):
        loc = self._result.get("loc","")
        if not loc:
            messagebox.showinfo("Callbook","Nu s-a găsit locator."); return
        if self._on_fill:
            self._on_fill(self._result)
            messagebox.showinfo("Callbook", f"✓ Locatorul {loc} copiat în câmpul Notă.")
        else:
            try: self.clipboard_clear(); self.clipboard_append(loc)
            except Exception: pass
            messagebox.showinfo("Callbook", f"✓ Locatorul {loc} copiat în clipboard.")

    def _copy_call(self):
        call = self._result.get("call","") or self._call_e.get().strip().upper()
        if call:
            try: self.clipboard_clear(); self.clipboard_append(call)
            except Exception: pass

    def _open_browser(self):
        call = self._call_e.get().strip().upper()
        if not call: return
        src = self._src_v.get()
        if src == "radioamator.ro":
            webbrowser.open(self.RADIOAMATOR_URL.format(call))
        else:
            webbrowser.open(self.QRZ_URL.format(call))

    @staticmethod
    def _open_qrz(call):
        if call: webbrowser.open(f"https://www.qrz.com/db/{call.upper()}")

    @staticmethod
    def _open_ro(call):
        if call:
            webbrowser.open(
                f"https://www.radioamator.ro/call-book/yocall.php?call={call.upper()}")



# ═══════════════════════════════════════════════════════════
# BAND MAP — Hartă vizuală benzi cu activitate
# ═══════════════════════════════════════════════════════════

class BandMapWindow(tk.Toplevel):
    """Fereastră Band Map — afișează activitate QSO per bandă + frecvențe."""

    BAND_COLORS = {
        "160m": "#ff4444", "80m": "#ff8800", "60m": "#ffcc00",
        "40m": "#88ff00", "30m": "#00ff88", "20m": "#00aaff",
        "17m": "#4488ff", "15m": "#8844ff", "12m": "#ff44aa",
        "10m": "#ff0066", "6m": "#00ffff", "2m": "#44ffaa",
        "70cm": "#aaffee", "23cm": "#ffffff"
    }

    def __init__(self, parent, log_getter, cfg_getter):
        super(BandMapWindow, self).__init__(parent)
        self.log_getter = log_getter
        self.cfg_getter = cfg_getter
        self.title("📡 Band Map — YO Log PRO v17.1")
        self.geometry("820x500")
        self.configure(bg=TH["bg"])
        self.resizable(True, True)
        self._build()
        self._refresh()
        self._schedule()

    def _build(self):
        self.configure(bg=TH["bg"])
        hdr = tk.Frame(self, bg=TH["header_bg"], pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📡 Band Map — Activitate în timp real",
                 bg=TH["header_bg"], fg=TH["gold"],
                 font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        tk.Button(hdr, text="↺ Refresh", command=self._refresh,
                  bg=TH["accent"], fg="white", font=("Consolas", 10)).pack(side="right", padx=6)

        self._canvas = tk.Canvas(self, bg=TH["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Stats bar
        self._stat_lbl = tk.Label(self, text="", bg=TH["bg"], fg=TH["fg"],
                                   font=("Consolas", 9))
        self._stat_lbl.pack(side="bottom", fill="x", padx=6, pady=2)

    def _refresh(self):
        self._canvas.delete("all")
        log = self.log_getter()
        cfg = self.cfg_getter()
        my_loc = cfg.get("loc", "")

        # Grupează QSO-urile pe bandă
        band_qsos = {}
        for q in log:
            b = q.get("b", "?")
            if b not in band_qsos:
                band_qsos[b] = []
            band_qsos[b].append(q)

        bands = BANDS_ALL
        cw = max(60, self._canvas.winfo_width() or 820)
        col_w = max(50, (cw - 20) // len(bands))
        row_h = 22
        max_rows = max((len(v) for v in band_qsos.values()), default=0)
        canvas_h = max(300, (max_rows + 3) * row_h + 60)
        self._canvas.configure(scrollregion=(0, 0, cw, canvas_h))

        for ci, band in enumerate(bands):
            x = 10 + ci * col_w
            color = self.BAND_COLORS.get(band, "#888888")
            count = len(band_qsos.get(band, []))

            # Header bandă
            self._canvas.create_rectangle(x, 5, x + col_w - 2, 30,
                                          fill=color, outline="", tags="band_hdr")
            self._canvas.create_text(x + col_w//2, 17, text=f"{band}",
                                     font=("Consolas", 9, "bold"), fill="#000000")

            # Counter QSO
            self._canvas.create_text(x + col_w//2, 42,
                                     text=f"{count} QSO",
                                     font=("Consolas", 8), fill=color)

            # Listează QSO-urile pe bandă
            qsos = band_qsos.get(band, [])
            for ri, q in enumerate(reversed(qsos[-20:])):  # max 20 per bandă
                y = 55 + ri * row_h
                call = q.get("c", "?")
                freq = q.get("f", "")
                country, _ = DXCC.lookup(call)

                # Colorează diferit dacă e DX (altă țară)
                my_country, _ = DXCC.lookup(cfg.get("call", "YO8ACR"))
                is_dx = country != my_country and country != "Unknown"
                row_color = TH.get("cyan", "#00aaff") if is_dx else TH["fg"]

                # Calculează distanța dacă avem locator
                note = q.get("n", "")
                dist_txt = ""
                if my_loc and Loc.valid(my_loc) and len(note) >= 4 and Loc.valid(note[:6] if len(note)>=6 else note[:4]):
                    d = Loc.dist(my_loc, note[:6] if len(note)>=6 else note[:4])
                    if d > 0: dist_txt = f" {int(d)}km"

                disp = f"{call[:9]}"
                if freq: disp += f" {freq}k"
                self._canvas.create_text(x + 3, y + 11, text=disp,
                                         font=("Consolas", 8), fill=row_color, anchor="w")

        # Stats
        total = len(log)
        dxcc_set = set(DXCC.prefix(q.get("c","")) for q in log)
        self._stat_lbl.config(
            text=f"Total QSO: {total}  |  DXCC: {len(dxcc_set)}  |  "
                 f"Benzi active: {len(band_qsos)}  |  Ultimul refresh: {datetime.datetime.utcnow().strftime('%H:%M:%S')} UTC"
        )

    def _schedule(self):
        try:
            if self.winfo_exists():
                self._refresh()
                self.after(30000, self._schedule)  # refresh la 30s
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# DX CLUSTER — Client telnet GUI integrat
# ═══════════════════════════════════════════════════════════

class DXClusterWindow(tk.Toplevel):
    """DX Cluster client GUI — conectare telnet, filtrare, click-to-log."""

    DEFAULT_CLUSTERS = [
        "dxc.yo8acr.ro:7300",
        "cluster.dl9gtb.de:7300",
        "dx.db0sue.de:7300",
        "www.dxsummit.fi:7300",
        "gb7mbc.spoo.org:7300",
    ]

    def __init__(self, parent, on_spot=None):
        super(DXClusterWindow, self).__init__(parent)
        self.on_spot = on_spot  # callback(call, freq) la click spot
        self.title("📡 DX Cluster — YO Log PRO v17.1")
        self.geometry("860x520")
        self.configure(bg=TH["bg"])
        self._sock = None
        self._thread = None
        self._stop_evt = threading.Event()
        self._spots = []
        self._queue = deque(maxlen=200)
        self._connected = False
        self._build()
        self._tick()

    def _build(self):
        # Toolbar
        tb = tk.Frame(self, bg=TH["header_bg"], pady=4)
        tb.pack(fill="x")
        tk.Label(tb, text="Cluster:", bg=TH["header_bg"], fg=TH["fg"],
                 font=("Consolas", 10)).pack(side="left", padx=4)
        self._cluster_v = tk.StringVar(value=self.DEFAULT_CLUSTERS[0])
        cb = ttk.Combobox(tb, textvariable=self._cluster_v,
                          values=self.DEFAULT_CLUSTERS, width=28, font=("Consolas", 10))
        cb.pack(side="left", padx=4)
        tk.Label(tb, text="Call:", bg=TH["header_bg"], fg=TH["fg"],
                 font=("Consolas", 10)).pack(side="left")
        self._call_e = tk.Entry(tb, width=10, bg=TH["entry_bg"], fg=TH["gold"],
                                font=("Consolas", 10), insertbackground=TH["fg"])
        self._call_e.pack(side="left", padx=4)
        self._conn_btn = tk.Button(tb, text="▶ Conectare",
                                   command=self._connect,
                                   bg=TH["ok"], fg="white", font=("Consolas", 10), width=12)
        self._conn_btn.pack(side="left", padx=4)
        tk.Button(tb, text="■ Stop", command=self._disconnect,
                  bg=TH["err"], fg="white", font=("Consolas", 10), width=8).pack(side="left", padx=2)
        self._status_lbl = tk.Label(tb, text="● Deconectat", bg=TH["header_bg"],
                                    fg=TH["err"], font=("Consolas", 9))
        self._status_lbl.pack(side="right", padx=8)

        # Filter bar
        ff = tk.Frame(self, bg=TH["bg"], pady=2)
        ff.pack(fill="x", padx=6)
        tk.Label(ff, text="Filtru bandă:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="left")
        self._fband_v = tk.StringVar(value="Toate")
        fcb = ttk.Combobox(ff, textvariable=self._fband_v,
                           values=["Toate"] + BANDS_ALL, state="readonly", width=8)
        fcb.pack(side="left", padx=4)
        fcb.bind("<<ComboboxSelected>>", lambda e: self._refresh_spots())
        tk.Label(ff, text="Filtru call:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="left", padx=(8,0))
        self._fcall_v = tk.StringVar()
        fe = tk.Entry(ff, textvariable=self._fcall_v, width=10,
                      bg=TH["entry_bg"], fg=TH["fg"],
                      font=("Consolas", 9), insertbackground=TH["fg"])
        fe.pack(side="left", padx=4)
        fe.bind("<KeyRelease>", lambda e: self._refresh_spots())
        tk.Label(ff, text="Spoturi:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack(side="right")
        self._spot_count_lbl = tk.Label(ff, text="0", bg=TH["bg"],
                                         fg=TH["gold"], font=("Consolas", 9, "bold"))
        self._spot_count_lbl.pack(side="right")

        # Spoturi treeview
        tf = tk.Frame(self, bg=TH["bg"])
        tf.pack(fill="both", expand=True, padx=6, pady=3)
        cols = ("time", "dx", "freq", "band", "mode", "country", "comment", "spotter")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        hdrs = [("time","UTC",55),("dx","DX Call",95),("freq","Freq kHz",80),
                ("band","Bandă",55),("mode","Mod",50),("country","Țara",90),
                ("comment","Comment",160),("spotter","Spotter",90)]
        for col, hdr, w in hdrs:
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._tree.bind("<Double-1>", self._on_spot_dbl)
        self._tree.bind("<Return>", self._on_spot_dbl)
        self._tree.bind("<MouseWheel>",
            lambda e: self._tree.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._tree.bind("<Button-4>", lambda e: self._tree.yview_scroll(-1,"units"))
        self._tree.bind("<Button-5>", lambda e: self._tree.yview_scroll(1,"units"))

        # Raw log box
        rf = tk.Frame(self, bg=TH["bg"])
        rf.pack(fill="x", padx=6)
        tk.Label(rf, text="Raw cluster:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 8)).pack(anchor="w")
        self._raw_box = scrolledtext.ScrolledText(rf, height=5, bg=TH["entry_bg"],
                                                   fg=TH["ok"], font=("Consolas", 8),
                                                   state="disabled", insertbackground=TH["fg"])
        self._raw_box.pack(fill="x")

        # Cmd entry
        cf2 = tk.Frame(self, bg=TH["bg"])
        cf2.pack(fill="x", padx=6, pady=3)
        self._cmd_e = tk.Entry(cf2, bg=TH["entry_bg"], fg=TH["gold"],
                                font=("Consolas", 10), insertbackground=TH["fg"])
        self._cmd_e.pack(side="left", fill="x", expand=True)
        self._cmd_e.bind("<Return>", self._send_cmd)
        tk.Button(cf2, text="Trimite", command=self._send_cmd,
                  bg=TH["accent"], fg="white", font=("Consolas", 10)).pack(side="left", padx=4)

    def _connect(self):
        addr = self._cluster_v.get().strip()
        call = self._call_e.get().strip().upper()
        if not addr:
            messagebox.showerror("DX Cluster", "Selectați un cluster!"); return
        if not call:
            messagebox.showerror("DX Cluster", "Introduceți indicativul!"); return
        host, _, port_s = addr.partition(":")
        try: port = int(port_s) if port_s else 7300
        except: port = 7300
        self._disconnect()
        self._stop_evt.clear()
        self._thread = threading.Thread(
            target=self._run, args=(host, port, call), daemon=True)
        self._thread.start()

    def _disconnect(self):
        self._stop_evt.set()
        self._connected = False
        try:
            if self._sock: self._sock.close()
        except Exception: pass
        self._sock = None

    def _run(self, host, port, call):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((host, port))
            self._connected = True
            self._queue.append(("status", "● Conectat la " + host))
            # Login
            buf = b""
            t0 = time.time()
            while time.time() - t0 < 8:
                chunk = self._sock.recv(256)
                if not chunk: break
                buf += chunk
                if b"call" in buf.lower() or b"login" in buf.lower() or b">" in buf:
                    break
            self._sock.sendall((call + "\r\n").encode("ascii", errors="ignore"))
            time.sleep(0.5)
            # Receive loop
            self._sock.settimeout(5)
            line_buf = ""
            while not self._stop_evt.is_set():
                try:
                    data = self._sock.recv(512)
                    if not data:
                        break
                    line_buf += data.decode("ascii", errors="ignore")
                    while "\n" in line_buf:
                        line, line_buf = line_buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            self._queue.append(("raw", line))
                            spot = self._parse_spot(line)
                            if spot:
                                self._queue.append(("spot", spot))
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception as e:
            self._queue.append(("status", "● Eroare: " + str(e)))
        self._connected = False
        self._queue.append(("status", "● Deconectat"))

    def _parse_spot(self, line):
        """Parsează linii DX Cluster în multiple formate standard.

        Format principal (AR-Cluster/CC Cluster):
          DX de YO8ACR-6:  14200.0  KP4RV          <comment>
        Format alternativ (DX Spider):
          DX de YO8ACR:14200.0 KP4RV comment
        Format vechi:
          DXC  14200.0  KP4RV  <comment>
        """
        line = line.strip()
        spotter = ""; freq_s = ""; dx_call = ""; comment = ""

        # Format principal: DX de SPOTTER-N:  FREQ  DX_CALL  COMMENT
        m = re.match(
            r'DX\s+de\s+(\S+?)\s*:\s*(\d[\d.]+)\s+(\S+)\s*(.*)',
            line, re.IGNORECASE)
        if m:
            spotter  = m.group(1)
            freq_s   = m.group(2)
            dx_call  = m.group(3)
            comment  = m.group(4).strip()
        else:
            # Format vechi/alternativ
            m2 = re.match(r'DX\s+(\d[\d.]+)\s+(\w+)\s*(.*)', line, re.IGNORECASE)
            if m2:
                freq_s   = m2.group(1)
                dx_call  = m2.group(2)
                comment  = m2.group(3).strip()
            else:
                return None
        try:
            freq_khz = float(re.sub(r'[^0-9.]', '', freq_s))
        except Exception:
            return None
        band = freq2band(freq_khz) or "?"
        country, _ = DXCC.lookup(dx_call)
        # Detectare mod din comentariu
        mode = "SSB"
        for mo in ["CW", "FT8", "FT4", "RTTY", "PSK31", "SSB", "AM", "FM", "DIGI"]:
            if mo in comment.upper():
                mode = mo; break
        return {
            "time": datetime.datetime.utcnow().strftime("%H:%M"),
            "dx": dx_call.upper(),
            "freq": str(freq_khz),
            "band": band,
            "mode": mode,
            "country": country,
            "comment": comment.strip()[:40],
            "spotter": spotter.upper()
        }

    def _tick(self):
        try:
            if not self.winfo_exists(): return
        except Exception:
            return
        # Procesează coada
        processed = 0
        while self._queue and processed < 20:
            item = self._queue.popleft()
            kind = item[0]; data = item[1]
            if kind == "status":
                try:
                    self._status_lbl.config(
                        text=data,
                        fg=TH["ok"] if "Conectat" in data and "De" not in data else TH["err"])
                except Exception: pass
            elif kind == "raw":
                try:
                    self._raw_box.config(state="normal")
                    self._raw_box.insert("end", data + "\n")
                    self._raw_box.see("end")
                    self._raw_box.config(state="disabled")
                except Exception: pass
            elif kind == "spot":
                self._spots.insert(0, data)
                if len(self._spots) > 500: self._spots = self._spots[:500]
                self._refresh_spots()
            processed += 1
        self.after(500, self._tick)

    def _refresh_spots(self):
        fb = self._fband_v.get()
        fc = self._fcall_v.get().upper().strip()
        for row in self._tree.get_children():
            self._tree.delete(row)
        shown = 0
        for spot in self._spots:
            if fb != "Toate" and spot["band"] != fb: continue
            if fc and fc not in spot["dx"] and fc not in spot["spotter"]: continue
            tags = ()
            if spot["country"] not in ("Unknown",):
                tags = ("dx",)
            self._tree.insert("", "end", values=(
                spot["time"], spot["dx"], spot["freq"], spot["band"],
                spot["mode"], spot["country"], spot["comment"], spot["spotter"]
            ), tags=tags)
            shown += 1
            if shown >= 200: break
        self._tree.tag_configure("dx", foreground=TH.get("cyan", "#00aaff"))
        self._spot_count_lbl.config(text=str(shown))

    def _on_spot_dbl(self, event=None):
        sel = self._tree.selection()
        if not sel: return
        vals = self._tree.item(sel[0], "values")
        if vals and self.on_spot:
            dx_call = vals[1]
            freq = vals[2]
            self.on_spot(dx_call, freq)

    def _send_cmd(self, event=None):
        cmd = self._cmd_e.get().strip()
        if not cmd or not self._sock: return
        try:
            self._sock.sendall((cmd + "\r\n").encode("ascii", errors="ignore"))
            self._cmd_e.delete(0, "end")
        except Exception as e:
            messagebox.showerror("DX Cluster", str(e))


# ═══════════════════════════════════════════════════════════
# QSO RATE STATISTICS — Statistici și grafic QSO/h
# ═══════════════════════════════════════════════════════════

class RateStatsWindow(tk.Toplevel):
    """Statistici live QSO Rate — grafic QSO/h pe ore, top DXCC, top bandă."""

    def __init__(self, parent, log_getter, cfg_getter):
        super(RateStatsWindow, self).__init__(parent)
        self.log_getter = log_getter
        self.cfg_getter = cfg_getter
        self.title("📈 Statistici Rate QSO — YO Log PRO v17.1")
        self.geometry("860x560")
        self.configure(bg=TH["bg"])
        self._build()
        self._refresh()
        self._schedule()

    def _build(self):
        hdr = tk.Frame(self, bg=TH["header_bg"], pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📈 Statistici Rate QSO — Live",
                 bg=TH["header_bg"], fg=TH["gold"],
                 font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        tk.Button(hdr, text="↺ Refresh", command=self._refresh,
                  bg=TH["accent"], fg="white", font=("Consolas", 10)).pack(side="right", padx=6)

        # Main frame
        mf = tk.Frame(self, bg=TH["bg"])
        mf.pack(fill="both", expand=True, padx=6, pady=4)

        # Left: canvas grafic
        lf = tk.Frame(mf, bg=TH["bg"])
        lf.pack(side="left", fill="both", expand=True)
        tk.Label(lf, text="QSO / oră", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 10, "bold")).pack(anchor="w")
        self._rate_canvas = tk.Canvas(lf, bg=TH["bg"], highlightthickness=1,
                                       highlightbackground=TH["accent"], width=480, height=260)
        self._rate_canvas.pack(fill="both", expand=True, pady=4)

        # Right: tabele
        rf = tk.Frame(mf, bg=TH["bg"], width=320)
        rf.pack(side="right", fill="y", padx=(6,0))
        rf.pack_propagate(False)

        tk.Label(rf, text="Top DXCC", bg=TH["bg"], fg=TH["gold"],
                 font=("Consolas", 10, "bold")).pack(anchor="w", pady=(0,2))
        self._dxcc_tree = ttk.Treeview(rf, columns=("dxcc","count"), show="headings", height=8)
        self._dxcc_tree.heading("dxcc", text="DXCC/Țară")
        self._dxcc_tree.heading("count", text="QSO")
        self._dxcc_tree.column("dxcc", width=200)
        self._dxcc_tree.column("count", width=60, anchor="center")
        self._dxcc_tree.pack(fill="x")

        tk.Label(rf, text="Per Bandă", bg=TH["bg"], fg=TH["gold"],
                 font=("Consolas", 10, "bold")).pack(anchor="w", pady=(8,2))
        self._band_tree = ttk.Treeview(rf, columns=("band","count","pct"), show="headings", height=8)
        self._band_tree.heading("band", text="Bandă")
        self._band_tree.heading("count", text="QSO")
        self._band_tree.heading("pct", text="%")
        self._band_tree.column("band", width=70, anchor="center")
        self._band_tree.column("count", width=60, anchor="center")
        self._band_tree.column("pct", width=50, anchor="center")
        self._band_tree.pack(fill="x")

        # Bottom stats
        self._stats_frame = tk.Frame(self, bg=TH["bg"])
        self._stats_frame.pack(fill="x", padx=6, pady=4)
        self._stat_labels = {}
        stats_keys = [
            ("total", "Total QSO"), ("unique_calls", "Indicative unice"),
            ("dxcc_count", "DXCC lucrate"), ("rate_1h", "Rate 1h"),
            ("rate_last_qso", "Ultimul QSO"), ("top_band", "Banda activă"),
        ]
        for i, (k, lbl) in enumerate(stats_keys):
            r, c = divmod(i, 3)
            frm = tk.Frame(self._stats_frame, bg=TH["bg"], bd=1, relief="solid",
                           padx=8, pady=4)
            frm.grid(row=r, column=c, padx=4, pady=2, sticky="ew")
            self._stats_frame.columnconfigure(c, weight=1)
            tk.Label(frm, text=lbl, bg=TH["bg"], fg=TH["fg"],
                     font=("Consolas", 8)).pack(anchor="w")
            val_lbl = tk.Label(frm, text="—", bg=TH["bg"], fg=TH["gold"],
                                font=("Consolas", 11, "bold"))
            val_lbl.pack(anchor="w")
            self._stat_labels[k] = val_lbl

    def _refresh(self):
        log = self.log_getter()
        if not log:
            return

        # Calculează QSO/oră
        hour_counts = Counter()
        for q in log:
            try:
                dt_str = q.get("d", "") + " " + q.get("t", "00:00")
                dt = datetime.datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
                hour_counts[dt.strftime("%Y-%m-%d %H")] += 1
            except Exception:
                pass

        # Desenează graficul
        self._draw_rate_chart(hour_counts)

        # DXCC
        dxcc_counts = Counter(DXCC.lookup(q.get("c",""))[0] for q in log)
        for row in self._dxcc_tree.get_children(): self._dxcc_tree.delete(row)
        for country, cnt in dxcc_counts.most_common(20):
            self._dxcc_tree.insert("", "end", values=(country, cnt))

        # Per bandă
        band_counts = Counter(q.get("b", "?") for q in log)
        total = max(1, len(log))
        for row in self._band_tree.get_children(): self._band_tree.delete(row)
        for band in BANDS_ALL:
            cnt = band_counts.get(band, 0)
            if cnt:
                pct = f"{100*cnt//total}%"
                self._band_tree.insert("", "end", values=(band, cnt, pct))

        # Stats
        unique_calls = len(set(q.get("c","") for q in log))
        dxcc_count = len(set(DXCC.prefix(q.get("c","")) for q in log))
        top_band = band_counts.most_common(1)[0][0] if band_counts else "—"

        # Rate ultima oră
        now = datetime.datetime.utcnow()
        rate_1h = sum(1 for q in log if self._qso_in_window(q, now, 60))
        rate_last_qso = "—"
        if len(log) >= 2:
            try:
                def parse_dt(q):
                    return datetime.datetime.strptime(
                        (q.get("d","") + " " + q.get("t","00:00")).strip(), "%Y-%m-%d %H:%M")
                sorted_log = sorted(log, key=parse_dt)
                gap = parse_dt(sorted_log[-1]) - parse_dt(sorted_log[-2])
                rate_last_qso = f"{int(gap.total_seconds()//60)}m"
            except Exception:
                pass

        vals = {
            "total": str(len(log)),
            "unique_calls": str(unique_calls),
            "dxcc_count": str(dxcc_count),
            "rate_1h": f"{rate_1h} QSO/h",
            "rate_last_qso": rate_last_qso,
            "top_band": top_band,
        }
        for k, v in vals.items():
            if k in self._stat_labels:
                self._stat_labels[k].config(text=v)

    def _qso_in_window(self, q, now, minutes):
        try:
            dt = datetime.datetime.strptime(
                (q.get("d","") + " " + q.get("t","00:00")).strip(), "%Y-%m-%d %H:%M")
            return (now - dt).total_seconds() <= minutes * 60
        except Exception:
            return False

    def _draw_rate_chart(self, hour_counts):
        c = self._rate_canvas
        c.delete("all")
        cw = c.winfo_width() or 480
        ch = c.winfo_height() or 260
        pad_l, pad_r, pad_t, pad_b = 40, 10, 10, 30

        if not hour_counts:
            c.create_text(cw//2, ch//2, text="Nu există date", fill=TH["fg"],
                          font=("Consolas", 11)); return

        sorted_hours = sorted(hour_counts.keys())[-24:]  # ultimele 24h
        max_val = max(hour_counts[h] for h in sorted_hours) or 1
        n = len(sorted_hours)
        if n == 0: return
        bar_w = max(4, (cw - pad_l - pad_r) // n - 2)

        # Gridlines
        for i in range(5):
            y = pad_t + (ch - pad_t - pad_b) * i // 4
            val = max_val * (4 - i) // 4
            c.create_line(pad_l, y, cw - pad_r, y, fill=TH["accent"], dash=(2, 4))
            c.create_text(pad_l - 4, y, text=str(val), fill=TH["fg"],
                          font=("Consolas", 7), anchor="e")

        # Bars
        for i, hour in enumerate(sorted_hours):
            x = pad_l + i * (bar_w + 2)
            val = hour_counts[hour]
            bar_h = int((ch - pad_t - pad_b) * val / max_val)
            y0 = ch - pad_b - bar_h
            col = TH.get("cyan", "#00aaff") if val == max(hour_counts[h] for h in sorted_hours) else TH["accent"]
            c.create_rectangle(x, y0, x + bar_w, ch - pad_b, fill=col, outline="")
            c.create_text(x + bar_w//2, y0 - 8, text=str(val),
                          fill=TH["fg"], font=("Consolas", 7))
            # Label oră
            lbl = hour[-2:] + "h"
            c.create_text(x + bar_w//2, ch - pad_b + 12, text=lbl,
                          fill=TH["fg"], font=("Consolas", 7), angle=0)

    def _schedule(self):
        try:
            if self.winfo_exists():
                self._refresh()
                self.after(60000, self._schedule)  # refresh la 60s
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# LIVE SCORE PANEL — Scor contest în timp real
# ═══════════════════════════════════════════════════════════

class LiveScorePanel(tk.Toplevel):
    """Panou scor concurs live — QSO/h, multiplicatori, DXCC, bandă."""

    def __init__(self, parent, log_getter, cfg_getter, contest_getter):
        super(LiveScorePanel, self).__init__(parent)
        self.log_getter = log_getter
        self.cfg_getter = cfg_getter
        self.contest_getter = contest_getter
        self.title("📊 Scor Live — YO Log PRO v17.1")
        self.geometry("420x500")
        self.configure(bg=TH["bg"])
        self.resizable(False, True)
        self._build()
        self._refresh()
        self._schedule()

    def _build(self):
        tk.Label(self, text="📊 Scor Contest Live",
                 bg=TH["header_bg"], fg=TH["gold"],
                 font=("Consolas", 13, "bold"), pady=6).pack(fill="x")

        mf = tk.Frame(self, bg=TH["bg"], padx=12, pady=8)
        mf.pack(fill="both", expand=True)

        # Score principal
        self._score_lbl = tk.Label(mf, text="0", bg=TH["bg"], fg=TH["gold"],
                                    font=("Consolas", 36, "bold"))
        self._score_lbl.pack(pady=(10, 0))
        tk.Label(mf, text="SCOR TOTAL", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9)).pack()

        sep = tk.Frame(mf, bg=TH["accent"], height=1)
        sep.pack(fill="x", pady=8)

        # Grid de statistici
        stats_grid = tk.Frame(mf, bg=TH["bg"])
        stats_grid.pack(fill="x")

        self._stat_widgets = {}
        stat_items = [
            ("qso_total", "Total QSO", 0, 0),
            ("qso_pts", "Puncte QSO", 0, 1),
            ("mults", "Multiplicatori", 1, 0),
            ("dxcc", "DXCC", 1, 1),
            ("rate_1h", "QSO/h (1h)", 2, 0),
            ("rate_10", "QSO/h (10min)", 2, 1),
            ("unique", "Indicative unice", 3, 0),
            ("countries", "Țări lucrate", 3, 1),
        ]
        for key, label, row, col in stat_items:
            frm = tk.Frame(stats_grid, bg=TH["bg"], bd=1, relief="flat",
                           padx=10, pady=6)
            frm.grid(row=row, column=col, padx=4, pady=3, sticky="ew")
            stats_grid.columnconfigure(col, weight=1)
            tk.Label(frm, text=label, bg=TH["bg"], fg=TH["fg"],
                     font=("Consolas", 8)).pack(anchor="w")
            val_lbl = tk.Label(frm, text="0", bg=TH["bg"], fg=TH["cyan"],
                                font=("Consolas", 14, "bold"))
            val_lbl.pack(anchor="w")
            self._stat_widgets[key] = val_lbl

        sep2 = tk.Frame(mf, bg=TH["accent"], height=1)
        sep2.pack(fill="x", pady=8)

        # Per bandă progress bars
        tk.Label(mf, text="QSO per bandă:", bg=TH["bg"], fg=TH["fg"],
                 font=("Consolas", 9, "bold")).pack(anchor="w")
        self._band_frame = tk.Frame(mf, bg=TH["bg"])
        self._band_frame.pack(fill="x", pady=4)

        # Last update
        self._upd_lbl = tk.Label(self, text="", bg=TH["bg"], fg=TH["fg"],
                                  font=("Consolas", 8))
        self._upd_lbl.pack(side="bottom", anchor="e", padx=6, pady=2)

        tk.Button(self, text="↺ Refresh", command=self._refresh,
                  bg=TH["btn_bg"], fg="white", font=("Consolas", 9)).pack(
                      side="bottom", pady=4)

    def _refresh(self):
        log = self.log_getter()
        cfg = self.cfg_getter()
        cc = self.contest_getter()
        now = datetime.datetime.utcnow()

        # Score calcul
        qp, mc, tot = Score.total(log, cc, cfg)
        self._score_lbl.config(text=str(tot))

        # Stats
        unique_calls = len(set(q.get("c","") for q in log))
        countries = len(set(DXCC.lookup(q.get("c",""))[0] for q in log if q.get("c")))
        dxcc_count = len(set(DXCC.prefix(q.get("c","")) for q in log))

        def _in_window(q, mins):
            try:
                dt = datetime.datetime.strptime(
                    (q.get("d","") + " " + q.get("t","00:00")).strip(), "%Y-%m-%d %H:%M")
                return (now - dt).total_seconds() <= mins * 60
            except Exception:
                return False

        rate_1h = sum(1 for q in log if _in_window(q, 60))
        rate_10 = sum(1 for q in log if _in_window(q, 10)) * 6  # → /h

        vals = {
            "qso_total": str(len(log)),
            "qso_pts": str(qp),
            "mults": str(mc),
            "dxcc": str(dxcc_count),
            "rate_1h": str(rate_1h),
            "rate_10": str(rate_10),
            "unique": str(unique_calls),
            "countries": str(countries),
        }
        for k, v in vals.items():
            if k in self._stat_widgets:
                self._stat_widgets[k].config(text=v)

        # Band bars
        for w in self._band_frame.winfo_children(): w.destroy()
        band_counts = Counter(q.get("b","?") for q in log)
        total_q = max(1, len(log))
        active_bands = [(b, band_counts[b]) for b in BANDS_ALL if band_counts.get(b,0) > 0]
        active_bands.sort(key=lambda x: -x[1])
        for band, cnt in active_bands[:6]:
            bf = tk.Frame(self._band_frame, bg=TH["bg"])
            bf.pack(fill="x", pady=1)
            tk.Label(bf, text=f"{band:<5}", bg=TH["bg"], fg=TH["fg"],
                     font=("Consolas", 8), width=5).pack(side="left")
            pct = cnt * 100 // total_q
            bar_frame = tk.Frame(bf, bg=TH["entry_bg"], height=12, width=200)
            bar_frame.pack(side="left", padx=4)
            bar_frame.pack_propagate(False)
            bar_fill = tk.Frame(bar_frame, bg=TH["accent"], height=12,
                                 width=max(2, pct * 2))
            bar_fill.pack(side="left")
            tk.Label(bf, text=f"{cnt}", bg=TH["bg"], fg=TH["gold"],
                     font=("Consolas", 8)).pack(side="left")

        self._upd_lbl.config(text=f"Actualizat: {now.strftime('%H:%M:%S')} UTC")

    def _schedule(self):
        try:
            if self.winfo_exists():
                self._refresh()
                self.after(15000, self._schedule)  # refresh la 15s
        except Exception:
            pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg=DM.load("config.json",DEFAULT_CFG.copy())
        for k,v in DEFAULT_CFG.items():
            if k not in self.cfg: self.cfg[k]=v
        self.contests=DM.load("contests.json",DEFAULT_CONTESTS.copy())
        for k,v in DEFAULT_CONTESTS.items():
            if k not in self.contests: self.contests[k]=copy.deepcopy(v)
            else:
                for fk,fv in v.items():
                    if fk not in self.contests[k]: self.contests[k][fk]=fv
        if self.cfg.get("contest","") not in self.contests: self.cfg["contest"]="simplu"
        self.log=DM.load_log(self.cfg.get("contest","simplu"))
        if not isinstance(self.log,list): self.log=[]
        L.s(self.cfg.get("lang","ro")); self.edit_idx=None; self.ent={}; self.serial=len(self.log)+1; self.undo_stack=deque(maxlen=50)
        self._apply_theme_from_cfg()
        # CAT: reconnect if was enabled
        CAT.on_update = self._on_cat_update
        if self.cfg.get("cat_enabled") and self.cfg.get("cat_port"):
            CAT.connect(self.cfg)
        self.info_lbl=self.sc_lbl=self.clk=self.rate_lbl=self.cat_lbl=None; self.led_c=self.led=self.st_lbl=self.wb_lbl=self.log_btn=None
        self.tree=self.ctx=self.fb_v=self.fm_v=None; self.cv=self.ccb=self.lang_v=self.man_v=self.cat_v=self.cou_v=None
        self._setup_win(); self._setup_style(); self._build_menu(); self._build_ui(); self._build_ctx(); self._refresh()
        self.protocol("WM_DELETE_WINDOW",self._exit)
        self.bind('<Return>',lambda e:self._add_qso()); self.bind('<Control-s>',lambda e:self._fsave())
        self.bind('<Control-z>',lambda e:self._undo()); self.bind('<Control-f>',lambda e:self._search_dlg())
        self.bind('<F2>',self._cycle_band); self.bind('<F3>',self._cycle_mode)
        self._tick_clock(); self._tick_save()
        # Focus pe câmpul indicativ la pornire
        self.after(100, self._focus_call)
        # MouseWheel pe tree principal
        self.bind_all("<MouseWheel>",   self._on_mousewheel)
        self.bind_all("<Button-4>",     lambda e: self._on_mousewheel(e, +1))
        self.bind_all("<Button-5>",     lambda e: self._on_mousewheel(e, -1))
        # Prima utilizare — arata dialog configurare
        if self.cfg.get("first_run", True):
            self.after(200, self._first_run_setup)

    def _focus_call(self):
        """Focus pe câmpul indicativ la pornire."""
        try:
            if self.ent.get("call"):
                self.ent["call"].focus_set()
                self.ent["call"].icursor("end")
        except Exception:
            pass

    def _on_mousewheel(self, event, direction=None):
        """Scroll cu rotița mouse-ului pe widget-ul activ sau pe tree."""
        widget = event.widget
        # Detectăm direcția
        if direction is not None:
            delta = direction
        else:
            try:
                delta = -1 if event.delta > 0 else 1
            except Exception:
                delta = -1
        # Scroll pe Treeview principal
        try:
            if self.tree and widget in (self.tree, self):
                self.tree.yview_scroll(delta, "units")
                return
        except Exception:
            pass
        # Scroll pe orice Treeview/Text/Canvas care are focus
        try:
            if hasattr(widget, 'yview_scroll'):
                widget.yview_scroll(delta, "units")
        except Exception:
            pass

    def _first_run_setup(self):
        """Apare automat la primul start — cere indicativ si informatii."""
        d = FirstRunDialog(self, self.cfg)
        self.wait_window(d)
        if d.result:
            self.cfg.update(d.result)
            DM.save("config.json", self.cfg)
            L.s(self.cfg.get("lang","ro"))
            self._rebuild()
            messagebox.showinfo(
                "YO Log PRO v17.1",
                f"Bun venit, {self.cfg.get('call','')}!\n\nYO Log PRO v17.1 este gata de utilizare.\n73 de YO8ACR!"
            )

    def _cat_quick_connect(self):
        """Conectare rapida din meniu cu setarile salvate."""
        if not self.cfg.get("cat_port") and not self.cfg.get("cat_protocol","").startswith("Hamlib"):
            messagebox.showinfo("CAT", "Configureaza portul COM mai intai: Meniu CAT -> Setari CAT")
            self._cat_dlg(); return
        ok, msg = CAT.connect(self.cfg)
        if self.cat_lbl:
            self.cat_lbl.config(text=f"CAT: {'ON' if ok else 'ERR'}",
                                fg=TH["ok"] if ok else TH["err"])
        messagebox.showinfo("CAT", msg)

    def _cat_quick_disconnect(self):
        CAT.disconnect()
        if self.cat_lbl:
            self.cat_lbl.config(text="CAT: OFF", fg=TH["err"])

    def _apply_theme_quick(self, theme_name):
        """Aplica o tema direct din meniu fara dialog."""
        self.cfg["theme"] = theme_name
        self.cfg["custom_colors"] = {}
        DM.save("config.json", self.cfg)
        self._apply_theme_from_cfg()
        self._rebuild()

    def _apply_theme_from_cfg(self):
        global TH
        custom = self.cfg.get("custom_colors",{})
        base = dict(THEMES.get(self.cfg.get("theme","Dark Blue (implicit)"), THEMES["Dark Blue (implicit)"]))
        if custom: base.update({k:v for k,v in custom.items() if k in base})
        TH.update(base)

    def _on_cat_update(self, freq_khz, mode):
        """Callback din thread CAT — actualizează câmpurile freq și mode."""
        def _upd():
            try:
                if not self.winfo_exists(): return
                # Freq
                if freq_khz and self.ent.get("freq") is not None:
                    cur = self.ent["freq"].get().strip()
                    if cur != freq_khz:
                        self.ent["freq"].delete(0,"end")
                        self.ent["freq"].insert(0, freq_khz)
                        self._on_freq_out()   # auto-setează banda
                # Mode
                if mode and self.ent.get("mode") is not None:
                    cc = self._cc()
                    allowed = cc.get("allowed_modes", MODES_ALL)
                    # SSB fallback
                    m = mode if mode in allowed else ("SSB" if "SSB" in allowed else None)
                    if m and self.ent["mode"].get() != m:
                        self.ent["mode"].set(m)
                        self._on_mode_change()
                # Update CAT indicator
                if self.cat_lbl:
                    self.cat_lbl.config(
                        text=f"📡 {freq_khz} kHz  {mode}",
                        fg=TH["ok"])
            except: pass
        self.after(0, _upd)   # thread-safe: scheduleaza pe main thread

    def _cat_dlg(self):
        d = CATSettingsDialog(self, self.cfg, CAT)
        self.wait_window(d)
        if d.result:
            self.cfg.update(d.result)
            DM.save("config.json", self.cfg)
            CAT.on_update = self._on_cat_update

    def _new_log_dlg(self):
        DM.save_log(self._cid(), self.log)
        d = NewLogDialog(self, self.contests)
        self.wait_window(d)
        if not d.result: return
        self.cfg["contest"] = d.result["contest"]
        self.cfg["log_id"]  = d.result["log_id"]
        DM.save("config.json", self.cfg)
        self.log = DM.load_log(d.result["log_id"])
        if not isinstance(self.log, list): self.log = []
        self.serial = 1; self.undo_stack.clear(); self._rebuild()

    def _theme_dlg(self):
        d = ThemeDialog(self, self.cfg.get("theme","Dark Blue (implicit)"), self.cfg.get("custom_colors",{}))
        self.wait_window(d)
        if not d.result: return
        self.cfg["theme"] = d.result["theme"]
        self.cfg["custom_colors"] = d.result["colors"]
        DM.save("config.json", self.cfg)
        self._apply_theme_from_cfg(); self._rebuild()

    def _cc(self): return self.contests.get(self.cfg.get("contest","simplu"),self.contests.get("simplu",{}))
    def _cid(self): return self.cfg.get("log_id", self.cfg.get("contest","simplu"))
    def _sounds(self): return self.cfg.get("sounds",True) and HAS_SOUND

    def _setup_win(self):
        self.title(L.t("app_title")); self.configure(bg=TH["bg"])
        geo=self.cfg.get("win_geo","")
        try: self.geometry(geo if geo else "1280x780")
        except: self.geometry("1280x780")
        self.minsize(1100,680)

    def _setup_style(self):
        self.fs=int(self.cfg.get("fs",11)); self.fn=("Consolas",self.fs); self.fb=("Consolas",self.fs,"bold")
        s=ttk.Style()
        try: s.theme_use('clam')
        except: pass
        s.configure("Treeview",background=TH["entry_bg"],foreground=TH["fg"],fieldbackground=TH["entry_bg"],font=self.fn,rowheight=22)
        s.configure("Treeview.Heading",background=TH["header_bg"],foreground=TH["fg"],font=self.fb)
        s.map("Treeview",background=[("selected",TH["accent"])])

    def _build_menu(self):
        mb=tk.Menu(self); self.config(menu=mb)
        cm=tk.Menu(mb,tearoff=0); mb.add_cascade(label=L.t("contests"),menu=cm)
        cm.add_command(label=L.t("contest_mgr"),command=self._mgr); cm.add_separator()
        for cid,cd in self.contests.items():
            cm.add_command(label=f"⚡ {cd.get('name_'+L.g(),cd.get('name_ro',cid))}",command=lambda c=cid:self._switch_contest(c))
        lm=tk.Menu(mb,tearoff=0); mb.add_cascade(label="Log",menu=lm)
        lm.add_command(label="Log Nou / New Log",command=self._new_log_dlg)
        lm.add_separator()
        lm.add_command(label="Salveaza acum",command=lambda:DM.save_log(self._cid(),self.log))
        catn=tk.Menu(mb,tearoff=0); mb.add_cascade(label="CAT",menu=catn)
        catn.add_command(label="Setari CAT / CAT Settings",command=self._cat_dlg)
        catn.add_separator()
        catn.add_command(label="Conecteaza / Connect",command=lambda:self._cat_quick_connect())
        catn.add_command(label="Deconecteaza / Disconnect",command=lambda:self._cat_quick_disconnect())
        temn=tk.Menu(mb,tearoff=0); mb.add_cascade(label="Teme",menu=temn)
        temn.add_command(label="Editor teme / Themes",command=self._theme_dlg)
        temn.add_separator()
        for tnm in THEMES.keys():
            temn.add_command(label=tnm,command=lambda t=tnm:self._apply_theme_quick(t))
        tm=tk.Menu(mb,tearoff=0); mb.add_cascade(label=L.t("tools"),menu=tm)
        tm.add_command(label=L.t("search"),command=self._search_dlg); tm.add_command(label=L.t("timer"),command=self._timer_dlg); tm.add_separator()
        tm.add_command(label=L.t("imp_adif"),command=self._import_adif); tm.add_command(label=L.t("imp_csv"),command=self._import_csv)
        tm.add_command(label=L.t("imp_cab"),command=self._import_cabrillo); tm.add_separator()
        tm.add_command(label=L.t("print_log"),command=self._print_log); tm.add_command(label=L.t("verify"),command=self._verify_hash); tm.add_separator()
        tm.add_command(label=L.t("clear_log"),command=self._clear_log)
        # ─── Meniu v17.1: Instrumente noi ───
        v171m = tk.Menu(mb, tearoff=0); mb.add_cascade(label="📡 v17.1", menu=v171m)
        v171m.add_command(label="📡 Band Map", command=self._open_bandmap)
        v171m.add_command(label="📡 DX Cluster", command=self._open_cluster)
        v171m.add_command(label="📊 Scor Live", command=self._open_live_score)
        v171m.add_command(label="📈 Rate QSO Stats", command=self._open_rate_stats)
        v171m.add_separator()
        v171m.add_command(label="📂 Încarcă cty.dat", command=self._load_cty_dat)
        v171m.add_separator()
        v171m.add_command(label="📝 Editor Log dedicat",  command=self._open_log_editor)
        v171m.add_command(label="🌐 Callbook Lookup",     command=self._open_callbook)
        hm=tk.Menu(mb,tearoff=0); mb.add_cascade(label=L.t("help"),menu=hm)
        hm.add_command(label=L.t("about"),command=self._about); hm.add_command(label="Exit",command=self._exit)

    def _build_ctx(self):
        self.ctx=Menu(self,tearoff=0); self.ctx.add_command(label=L.t("edit_qso"),command=self._edit_sel); self.ctx.add_command(label=L.t("delete_qso"),command=self._del_sel)

    def _build_ui(self): self._build_hdr(); self._build_inp(); self._build_flt(); self._build_tree(); self._build_btns()

    def _build_hdr(self):
        h=tk.Frame(self,bg=TH["header_bg"],pady=5); h.pack(fill="x")
        lf=tk.Frame(h,bg=TH["header_bg"]); lf.pack(side="left",padx=10)
        self.led_c=tk.Canvas(lf,width=14,height=14,bg=TH["header_bg"],highlightthickness=0)
        self.led=self.led_c.create_oval(1,1,13,13,fill=TH["led_on"],outline=""); self.led_c.pack(side="left",padx=(0,5))
        self.st_lbl=tk.Label(lf,text=L.t("online"),bg=TH["header_bg"],fg=TH["led_on"],font=self.fn); self.st_lbl.pack(side="left")
        self.info_lbl=tk.Label(lf,text="",bg=TH["header_bg"],fg=TH["fg"],font=self.fn); self.info_lbl.pack(side="left",padx=12)
        rf=tk.Frame(h,bg=TH["header_bg"]); rf.pack(side="right",padx=10)
        self.clk=tk.Label(rf,text="UTC 00:00:00",bg=TH["header_bg"],fg=TH["gold"],font=("Consolas",12,"bold")); self.clk.pack(side="right",padx=8)
        self.rate_lbl=tk.Label(rf,text="",bg=TH["header_bg"],fg=TH["ok"],font=("Consolas",10)); self.rate_lbl.pack(side="right",padx=8)
        self.cat_lbl=tk.Label(rf,text="CAT: OFF",bg=TH["header_bg"],fg=TH["err"],
                               font=("Consolas",10,"bold"),cursor="hand2")
        self.cat_lbl.pack(side="right",padx=6)
        self.cat_lbl.bind("<Button-1>",lambda e:self._cat_dlg())
        if CAT.connected:
            freq_txt = f"{CAT.last_freq}kHz" if CAT.last_freq else ""
            mode_txt = CAT.last_mode or ""
            self.cat_lbl.config(text=f"CAT:{freq_txt} {mode_txt}".strip(),fg=TH["ok"])
        self.lang_v=tk.StringVar(value=self.cfg.get("lang","ro"))
        lc=ttk.Combobox(rf,textvariable=self.lang_v,values=["ro","en"],state="readonly",width=4); lc.pack(side="right",padx=3); lc.bind("<<ComboboxSelected>>",self._on_lang)
        self.cv=tk.StringVar(value=self._cid())
        self.ccb=ttk.Combobox(rf,textvariable=self.cv,values=list(self.contests.keys()),state="readonly",width=15); self.ccb.pack(side="right",padx=3); self.ccb.bind("<<ComboboxSelected>>",self._on_cchange)
        self._upd_info()

    def _build_inp(self):
        ip=tk.Frame(self,bg=TH["bg"],pady=8); ip.pack(fill="x",padx=10); r1=tk.Frame(ip,bg=TH["bg"]); r1.pack(fill="x"); cc=self._cc()
        cf=tk.Frame(r1,bg=TH["bg"]); cf.pack(side="left",padx=3)
        tk.Label(cf,text=L.t("call"),bg=TH["bg"],fg=TH["fg"],font=self.fb).pack()
        self.ent["call"]=tk.Entry(cf,width=15,bg=TH["entry_bg"],fg=TH["gold"],font=("Consolas",self.fs+2,"bold"),insertbackground=TH["fg"],justify="center")
        self.ent["call"].pack(ipady=3); self.ent["call"].bind("<KeyRelease>",self._on_call_key)
        self.wb_lbl=tk.Label(cf,text="",bg=TH["bg"],fg=TH["err"],font=("Consolas",9)); self.wb_lbl.pack()
        # Buton callbook inline sub câmpul call
        tk.Button(cf,text="🌐 Callbook",
                  command=self._open_callbook,
                  bg="#1a237e",fg="white",
                  font=("Consolas",8),width=10).pack(pady=(1,0))
        ff=tk.Frame(r1,bg=TH["bg"]); ff.pack(side="left",padx=3)
        tk.Label(ff,text=L.t("freq"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
        self.ent["freq"]=tk.Entry(ff,width=9,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,insertbackground=TH["fg"],justify="center"); self.ent["freq"].pack()
        self.ent["freq"].bind("<FocusOut>",self._on_freq_out)
        self.ent["freq"].bind("<Return>",lambda e:self._send_freq_to_radio())
        ab=cc.get("allowed_bands",BANDS_ALL)
        bf2=tk.Frame(r1,bg=TH["bg"]); bf2.pack(side="left",padx=3)
        tk.Label(bf2,text=L.t("band"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
        self.ent["band"]=ttk.Combobox(bf2,values=ab,state="readonly",width=6,font=self.fn); self.ent["band"].set(ab[0] if ab else "40m"); self.ent["band"].pack()
        self.ent["band"].bind("<<ComboboxSelected>>",self._on_band_change)
        am=cc.get("allowed_modes",MODES_ALL)
        mf2=tk.Frame(r1,bg=TH["bg"]); mf2.pack(side="left",padx=3)
        tk.Label(mf2,text=L.t("mode"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
        self.ent["mode"]=ttk.Combobox(mf2,values=am,state="readonly",width=6,font=self.fn); self.ent["mode"].set(am[0] if am else "SSB"); self.ent["mode"].pack()
        self.ent["mode"].bind("<<ComboboxSelected>>",self._on_mode_change)
        drst=RST_DEFAULTS.get(am[0] if am else "SSB","59")
        for k,lb in [("rst_s",L.t("rst_s")),("rst_r",L.t("rst_r"))]:
            frame=tk.Frame(r1,bg=TH["bg"]); frame.pack(side="left",padx=3)
            tk.Label(frame,text=lb,bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
            e=tk.Entry(frame,width=5,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,insertbackground=TH["fg"],justify="center"); e.insert(0,drst); e.pack(); self.ent[k]=e
        if cc.get("use_serial"):
            for k,lb in [("ss",L.t("serial_s")),("sr",L.t("serial_r"))]:
                frame=tk.Frame(r1,bg=TH["bg"]); frame.pack(side="left",padx=3)
                tk.Label(frame,text=lb,bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
                e=tk.Entry(frame,width=5,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,insertbackground=TH["fg"],justify="center")
                if k=="ss": e.insert(0,str(self.serial))
                e.pack(); self.ent[k]=e
        nf=tk.Frame(r1,bg=TH["bg"]); nf.pack(side="left",padx=3)
        tk.Label(nf,text=L.t("note"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack()
        self.ent["note"]=tk.Entry(nf,width=13,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,insertbackground=TH["fg"],justify="center"); self.ent["note"].pack()
        rbf=tk.Frame(r1,bg=TH["bg"]); rbf.pack(side="left",padx=6)
        self.man_v=tk.BooleanVar(value=self.cfg.get("manual_dt",False))
        tk.Checkbutton(rbf,text=L.t("manual"),variable=self.man_v,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"],command=self._tog_man).pack()
        self.log_btn=tk.Button(rbf,text=L.t("log"),command=self._add_qso,bg=TH["accent"],fg="white",font=self.fb,width=10); self.log_btn.pack(pady=1)
        tk.Button(rbf,text=L.t("reset"),command=self._full_clr,bg=TH["btn_bg"],fg=TH["btn_fg"],font=self.fn,width=10).pack(pady=1)
        r2=tk.Frame(ip,bg=TH["bg"]); r2.pack(fill="x",pady=(6,0))
        tk.Label(r2,text=L.t("date_l"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack(side="left",padx=3)
        self.ent["date"]=tk.Entry(r2,width=11,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,justify="center",state="disabled"); self.ent["date"].pack(side="left",padx=2)
        tk.Label(r2,text=L.t("time_l"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack(side="left",padx=3)
        self.ent["time"]=tk.Entry(r2,width=7,bg=TH["entry_bg"],fg=TH["fg"],font=self.fn,justify="center",state="disabled"); self.ent["time"].pack(side="left",padx=2)
        now=datetime.datetime.utcnow()
        for k,v in [("date",now.strftime("%Y-%m-%d")),("time",now.strftime("%H:%M"))]:
            self.ent[k].config(state="normal"); self.ent[k].insert(0,v)
            if not self.man_v.get(): self.ent[k].config(state="disabled")
        tk.Label(r2,text=L.t("category"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack(side="left",padx=(12,3))
        cats=cc.get("categories",["Individual"]) or ["Individual"]
        saved_cat=min(self.cfg.get("cat",0),max(0,len(cats)-1))
        self.cat_v=tk.StringVar(value=cats[saved_cat]); ttk.Combobox(r2,textvariable=self.cat_v,values=cats,state="readonly",width=20).pack(side="left",padx=2)
        if cc.get("use_county"):
            tk.Label(r2,text=L.t("county"),bg=TH["bg"],fg=TH["fg"],font=self.fn).pack(side="left",padx=(8,3))
            self.cou_v=tk.StringVar(value=self.cfg.get("county","NT"))
            ttk.Combobox(r2,textvariable=self.cou_v,values=cc.get("county_list",YO_COUNTIES),state="readonly",width=6).pack(side="left",padx=2)
        tk.Button(r2,text=L.t("save_cat"),command=self._save_cat,bg=TH["btn_bg"],fg="white",font=("Consolas",10)).pack(side="left",padx=8)

    def _build_flt(self):
        ff=tk.Frame(self,bg=TH["bg"]); ff.pack(fill="x",padx=10,pady=(1,0))
        tk.Label(ff,text=L.t("f_band"),bg=TH["bg"],fg=TH["fg"],font=("Consolas",10)).pack(side="left")
        self.fb_v=tk.StringVar(value=L.t("all"))
        fb=ttk.Combobox(ff,textvariable=self.fb_v,values=[L.t("all")]+self._cc().get("allowed_bands",BANDS_ALL),state="readonly",width=7); fb.pack(side="left",padx=3); fb.bind("<<ComboboxSelected>>",lambda e:self._refresh())
        tk.Label(ff,text=L.t("f_mode"),bg=TH["bg"],fg=TH["fg"],font=("Consolas",10)).pack(side="left",padx=(8,0))
        self.fm_v=tk.StringVar(value=L.t("all"))
        fm=ttk.Combobox(ff,textvariable=self.fm_v,values=[L.t("all")]+self._cc().get("allowed_modes",MODES_ALL),state="readonly",width=7); fm.pack(side="left",padx=3); fm.bind("<<ComboboxSelected>>",lambda e:self._refresh())
        self.sc_lbl=tk.Label(ff,text="",bg=TH["bg"],fg=TH["gold"],font=("Consolas",11,"bold")); self.sc_lbl.pack(side="right",padx=8)

    def _build_tree(self):
        tf=tk.Frame(self,bg=TH["bg"]); tf.pack(fill="both",expand=True,padx=10,pady=3)
        cc=self._cc(); us=cc.get("use_serial",False); hs=cc.get("scoring_mode","none")!="none"
        cols=["nr","call","freq","band","mode","rst_s","rst_r"]; hdrs=[L.t("nr"),L.t("call"),L.t("freq"),L.t("band"),L.t("mode"),L.t("rst_s"),L.t("rst_r")]; wids=[38,115,75,55,55,45,45]
        if us: cols+=["ss","sr"]; hdrs+=[L.t("serial_s"),L.t("serial_r")]; wids+=[45,45]
        cols+=["note","country","date","time"]; hdrs+=[L.t("note"),L.t("country"),L.t("data"),L.t("ora")]; wids+=[95,95,80,50]
        if hs: cols.append("pts"); hdrs.append(L.t("pts")); wids.append(50)
        self.tree=ttk.Treeview(tf,columns=cols,show="headings",selectmode="extended")
        for c,h,w in zip(cols,hdrs,wids):
            self.tree.heading(c,text=h,command=lambda col=c:self._sort_tree(col)); self.tree.column(c,width=w,anchor="center")
        self.tree.tag_configure("dup",background=TH["dup_bg"]); self.tree.tag_configure("alt",background=TH["alt"]); self.tree.tag_configure("spec",background=TH["spec_bg"])
        sb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self.tree.bind("<Double-1>",lambda e:self._edit_sel()); self.tree.bind("<Button-3>",self._on_rclick)
        self.tree.bind("<MouseWheel>",lambda e:self.tree.yview_scroll(int(-1*(e.delta/120)),"units"))
        self.tree.bind("<Button-4>",lambda e:self.tree.yview_scroll(-1,"units"))
        self.tree.bind("<Button-5>",lambda e:self.tree.yview_scroll(1,"units"))
        self._sort_col=None; self._sort_rev=False

    def _sort_tree(self,col):
        if self._sort_col==col: self._sort_rev=not self._sort_rev
        else: self._sort_col=col; self._sort_rev=False
        items=[(self.tree.set(k,col),k) for k in self.tree.get_children("")]
        try: items.sort(key=lambda x:float(x[0]) if x[0].lstrip("-").isdigit() else x[0],reverse=self._sort_rev)
        except: items.sort(key=lambda x:x[0],reverse=self._sort_rev)
        for idx,(_,k) in enumerate(items): self.tree.move(k,"",idx)

    def _build_btns(self):
        """Bara de butoane — 2 rânduri, text complet vizibil, fără trunchiere."""
        BFONT = ("Consolas", 9)
        BPAD  = 2
        def _btn(parent, text, cmd, color, w=9):
            tk.Button(parent, text=text, command=cmd,
                      bg=color, fg="white",
                      font=BFONT, width=w,
                      relief="raised", bd=1,
                      activebackground=color,
                      activeforeground="white").pack(side="left", padx=BPAD, pady=1)

        # ── Rândul 1 ──
        bb1 = tk.Frame(self, bg=TH["bg"]); bb1.pack(fill="x", padx=4, pady=(4,1))
        _btn(bb1, "⚙ " + L.t("settings"),  self._settings,       TH["warn"],   w=10)
        _btn(bb1, "🏆 " + L.t("contests"), self._mgr,             "#C2185B",    w=10)
        _btn(bb1, "📡 CAT",                 self._cat_dlg,         "#1a5276",    w=8)
        _btn(bb1, "📝 Log Nou",             self._new_log_dlg,     "#2e7d32",    w=9)
        _btn(bb1, "🎨 Teme",                self._theme_dlg,       "#6a1b9a",    w=8)
        _btn(bb1, "📊 " + L.t("stats"),    self._stats,           "#3F51B5",    w=10)
        _btn(bb1, "✔ " + L.t("validate"),  self._validate,        TH["ok"],     w=10)
        _btn(bb1, "📤 " + L.t("export"),   self._export_dlg,      "#9C27B0",    w=9)

        # ── Rândul 2 ──
        bb2 = tk.Frame(self, bg=TH["bg"]); bb2.pack(fill="x", padx=4, pady=(1,4))
        _btn(bb2, "📥 " + L.t("import_log"), self._import_menu,   "#E64A19",    w=9)
        _btn(bb2, "↩ " + L.t("undo"),        self._undo,          "#5D4037",    w=8)
        _btn(bb2, "💾 " + L.t("backup"),     self._bak,           "#546E7A",    w=9)
        _btn(bb2, "🔍 " + L.t("search"),     self._search_dlg,    "#00796B",    w=9)
        _btn(bb2, "⏱ Timer",                 self._timer_dlg,     "#004D40",    w=8)
        _btn(bb2, "📝 Log Editor",            self._open_log_editor,"#1B5E20",   w=11)
        _btn(bb2, "🌐 Callbook",              self._open_callbook,  "#1a237e",   w=10)

    def _refresh(self):
        if not self.tree: return
        for i in self.tree.get_children(): self.tree.delete(i)
        cc=self._cc(); hs=cc.get("scoring_mode","none")!="none"; us=cc.get("use_serial",False)
        fb=self.fb_v.get() if self.fb_v else L.t("all"); fm=self.fm_v.get() if self.fm_v else L.t("all")
        sp_calls=set((cc.get("special_scoring") or {}).keys()); seen=set()
        for i,q in enumerate(self.log):
            b,m,c=q.get("b",""),q.get("m",""),q.get("c","").upper()
            if fb!=L.t("all") and b!=fb: continue
            if fm!=L.t("all") and m!=fm: continue
            nr=len(self.log)-i; key=(c,b,m)
            tag=("dup",) if key in seen else ("spec",) if c in sp_calls else ("alt",) if i%2==0 else ()
            seen.add(key); country,_=DXCC.lookup(c)
            vals=[nr,c,q.get("f",""),b,m,q.get("s","59"),q.get("r","59")]
            if us: vals+=[q.get("ss",""),q.get("sr","")]
            vals+=[q.get("n",""),country if country!="Unknown" else "",q.get("d",""),q.get("t","")]
            if hs: vals.append(Score.qso(q,cc,self.cfg))
            self.tree.insert("","end",iid=str(i),values=vals,tags=tag)
        self._upd_info()

    def _upd_info(self):
        cc=self._cc(); call=self.cfg.get("call","NOCALL"); nm=cc.get("name_"+L.g(),cc.get("name_ro","?"))
        cat=self.cat_v.get() if self.cat_v else ""
        if self.info_lbl: self.info_lbl.config(text=f"{call} | {nm} | {cat} | QSO: {len(self.log)}")
        if self.sc_lbl:
            qp,mc,tot=Score.total(self.log,cc,self.cfg)
            if cc.get("scoring_mode","none")!="none":
                self.sc_lbl.config(text=f"Σ {qp}×{mc}={tot}" if cc.get("multiplier_type","none")!="none" else f"Σ {tot}")
            else: self.sc_lbl.config(text="")
        if self.rate_lbl and len(self.log)>=2:
            try:
                dts=sorted([datetime.datetime.strptime(q.get("d","")+" "+q.get("t",""),"%Y-%m-%d %H:%M") for q in self.log[:20] if q.get("d") and q.get("t")])
                if len(dts)>=2:
                    span=(dts[-1]-dts[0]).total_seconds()/3600
                    if span>0: self.rate_lbl.config(text=f"⚡{len(dts)/span:.0f} {L.t('rate')}")
            except: pass

    def _get_dt(self):
        if self.man_v and self.man_v.get(): return self.ent["date"].get().strip(),self.ent["time"].get().strip()
        now=datetime.datetime.utcnow(); return now.strftime("%Y-%m-%d"),now.strftime("%H:%M")

    def _resolve_exchange_sent(self,q,mode="none"):
        if mode=="county": return self.cfg.get("county",self.cfg.get("jud","--"))
        elif mode=="grid": return self.cfg.get("loc","--")
        elif mode=="serial": return q.get("ss","") or "--"
        return "--"

    def _resolve_exchange_rcvd(self,q,mode="log"):
        if mode=="log": return q.get("sr","").strip() or q.get("n","").strip() or "--"
        return "--"

    def _add_qso(self):
        try: self._do_add_qso()
        except Exception as e:
            import traceback; messagebox.showerror(L.t("error"),f"Error:\n{e}\n{traceback.format_exc()[-300:]}")

    def _do_add_qso(self):
        call=self.ent["call"].get().upper().strip()
        if not call: return
        band=self.ent["band"].get(); mode=self.ent["mode"].get()
        if not band or not mode: return
        if not isinstance(self.log,list): self.log=[]
        if self.edit_idx is not None and self.edit_idx>=len(self.log):
            self.edit_idx=None
            if self.log_btn: self.log_btn.config(text=L.t("log"),bg=TH["accent"])
        dup,di=Score.is_dup(self.log,call,band,mode,self.edit_idx)
        if dup and self.edit_idx is None:
            if self._sounds(): beep("warning")
            if not messagebox.askyesno(L.t("dup_warn"),L.t("dup_msg").format(call,band,mode,len(self.log)-di)): return
        ds,ts=self._get_dt(); cc=self._cc()
        qp={"c":call,"b":band,"m":mode,"n":self.ent["note"].get().upper().strip()}
        is_new_mult = Score.is_new_mult(self.log, qp, cc)
        if is_new_mult:
            self._mult_alert(qp)
        elif self._sounds():
            pass  # sunet normal la QSO — optional
        q={"c":call,"b":band,"m":mode,"s":self.ent["rst_s"].get().strip() or "59","r":self.ent["rst_r"].get().strip() or "59",
           "n":self.ent["note"].get().strip(),"d":ds,"t":ts,"f":self.ent["freq"].get().strip()}
        if "ss" in self.ent: q["ss"]=self.ent["ss"].get().strip()
        if "sr" in self.ent: q["sr"]=self.ent["sr"].get().strip()
        if self.edit_idx is not None:
            self.log[self.edit_idx]=q; self.edit_idx=None
            if self.log_btn: self.log_btn.config(text=L.t("log"),bg=TH["accent"])
        else: self.log.insert(0,q); self.undo_stack.append(("add",0,q)); self.serial+=1
        self._clr(); self._refresh(); DM.save_log(self._cid(),self.log)

    # ── v17.0: Only clear call and note — keep freq, band, mode, RST ──
    def _clr(self):
        """Clear only call and note fields. Frequency, band, mode and RST persist."""
        self.ent["call"].delete(0, "end")
        self.ent["note"].delete(0, "end")
        # freq, band, mode, rst_s, rst_r — DO NOT CLEAR
        if "ss" in self.ent:
            self.ent["ss"].delete(0, "end")
            self.ent["ss"].insert(0, str(self.serial))
        if "sr" in self.ent:
            self.ent["sr"].delete(0, "end")
        if self.wb_lbl:
            self.wb_lbl.config(text="")
        self.after(50, self._focus_call)

    def _full_clr(self):
        """Full reset — clears ALL fields including freq, band, mode, RST."""
        self.ent["call"].delete(0, "end")
        self.ent["note"].delete(0, "end")
        self.ent["freq"].delete(0, "end")
        # Reset RST to defaults based on current mode
        mode = self.ent["mode"].get()
        rst = RST_DEFAULTS.get(mode, "59")
        for k in ("rst_s", "rst_r"):
            self.ent[k].delete(0, "end")
            self.ent[k].insert(0, rst)
        if "ss" in self.ent:
            self.ent["ss"].delete(0, "end")
            self.ent["ss"].insert(0, str(self.serial))
        if "sr" in self.ent:
            self.ent["sr"].delete(0, "end")
        if self.wb_lbl:
            self.wb_lbl.config(text="")
        self.after(50, self._focus_call)

    def _edit_sel(self):
        sel=self.tree.selection()
        if not sel: return
        try: idx=int(sel[0])
        except: return
        if idx<0 or idx>=len(self.log): return
        self.edit_idx=idx; q=self.log[idx]
        self.ent["call"].delete(0,"end"); self.ent["call"].insert(0,q.get("c",""))
        self.ent["freq"].delete(0,"end"); self.ent["freq"].insert(0,q.get("f",""))
        cc=self._cc()
        if q.get("b","") in cc.get("allowed_bands",BANDS_ALL): self.ent["band"].set(q["b"])
        if q.get("m","") in cc.get("allowed_modes",MODES_ALL): self.ent["mode"].set(q["m"])
        for k,fk in [("rst_s","s"),("rst_r","r"),("note","n")]:
            self.ent[k].delete(0,"end"); self.ent[k].insert(0,q.get(fk,""))
        for k in ["ss","sr"]:
            if k in self.ent: self.ent[k].delete(0,"end"); self.ent[k].insert(0,q.get(k,""))
        if self.log_btn: self.log_btn.config(text=L.t("update"),bg=TH["warn"])

    def _del_sel(self):
        sel=self.tree.selection()
        if sel and messagebox.askyesno(L.t("confirm_del"),L.t("confirm_del_t")):
            for idx in sorted([int(x) for x in sel],reverse=True):
                if 0<=idx<len(self.log): self.undo_stack.append(("del",idx,copy.deepcopy(self.log[idx]))); self.log.pop(idx)
            self._refresh(); DM.save_log(self._cid(),self.log)

    def _undo(self):
        if not self.undo_stack: messagebox.showinfo("",L.t("undo_empty")); return
        act,idx,q=self.undo_stack.pop()
        if act=="add" and 0<=idx<len(self.log): self.log.pop(idx)
        elif act=="del": self.log.insert(idx,q)
        self._refresh(); DM.save_log(self._cid(),self.log)

    def _on_call_key(self,e=None):
        c=self.ent["call"].get().upper(); pos=self.ent["call"].index(tk.INSERT)
        self.ent["call"].delete(0,tk.END); self.ent["call"].insert(0,c)
        try: self.ent["call"].icursor(min(pos,len(c)))
        except: pass
        if self.wb_lbl and len(c)>=3:
            dup,_=Score.is_dup(self.log,c,self.ent["band"].get(),self.ent["mode"].get(),self.edit_idx)
            if dup: self.wb_lbl.config(text="⚠ DUP",fg=TH["err"])
            elif Score.worked_other(self.log,c,self.ent["band"].get(),self.ent["mode"].get()): self.wb_lbl.config(text=f"ℹ {L.t('wb')}",fg=TH["warn"])
            else: self.wb_lbl.config(text="")
        elif self.wb_lbl: self.wb_lbl.config(text="")

    def _on_freq_out(self,e=None):
        f=self.ent["freq"].get().strip()
        if f:
            b=freq2band(f)
            if b and b in self._cc().get("allowed_bands",BANDS_ALL): self.ent["band"].set(b)

    def _send_freq_to_radio(self):
        """Enter în câmpul freq → trimite frecvența spre radio via CAT."""
        f = self.ent["freq"].get().strip()
        if f and CAT.connected:
            CAT.set_freq(f)
            self._on_freq_out()

    def _on_band_change(self,e=None):
        if not self.ent["freq"].get().strip():
            self.ent["freq"].delete(0,"end"); self.ent["freq"].insert(0,str(BAND_FREQ.get(self.ent["band"].get(),"")))

    def _on_mode_change(self,e=None):
        rst=RST_DEFAULTS.get(self.ent["mode"].get(),"59")
        for k in ("rst_s","rst_r"): self.ent[k].delete(0,"end"); self.ent[k].insert(0,rst)
        if CAT.connected: CAT.set_mode(self.ent["mode"].get())

    def _on_rclick(self,e):
        item=self.tree.identify_row(e.y)
        if item: self.tree.selection_set(item); self.ctx.post(e.x_root,e.y_root)

    def _on_lang(self,e): L.s(self.lang_v.get()); self.cfg["lang"]=self.lang_v.get(); DM.save("config.json",self.cfg); self._rebuild()

    def _on_cchange(self,e):
        DM.save_log(self._cid(),self.log); self.cfg["contest"]=self.cv.get(); DM.save("config.json",self.cfg)
        self.log=DM.load_log(self._cid())
        if not isinstance(self.log,list): self.log=[]
        self.serial=len(self.log)+1; self._rebuild()

    def _cycle_band(self,e=None):
        ab=self._cc().get("allowed_bands",BANDS_ALL) or BANDS_ALL; cur=self.ent["band"].get()
        self.ent["band"].set(ab[(ab.index(cur)+1)%len(ab)] if cur in ab else ab[0]); self._on_band_change()

    def _cycle_mode(self,e=None):
        am=self._cc().get("allowed_modes",MODES_ALL) or MODES_ALL; cur=self.ent["mode"].get()
        self.ent["mode"].set(am[(am.index(cur)+1)%len(am)] if cur in am else am[0]); self._on_mode_change()

    def _tog_man(self):
        m=self.man_v.get()
        self.ent["date"].config(state="normal" if m else "disabled"); self.ent["time"].config(state="normal" if m else "disabled")
        if self.led_c: self.led_c.itemconfig(self.led,fill=TH["led_off"] if m else TH["led_on"])
        if self.st_lbl: self.st_lbl.config(text=L.t("offline") if m else L.t("online"),fg=TH["led_off"] if m else TH["led_on"])
        self.cfg["manual_dt"]=m

    def _save_cat(self):
        if self.cat_v:
            cats=self._cc().get("categories",[])
            self.cfg["cat"]=cats.index(self.cat_v.get()) if self.cat_v.get() in cats else 0
        if self.cou_v: self.cfg["county"]=self.cou_v.get()
        DM.save("config.json",self.cfg); self._upd_info()

    def _switch_contest(self,cid):
        DM.save_log(self._cid(),self.log); self.cfg["contest"]=cid; DM.save("config.json",self.cfg)
        self.log=DM.load_log(cid)
        if not isinstance(self.log,list): self.log=[]
        self.serial=len(self.log)+1; self._rebuild()

    def _rebuild(self):
        self.cfg["win_geo"]=self.geometry()
        for w in self.winfo_children(): w.destroy()
        self.ent={}; self.info_lbl=self.sc_lbl=self.clk=self.rate_lbl=self.cat_lbl=None; self.led_c=self.led=self.st_lbl=self.wb_lbl=self.log_btn=None
        self.tree=self.ctx=self.fb_v=self.fm_v=None; self.cv=self.ccb=self.lang_v=self.man_v=self.cat_v=self.cou_v=None
        self._setup_style(); self._build_menu(); self._build_ui(); self._build_ctx(); self._refresh()
        # Reface focus și mousewheel după rebuild
        self.after(100, self._focus_call)
        self.bind_all("<MouseWheel>",  self._on_mousewheel)
        self.bind_all("<Button-4>",    lambda e: self._on_mousewheel(e, +1))
        self.bind_all("<Button-5>",    lambda e: self._on_mousewheel(e, -1))

    def _tick_clock(self):
        try:
            if not self.winfo_exists(): return
            if self.clk: self.clk.config(text=f"UTC {datetime.datetime.utcnow().strftime('%H:%M:%S')}")
            self.after(1000,self._tick_clock)
        except: pass

    def _tick_save(self):
        try:
            if not self.winfo_exists(): return
            DM.save_log(self._cid(),self.log); self.after(60000,self._tick_save)
        except: pass

    def _fsave(self):
        DM.save_log(self._cid(),self.log); DM.save("config.json",self.cfg); DM.save("contests.json",self.contests)
        if self._sounds(): beep("success")

    def _mgr(self):
        d=ContestMgr(self,self.contests); self.wait_window(d)
        if d.result: self.contests=d.result; DM.save("contests.json",self.contests); self._rebuild()

    def _about(self):
        d=tk.Toplevel(self); d.title(L.t("about")); d.geometry("520x360")
        d.configure(bg=TH["bg"]); d.transient(self); d.resizable(False,False)
        center_dialog(d,self)
        tk.Label(d,text="📻 YO Log PRO v17.1 — Full Edition",
                 bg=TH["bg"],fg=TH["accent"],font=("Consolas",15,"bold")).pack(pady=(16,4))
        tk.Label(d,text="Professional Multi-Contest Amateur Radio Logger",
                 bg=TH["bg"],fg=TH["fg"],font=("Consolas",10)).pack()
        tk.Frame(d,bg=TH["accent"],height=2).pack(fill="x",padx=30,pady=8)
        info=[
            ("Dezvoltat de:","Ardei Constantin-Cătălin (YO8ACR)"),
            ("Email:","yo8acr@gmail.com"),
            ("Repo:","https://github.com/acc1311/YOLogPRO_v17.1"),
            ("",""),
            ("Versiune:","v17.1 — Full Edition (2025)"),
            ("Python:","3.6+ / Tkinter GUI"),
            ("Platforme:","Windows 7/8/10/11, Linux, macOS"),
        ]
        for lbl,val in info:
            if not lbl and not val:
                tk.Frame(d,bg=TH["bg"],height=4).pack(); continue
            rf=tk.Frame(d,bg=TH["bg"]); rf.pack(anchor="w",padx=40,pady=1)
            tk.Label(rf,text=lbl,bg=TH["bg"],fg=TH["fg"],
                     font=("Consolas",9),width=14,anchor="e").pack(side="left")
            tk.Label(rf,text=val,bg=TH["bg"],fg=TH["gold"],
                     font=("Consolas",9),anchor="w").pack(side="left",padx=6)
        tk.Frame(d,bg=TH["accent"],height=2).pack(fill="x",padx=30,pady=8)
        shortcuts="Ctrl+F=Caută  Ctrl+Z=Undo  Ctrl+S=Save  F2=Bandă+  F3=Mod+  Enter=Log"
        tk.Label(d,text=shortcuts,bg=TH["bg"],fg=TH["fg"],
                 font=("Consolas",8)).pack(pady=(0,6))
        tk.Button(d,text=L.t("close"),command=d.destroy,
                  bg=TH["ok"],fg="white",font=("Consolas",11),width=12).pack(pady=8)


    def _settings(self):
        d=tk.Toplevel(self); d.title(L.t("settings")); d.geometry("420x560"); d.configure(bg=TH["bg"]); d.transient(self)
        eo={"bg":TH["entry_bg"],"fg":TH["fg"],"font":self.fn,"insertbackground":TH["fg"]}
        fields=[("call",L.t("call"),self.cfg.get("call","")),("loc",L.t("locator"),self.cfg.get("loc","")),
                ("jud",L.t("county"),self.cfg.get("jud","")),("addr",L.t("address"),self.cfg.get("addr","")),
                ("op_name",L.t("op"),self.cfg.get("op_name","")),("power",L.t("power"),self.cfg.get("power","100")),
                ("email",L.t("email_l"),self.cfg.get("email","")),("soapbox",L.t("soapbox_l"),self.cfg.get("soapbox","73 GL")),
                ("fs",L.t("font_size"),str(self.cfg.get("fs",11)))]
        es={}
        for k,lb,v in fields:
            tk.Label(d,text=lb,bg=TH["bg"],fg=TH["fg"]).pack(anchor="w",padx=15)
            e=tk.Entry(d,width=35,**eo); e.insert(0,v); e.pack(pady=2,padx=15); es[k]=e
        snd_v=tk.BooleanVar(value=self.cfg.get("sounds",True))
        tk.Checkbutton(d,text=L.t("en_sounds"),variable=snd_v,bg=TH["bg"],fg=TH["fg"],selectcolor=TH["entry_bg"],activebackground=TH["bg"]).pack(anchor="w",padx=15,pady=4)
        def save():
            for k in es:
                v=es[k].get().strip(); self.cfg[k]=v.upper() if k in {"call","loc","jud"} else v
            try: self.cfg["fs"]=int(es["fs"].get().strip())
            except: self.cfg["fs"]=11
            self.cfg["sounds"]=snd_v.get(); DM.save("config.json",self.cfg); d.destroy(); self._rebuild()
        tk.Button(d,text=L.t("save"),command=save,bg=TH["accent"],fg="white",width=12).pack(pady=12); center_dialog(d,self)

    def _stats(self): StatsWindow(self,self.log,self._cc(),self.cfg)
    def _validate(self):
        ok,msg,_=Score.validate(self.log,self._cc(),self.cfg)
        (messagebox.showinfo if ok else messagebox.showwarning)(L.t("val_result"),msg)
    def _search_dlg(self): SearchDialog(self,self.log)
    def _timer_dlg(self): TimerDialog(self)
    def _verify_hash(self):
        try:
            h=hashlib.md5(json.dumps(self.log,ensure_ascii=False,sort_keys=True).encode("utf-8")).hexdigest()
            messagebox.showinfo(L.t("hash_ok"),L.t("verify_ok").format(len(self.log),h))
        except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _clear_log(self):
        if self.log and messagebox.askyesno(L.t("clear_log"),L.t("clear_conf")):
            DM.backup(self._cid(),self.log); self.log.clear(); self.serial=1; self.undo_stack.clear()
            self._refresh(); DM.save_log(self._cid(),self.log)

    def _import_menu(self):
        d=tk.Toplevel(self); d.title(L.t("import_log")); d.geometry("280x200"); d.configure(bg=TH["bg"]); d.transient(self)
        for txt,cmd in [("ADIF (.adi/.adif)",lambda:[d.destroy(),self._import_adif()]),("CSV (.csv)",lambda:[d.destroy(),self._import_csv()]),("Cabrillo (.log)",lambda:[d.destroy(),self._import_cabrillo()])]:
            tk.Button(d,text=txt,command=cmd,bg=TH["accent"],fg="white",width=24).pack(pady=6)
        center_dialog(d,self)

    def _import_adif(self):
        fp=filedialog.askopenfilename(filetypes=[("ADIF","*.adi *.adif"),("All","*.*")])
        if fp:
            try:
                with open(fp,"r",encoding="utf-8",errors="replace") as f: self._do_import(Importer.parse_adif(f.read()))
            except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _import_csv(self):
        fp=filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("All","*.*")])
        if fp:
            try:
                with open(fp,"r",encoding="utf-8",errors="replace") as f: self._do_import(Importer.parse_csv(f.read()))
            except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _import_cabrillo(self):
        fp=filedialog.askopenfilename(filetypes=[("Cabrillo","*.log"),("All","*.*")])
        if fp:
            try:
                with open(fp,"r",encoding="utf-8",errors="replace") as f: self._do_import(Importer.parse_cabrillo(f.read()))
            except Exception as e: messagebox.showerror(L.t("error"),str(e))
    def _do_import(self,qsos):
        if qsos:
            if not isinstance(self.log,list): self.log=[]
            self.log.extend(qsos); self.serial=len(self.log)+1; self._refresh(); DM.save_log(self._cid(),self.log)
            messagebox.showinfo("OK",L.t("imp_ok").format(len(qsos)))
        else: messagebox.showwarning("","0 QSO")

    def _check_before_export(self):
        if not self.log: messagebox.showwarning(L.t("error"),"Log gol!"); return False
        ok,msg,_=Score.validate(self.log,self._cc(),self.cfg)
        if not ok:
            if not messagebox.askyesno(L.t("exp_warn"),L.t("exp_warn_msg").format(msg)): return False
        DM.backup(self._cid(),self.log); return True

    def _export_dlg(self):
        d=tk.Toplevel(self); d.title(L.t("export")); d.geometry("300x310"); d.configure(bg=TH["bg"]); d.transient(self)
        for txt,cmd in [("Cabrillo 3.0 (.log)",lambda:self._exp_cab(d)),(L.t("exp_cab2"),lambda:self._exp_cab2(d)),("ADIF 3.1 (.adi)",lambda:self._exp_adif(d)),("CSV (.csv)",lambda:self._exp_csv(d)),(L.t("exp_edi"),lambda:self._exp_edi(d)),(L.t("exp_print"),lambda:self._exp_print(d))]:
            tk.Button(d,text=txt,command=cmd,bg=TH["accent"],fg="white",width=28).pack(pady=4)
        center_dialog(d,self)

    def _exp_cab(self,parent=None):
        if not self._check_before_export(): return
        try:
            my=self.cfg.get("call","NOCALL"); cc=self._cc()
            nm=cc.get("cabrillo_name","") or cc.get("name_en",cc.get("name_ro","CONTEST"))
            pw=int(self.cfg.get("power","100")); cat_power="QRP" if pw<=5 else ("LOW" if pw<=100 else "HIGH")
            ef=cc.get("exchange_format","none")
            lines=["START-OF-LOG: 3.0",f"CONTEST: {nm}",f"CALLSIGN: {my}",f"GRID-LOCATOR: {self.cfg.get('loc','')}","CATEGORY-OPERATOR: SINGLE-OP","CATEGORY-BAND: ALL",f"CATEGORY-POWER: {cat_power}","CATEGORY-MODE: MIXED",f"NAME: {self.cfg.get('op_name','')}",f"ADDRESS: {self.cfg.get('addr','')}","SOAPBOX: Logged with YO Log PRO v17.1",f"SOAPBOX: {self.cfg.get('soapbox','73 GL')}","CREATED-BY: YO Log PRO v17.0"]
            for q in self.log:
                freq=q.get("f","") or str(BAND_FREQ.get(q.get("b",""),0))
                try: freq=str(int(float(freq)))
                except: pass
                es=self._resolve_exchange_sent(q,ef); er=self._resolve_exchange_rcvd(q,"log")
                date=q.get("d","").replace("-",""); time=q.get("t","").replace(":","")
                lines.append(f"QSO: {freq:>6} {q.get('m','SSB'):<5} {date} {time} {my:<13} {q.get('s','59'):<4} {es:<10} {q.get('c',''):<13} {q.get('r','59'):<4} {er}")
            lines.append("END-OF-LOG:"); content="\n".join(lines)
            def do_save(text):
                fp=filedialog.asksaveasfilename(defaultextension=".log",filetypes=[("Cabrillo","*.log")],initialfile=f"cab3_{self._cid()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.log")
                if fp:
                    with open(fp,"w",encoding="utf-8") as f: f.write(text)
                    messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            PreviewDialog(self,L.t("preview_t")+" — Cabrillo 3.0",content,do_save)
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _exp_cab2(self,parent=None):
        if not self._check_before_export(): return
        cfg_dlg=Cab2ConfigDialog(self,self.cfg); self.wait_window(cfg_dlg)
        if not cfg_dlg.result: return
        exch_sent_mode=cfg_dlg.result["sent"]; exch_rcvd_mode=cfg_dlg.result["rcvd"]
        self.cfg["cab2_exch_sent"]=exch_sent_mode; self.cfg["cab2_exch_rcvd"]=exch_rcvd_mode; DM.save("config.json",self.cfg)
        try:
            my=self.cfg.get("call","NOCALL"); cc=self._cc()
            nm=(cc.get("cabrillo_name","") or cc.get("name_en",cc.get("name_ro","CONTEST"))).upper()
            cat_val=self.cat_v.get() if self.cat_v else ""; cat_num="1"
            if cat_val:
                m_cat=re.match(r'^([A-Za-z])',cat_val)
                if m_cat: cat_num=str(ord(m_cat.group(1).upper())-ord('A')+1)
                else:
                    cats=cc.get("categories",["Individual"])
                    cat_num=str(cats.index(cat_val)+1) if cat_val in cats else "1"
            _,_,tot=Score.total(self.log,cc,self.cfg)
            lines=["START-OF-LOG: 2.0","CREATED BY: YO Log PRO v17.1",f"CONTEST: {nm}",f"CALLSIGN: {my}",f"NAME: {self.cfg.get('op_name','')}",f"CATEGORY: {cat_num}",f"CLAIMED-SCORE: {tot}",f"ADDRESS: {self.cfg.get('addr','')}",f"EMAIL: {self.cfg.get('email','')}","SOAPBOX: Logged with YO Log PRO v17.1",f"SOAPBOX: {self.cfg.get('soapbox','73 GL')}","SOAPBOX:  mo  yyyy mm dd hhmm call         rs exc call          rs exc","SOAPBOX:  ** ********** **** ************* **  ** ************* **  **"]
            for q in self.log:
                freq=q.get("f","") or str(BAND_FREQ.get(q.get("b",""),0))
                try: freq=str(int(float(freq)))
                except: pass
                mode=CAB2_MODE_MAP.get(q.get("m","SSB"),"PH")
                date=q.get("d","")
                if len(date)==8 and "-" not in date: date=f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                time_str=q.get("t","").replace(":","")[:4]
                es=self._resolve_exchange_sent(q,exch_sent_mode); er=self._resolve_exchange_rcvd(q,exch_rcvd_mode)
                lines.append(f"QSO: {freq} {mode} {date} {time_str} {my:<13} {q.get('s','59'):>2}  {es:<2} {q.get('c',''):<13} {q.get('r','59'):>2}  {er:<2}")
            lines.append("END-OF-LOG:"); content="\n".join(lines)
            def do_save(text):
                fp=filedialog.asksaveasfilename(defaultextension=".log",filetypes=[("Cabrillo","*.log")],initialfile=f"cab2_{self._cid()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.log")
                if fp:
                    with open(fp,"w",encoding="utf-8") as f: f.write(text)
                    messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            PreviewDialog(self,L.t("preview_t")+" — Cabrillo 2.0",content,do_save)
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _exp_adif(self,parent=None):
        if not self._check_before_export(): return
        try:
            my_loc=self.cfg.get("loc","")
            lines=["<ADIF_VER:5>3.1.0","<PROGRAMID:14>YO_Log_PRO_v17","<PROGRAMVERSION:5>17.1",f"<MY_GRIDSQUARE:{len(my_loc)}>{my_loc}","<EOH>"]
            for q in self.log:
                dc=q.get("d","").replace("-",""); tc=q.get("t","").replace(":","")+"00"; note=q.get("n","")
                freq_mhz=""
                if q.get("f",""):
                    try: freq_mhz=f"{float(q['f'])/1000:.4f}"
                    except: pass
                def af(tag,val): return f"<{tag}:{len(str(val))}>{val}" if val else ""
                parts=[af("CALL",q.get("c","")),af("BAND",q.get("b","")),af("MODE",q.get("m","")),af("QSO_DATE",dc),af("TIME_ON",tc),af("RST_SENT",q.get("s","59")),af("RST_RCVD",q.get("r","59"))]
                if freq_mhz: parts.append(af("FREQ",freq_mhz))
                if Loc.valid(note[:6] if len(note)>=6 else note): parts.append(af("GRIDSQUARE",note))
                elif note: parts.append(af("COMMENT",note))
                if q.get("ss"): parts.append(af("STX",q["ss"]))
                if q.get("sr"): parts.append(af("SRX",q["sr"]))
                parts.append("<EOR>"); lines.append("".join(p for p in parts if p))
            fp=filedialog.asksaveasfilename(defaultextension=".adi",filetypes=[("ADIF","*.adi")],initialfile=f"adif_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.adi")
            if fp:
                with open(fp,"w",encoding="utf-8") as f: f.write("\n".join(lines))
                messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _exp_csv(self,parent=None):
        if not self._check_before_export(): return
        try:
            fp=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile=f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv")
            if not fp: return
            cc=self._cc()
            with open(fp,"w",encoding="utf-8",newline='') as f:
                w=csv.writer(f); w.writerow(["Nr","Date","Time","Call","Freq","Band","Mode","RST_S","RST_R","Nr_S","Nr_R","Note","Country","Score"])
                for i,q in enumerate(self.log):
                    c,_=DXCC.lookup(q.get("c",""))
                    w.writerow([len(self.log)-i,q.get("d",""),q.get("t",""),q.get("c",""),q.get("f",""),q.get("b",""),q.get("m",""),q.get("s",""),q.get("r",""),q.get("ss",""),q.get("sr",""),q.get("n",""),c if c!="Unknown" else "",Score.qso(q,cc,self.cfg)])
            messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _exp_edi(self,parent=None):
        if not self._check_before_export(): return
        try:
            my=self.cfg.get("call","NOCALL"); my_loc=self.cfg.get("loc",""); cc=self._cc()
            nm=cc.get("cabrillo_name","") or cc.get("name_en","VHF"); now=datetime.datetime.utcnow()
            lines=["[REG1TEST;1]",f"TName={nm}",f"TDate={now.strftime('%y%m%d')};{now.strftime('%y%m%d')}",f"PCall={my}",f"PWWLo={my_loc}","PExch=",f"PAdr1={self.cfg.get('addr','')}","PBand=144","PSect=","[Remarks]","Logged with YO Log PRO v17.1","[QSORecords]"]
            for q in self.log:
                dt=q.get("d","").replace("-","")[2:]; tm=q.get("t","").replace(":","")[:4]; loc=q.get("n","")
                km=int(Loc.dist(my_loc,loc)) if my_loc and Loc.valid(loc) else 0
                lines.append(f"{dt};{tm};{q.get('c','')};1;{q.get('s','59')};{q.get('ss','')};{q.get('r','59')};{q.get('sr','')};{loc};{km}")
            fp=filedialog.asksaveasfilename(defaultextension=".edi",filetypes=[("EDI","*.edi")],initialfile=f"edi_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.edi")
            if fp:
                with open(fp,"w",encoding="utf-8") as f: f.write("\n".join(lines))
                messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _exp_print(self,parent=None):
        if not self._check_before_export(): return
        try:
            my=self.cfg.get("call","NOCALL"); cc=self._cc(); nm=cc.get("name_"+L.g(),cc.get("name_ro","?"))
            lines=[f"{'='*90}",f"YO Log PRO v17.0 — {my} — {nm}",f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",f"{'='*90}",
                   f"{'Nr':<4} {'Call':<13} {'Freq':<8} {'Band':<6} {'Mode':<6} {'RSTt':<5} {'RSTr':<5} {'Note':<10} {'Country':<15} {'Date':<11} {'Time':<6} {'Pts':<5}",f"{'-'*90}"]
            for i,q in enumerate(self.log):
                c,_=DXCC.lookup(q.get("c",""))
                lines.append(f"{len(self.log)-i:<4} {q.get('c',''):<13} {q.get('f',''):<8} {q.get('b',''):<6} {q.get('m',''):<6} {q.get('s',''):<5} {q.get('r',''):<5} {q.get('n',''):<10} {c[:14]:<15} {q.get('d',''):<11} {q.get('t',''):<6} {Score.qso(q,cc,self.cfg):<5}")
            lines.append(f"{'='*90}"); qp,mc,tot=Score.total(self.log,cc,self.cfg); lines.append(f"Total QSO: {len(self.log)}  |  Score: {qp}×{mc}={tot}")
            fp=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")],initialfile=f"print_{self._cid()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt")
            if fp:
                with open(fp,"w",encoding="utf-8") as f: f.write("\n".join(lines))
                messagebox.showinfo(L.t("exp_ok"),f"→ {os.path.basename(fp)}")
            if parent: parent.destroy()
        except Exception as e: messagebox.showerror(L.t("error"),str(e))

    def _print_log(self): self._exp_print()

    def _bak(self):
        if DM.backup(self._cid(),self.log): messagebox.showinfo("OK",L.t("bak_ok"))
        else: messagebox.showerror(L.t("error"),L.t("bak_err"))

    def _exit(self):
        if messagebox.askyesno(L.t("exit_t"),L.t("exit_m")):
            self.cfg["win_geo"]=self.geometry()
            CAT.disconnect()
            DM.save_log(self._cid(),self.log); DM.save("config.json",self.cfg); DM.save("contests.json",self.contests)
            DM.backup(self._cid(),self.log); self.destroy()

    # ─── v17.1: Deschidere ferestre noi ─────────────────────────

    def _open_log_editor(self):
        """Deschide editorul dedicat de log — fereastră separată completă."""
        LogEditorWindow(
            self,
            log_ref      = self.log,
            contests_ref = self.contests,
            cfg_ref      = self.cfg,
            on_change    = self._refresh,
            cid_getter   = self._cid,
        )

    def _open_callbook(self, call=""):
        """Deschide dialogul Callbook Lookup."""
        if not call:
            # Încearcă să ia indicativul din câmpul activ
            try: call = self.ent.get("call","").get().strip().upper()
            except Exception: call = ""
        def _fill(data):
            loc = data.get("loc","")
            if loc and self.ent.get("note"):
                self.ent["note"].delete(0,"end")
                self.ent["note"].insert(0, loc)
        CallbookDialog(self, call=call, on_fill=_fill)

    def _open_bandmap(self):
        """Deschide fereastra Band Map."""
        BandMapWindow(self, lambda: self.log, lambda: self.cfg)

    def _open_cluster(self):
        """Deschide fereastra DX Cluster."""
        def on_spot(call, freq):
            """Click pe spot → completare indicativ + frecvență în formular."""
            try:
                if self.ent.get("call"):
                    self.ent["call"].delete(0, "end")
                    self.ent["call"].insert(0, call.upper())
                if self.ent.get("freq") and freq:
                    self.ent["freq"].delete(0, "end")
                    self.ent["freq"].insert(0, str(freq))
                    self._on_freq_out()
                self.ent["call"].focus_set()
            except Exception:
                pass
        DXClusterWindow(self, on_spot=on_spot)

    def _open_live_score(self):
        """Deschide panoul Scor Live."""
        LiveScorePanel(self, lambda: self.log, lambda: self.cfg, self._cc)

    def _open_rate_stats(self):
        """Deschide fereastra Statistici Rate QSO."""
        RateStatsWindow(self, lambda: self.log, lambda: self.cfg)

    def _load_cty_dat(self):
        """Încarcă un fișier cty.dat pentru DXCC extins."""
        fp = filedialog.askopenfilename(
            title="Selectați cty.dat",
            filetypes=[("CTY Database", "cty.dat"), ("All files", "*.*")])
        if fp:
            ok, msg = DXCC.load_cty_dat(fp)
            if ok:
                messagebox.showinfo("CTY.dat", f"✓ {msg}\n\nDXCC DB actualizat cu {len(DXCC.DB)} prefixe.")
            else:
                messagebox.showerror("CTY.dat", f"Eroare: {msg}")

    def _mult_alert(self, qso):
        """Alertă audio + vizuală la multiplicator nou."""
        cc = self._cc()
        if not Score.is_new_mult(self.log, qso, cc):
            return
        # Sunet alert
        if self.cfg.get("sounds", True):
            if HAS_SOUND:
                try:
                    import winsound
                    for _ in range(3):
                        winsound.Beep(1200, 120)
                        time.sleep(0.08)
                except Exception:
                    pass
        # Flash vizual + mesaj
        mt = cc.get("multiplier_type", "none")
        n = qso.get("n","").upper().strip(); c = qso.get("c","").upper()
        mult_val = "?"
        if mt == "dxcc": mult_val = DXCC.lookup(c)[0]
        elif mt in ("county","grid"): mult_val = n
        elif mt == "band": mult_val = qso.get("b","")
        try:
            if self.sc_lbl:
                orig_bg = self.sc_lbl.cget("bg")
                orig_fg = self.sc_lbl.cget("fg")
                self.sc_lbl.config(text=f"✦ MULT NOU: {mult_val} ✦", fg=TH["gold"])
                self.after(3000, lambda: self.sc_lbl.config(fg=TH["gold"]))
        except Exception:
            pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
