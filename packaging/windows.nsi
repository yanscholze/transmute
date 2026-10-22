; Native Windows installer. Payload is built by Windows Python/PyInstaller.
Unicode True
!include "MUI2.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
Name "Transmute"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\Transmute"
InstallDirRegKey HKCU "Software\Transmute" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "Transmute"
VIAddVersionKey "FileDescription" "Instalador Transmute"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Este instalador exige Windows de 64 bits."
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "Este aplicativo exige Windows 10 ou mais recente."
    Abort
  ${EndIf}
FunctionEnd

Section "Transmute"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\Transmute"
  CreateShortcut "$SMPROGRAMS\Transmute\Transmute.lnk" "$INSTDIR\ConversorDeBases.exe"
  CreateShortcut "$SMPROGRAMS\Transmute\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Transmute" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "DisplayName" "Transmute"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "DisplayIcon" "$INSTDIR\ConversorDeBases.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "UninstallString" '$"$INSTDIR\Uninstall.exe$"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute" "NoRepair" 1
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  ; Enumerated package files only: never recursively erase an operator's data.
  !include "${UNINSTALL_LIST}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\Transmute\Transmute.lnk"
  Delete "$SMPROGRAMS\Transmute\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\Transmute"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Transmute"
  DeleteRegKey HKCU "Software\Transmute"
SectionEnd
