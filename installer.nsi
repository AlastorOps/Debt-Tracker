; -----------------------------------------------
; Debt Tracker - Windows Installer Script (NSIS)
; -----------------------------------------------

!define APP_NAME "Debt Tracker"
!define APP_VERSION "2.0 (English Version)"
!define APP_EXE "DebtTracker.exe"
!define APP_ICON "debt_tracker_icon.ico"

!define INSTALL_DIR "$PROGRAMFILES\DebtTracker"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; Installer output
OutFile "DebtTracker_Setup.exe"

; Default install directory
InstallDir "${INSTALL_DIR}"

; Request admin rights
RequestExecutionLevel admin

; Modern UI
!include "MUI2.nsh"

; Installer icons
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"

; Welcome page
!define MUI_WELCOMEPAGE_TITLE "Welcome to Debt Tracker Setup"
!define MUI_WELCOMEPAGE_TEXT "This will install Debt Tracker ${APP_VERSION} on your computer.$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Install files page
!insertmacro MUI_PAGE_INSTFILES

; Finish page - option to launch app
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Debt Tracker now"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; -----------------------------------------------
; App name and version
; -----------------------------------------------
Name "${APP_NAME} ${APP_VERSION}"
BrandingText "${APP_NAME} v${APP_VERSION}"

; -----------------------------------------------
; Install Section
; -----------------------------------------------
Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy main executable
    File "dist\${APP_EXE}"

    ; Copy icon
    File "${APP_ICON}"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add to Windows "Add or Remove Programs"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_ICON}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "Alastor"

    ; Desktop shortcut
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
                   "$INSTDIR\${APP_EXE}" \
                   "" \
                   "$INSTDIR\${APP_ICON}" \
                   0

    ; Start Menu folder and shortcut
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
                    "$INSTDIR\${APP_EXE}" \
                    "" \
                    "$INSTDIR\${APP_ICON}" \
                    0

    ; Uninstall shortcut in Start Menu
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
                    "$INSTDIR\Uninstall.exe"

SectionEnd

; -----------------------------------------------
; Uninstall Section
; -----------------------------------------------
Section "Uninstall"
    ; Delete main files
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\${APP_ICON}"
    Delete "$INSTDIR\Uninstall.exe"

    ; Delete shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"

    ; Remove folders
    RMDir "$SMPROGRAMS\${APP_NAME}"
    RMDir "$INSTDIR"

    ; Remove from registry
    DeleteRegKey HKLM "${UNINSTALL_KEY}"

    ; Show success message with dynamic Documents path
    MessageBox MB_OK "Debt Tracker has been uninstalled successfully.$\r$\n$\r$\nYour database file (if any) has been kept safe in:$\r$\n$\r$\n$DOCUMENTS\DebtTracker$\r$\n$\r$\nYou can delete this folder manually if you no longer need the data."

SectionEnd