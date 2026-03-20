; ─────────────────────────────────────────────────────────────
;  YO Log PRO v17.1 — NSIS Installer Script
;  Dezvoltat de: Ardei Constantin-Cătălin (YO8ACR)
;  Compatibil: Windows 7 / 8 / 10 / 11 (x64)
; ─────────────────────────────────────────────────────────────

Unicode True

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; ── Informatii generale ───────────────────────────────────────
!define APP_NAME        "YO Log PRO"
!define APP_VERSION     "17.1"
!define APP_FULL_NAME   "YO Log PRO v17.1"
!define APP_EXE         "YO_Log_PRO_v17.1.exe"
!define APP_PUBLISHER   "Ardei Constantin-Cătălin (YO8ACR)"
!define APP_URL         "https://github.com/acc1311/YOLogPRO_v17.1"
!define INSTALL_DIR     "$PROGRAMFILES64\YO Log PRO"
!define REG_KEY         "Software\Microsoft\Windows\CurrentVersion\Uninstall\YOLogPRO"

Name            "${APP_FULL_NAME}"
OutFile         "YO_Log_PRO_v17.1_Setup.exe"
InstallDir      "${INSTALL_DIR}"
InstallDirRegKey HKLM "${REG_KEY}" "InstallLocation"
RequestExecutionLevel admin
BrandingText    "YO Log PRO v${APP_VERSION} — YO8ACR"

; ── Compresie ─────────────────────────────────────────────────
SetCompressor /SOLID lzma
SetCompressorDictSize 32

; ── Interfata MUI2 ────────────────────────────────────────────
!define MUI_ABORTWARNING
!define MUI_ICON                    "icon.ico"
!define MUI_UNICON                  "icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP_NOSTRETCH
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT

!define MUI_WELCOMEPAGE_TITLE       "Bun venit la instalarea ${APP_FULL_NAME}"
!define MUI_WELCOMEPAGE_TEXT        "Acest wizard va instala ${APP_FULL_NAME} pe calculatorul dumneavoastră.$\r$\n$\r$\nProgram de logare pentru radioamatori, dezvoltat de YO8ACR.$\r$\n$\r$\nCompatibil cu Windows 7, 8, 10 și 11.$\r$\n$\r$\nApăsați Next pentru a continua."

!define MUI_FINISHPAGE_TITLE        "Instalare finalizată!"
!define MUI_FINISHPAGE_TEXT         "${APP_FULL_NAME} a fost instalat cu succes.$\r$\n$\r$\nPuteți lansa programul din scurtătura de pe Desktop sau din meniul Start."
!define MUI_FINISHPAGE_RUN          "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT     "Lansează ${APP_FULL_NAME} acum"
!define MUI_FINISHPAGE_SHOWREADME   "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Deschide README"

; ── Pagini installer ──────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE      "README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ── Pagini uninstaller ────────────────────────────────────────
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ── Limba ─────────────────────────────────────────────────────
!insertmacro MUI_LANGUAGE "Romanian"
!insertmacro MUI_LANGUAGE "English"

; ═════════════════════════════════════════════════════════════
;  SECTIUNEA DE INSTALARE
; ═════════════════════════════════════════════════════════════
Section "YO Log PRO (obligatoriu)" SecMain
    SectionIn RO   ; Read Only — nu poate fi debifat

    SetOutPath "$INSTDIR"

    ; ── Copiaza fisierele ─────────────────────────────────────
    File "dist\${APP_EXE}"
    File "icon.ico"
    File "README.md"

    ; ── Copiaza documentatia (daca exista) ───────────────────
    IfFileExists "docs\*.*" 0 +3
        SetOutPath "$INSTDIR\docs"
        File /r "docs\*.*"

    SetOutPath "$INSTDIR"

    ; ── Scurtatura Desktop ────────────────────────────────────
    CreateShortcut "$DESKTOP\${APP_FULL_NAME}.lnk" \
                   "$INSTDIR\${APP_EXE}" "" \
                   "$INSTDIR\icon.ico" 0 \
                   SW_SHOWNORMAL "" \
                   "YO Log PRO — Program de logare radioamatori"

    ; ── Scurtatura meniu Start ────────────────────────────────
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_FULL_NAME}.lnk" \
                    "$INSTDIR\${APP_EXE}" "" \
                    "$INSTDIR\icon.ico" 0 \
                    SW_SHOWNORMAL "" \
                    "YO Log PRO — Program de logare radioamatori"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Dezinstalare ${APP_NAME}.lnk" \
                    "$INSTDIR\Uninstall.exe"

    ; ── Inregistrare in Add/Remove Programs ──────────────────
    WriteRegStr   HKLM "${REG_KEY}" "DisplayName"      "${APP_FULL_NAME}"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"   "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "Publisher"        "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${REG_KEY}" "URLInfoAbout"     "${APP_URL}"
    WriteRegStr   HKLM "${REG_KEY}" "InstallLocation"  "$INSTDIR"
    WriteRegStr   HKLM "${REG_KEY}" "UninstallString"  "$INSTDIR\Uninstall.exe"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayIcon"      "$INSTDIR\icon.ico"
    WriteRegDWORD HKLM "${REG_KEY}" "NoModify"         1
    WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"         1

    ; ── Dimensiune estimata instalare (~30 MB) ────────────────
    WriteRegDWORD HKLM "${REG_KEY}" "EstimatedSize" 30720

    ; ── Scrie uninstaller ─────────────────────────────────────
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

; ═════════════════════════════════════════════════════════════
;  SECTIUNEA DE DEZINSTALARE
; ═════════════════════════════════════════════════════════════
Section "Uninstall"

    ; ── Sterge fisierele ──────────────────────────────────────
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir  /r "$INSTDIR\docs"
    RMDir  "$INSTDIR"

    ; ── Sterge scurtaturile ───────────────────────────────────
    Delete "$DESKTOP\${APP_FULL_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_FULL_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Dezinstalare ${APP_NAME}.lnk"
    RMDir  "$SMPROGRAMS\${APP_NAME}"

    ; ── Sterge din registry ───────────────────────────────────
    DeleteRegKey HKLM "${REG_KEY}"

    ; ── Sterge datele utilizatorului (optional, cu confirmare) 
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Doriți să ștergeți și datele salvate (loguri, configurații)?$\r$\nAtenție: această acțiune este ireversibilă!" \
        IDNO +2
        RMDir /r "$APPDATA\YOLogPRO"

SectionEnd

; ═════════════════════════════════════════════════════════════
;  FUNCTII HELPER
; ═════════════════════════════════════════════════════════════

; ── Verifica daca e deja instalat ─────────────────────────────
Function .onInit
    ; Verifica arhitectura (Win7+ 64-bit)
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP \
            "YO Log PRO v17.1 necesită Windows pe 64 de biți.$\r$\nInstalarea va fi anulată."
        Abort
    ${EndIf}

    ; Verifica daca e deja instalat — ofera dezinstalare
    ReadRegStr $R0 HKLM "${REG_KEY}" "UninstallString"
    StrCmp $R0 "" done

    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_FULL_NAME} este deja instalat.$\r$\nApăsați OK pentru a dezinstala versiunea existentă înainte de a continua." \
        IDOK uninst
    Abort

    uninst:
        ClearErrors
        ExecWait '$R0 /S'

    done:
FunctionEnd

; ── Pagina de directoare — titlu personalizat ─────────────────
Function .onVerifyInstDir
    IfFileExists "$INSTDIR\*.exe" 0 +2
        MessageBox MB_OK "Directorul selectat conține deja fișiere EXE. Vă recomandăm să alegeți un director nou."
FunctionEnd
