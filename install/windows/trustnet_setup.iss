; TrustNet Windows Installer — Inno Setup Script

#define AppName "TrustNet"
#define AppVersion "1.0.0"
#define AppPublisher "Thames Senneam"
#define AppURL "https://github.com/thamessenneam/TrustNet"
#define AppExe "trustnet.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=dist\installer
OutputBaseFilename=TrustNet-Setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
ChangesEnvironment=yes
ChangesAssociations=yes
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Installer
VersionInfoCompany={#AppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";        GroupDescription: "Additional icons:"
Name: "startnode";      Description: "Start TrustNet node automatically at login"; GroupDescription: "Network:"; Flags: checked
Name: "contextmenu";    Description: "Add TrustNet to right-click menu";  GroupDescription: "Integration:"; Flags: checked

[Files]
Source: "dist\trustnet.exe";      DestDir: "{app}"; Flags: ignoreversion
Source: "dist\trustnet-node.exe"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\dist\trustnet-node.exe'))
Source: "LICENSE.txt";            DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\TrustNet";             Filename: "{app}\{#AppExe}"
Name: "{group}\Start TrustNet Node";  Filename: "{app}\{#AppExe}"; Parameters: "node start"
Name: "{group}\Stop TrustNet Node";   Filename: "{app}\{#AppExe}"; Parameters: "node stop"
Name: "{group}\Uninstall TrustNet";   Filename: "{uninstallexe}"
Name: "{autodesktop}\TrustNet";       Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; ── Add app dir to PATH ───────────────────────────────────────────────────────
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
  ValueType: expandsz; ValueName: "Path"; \
  ValueData: "{olddata};{app}"; \
  Check: NeedsAddPath(ExpandConstant('{app}')); \
  Flags: preservestringtype

; ── Right-click menu: Files ───────────────────────────────────────────────────
Root: HKCR; Subkey: "*\shell\TrustNet"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "TrustNet"; \
  Flags: uninsdeletekey; Tasks: contextmenu

Root: HKCR; Subkey: "*\shell\TrustNet"; \
  ValueType: string; ValueName: "SubCommands"; ValueData: ""; \
  Tasks: contextmenu

Root: HKCR; Subkey: "*\shell\TrustNet\shell\sign"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Sign File"; \
  Tasks: contextmenu

Root: HKCR; Subkey: "*\shell\TrustNet\shell\sign\command"; \
  ValueType: string; ValueName: ""; \
  ValueData: """{app}\{#AppExe}"" sign ""%1"""; \
  Tasks: contextmenu

Root: HKCR; Subkey: "*\shell\TrustNet\shell\verify"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Verify File"; \
  Tasks: contextmenu

Root: HKCR; Subkey: "*\shell\TrustNet\shell\verify\command"; \
  ValueType: string; ValueName: ""; \
  ValueData: """{app}\{#AppExe}"" verify ""%1"""; \
  Tasks: contextmenu

; ── Right-click menu: Folders ─────────────────────────────────────────────────
Root: HKCR; Subkey: "Directory\shell\TrustNet"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "TrustNet"; \
  Flags: uninsdeletekey; Tasks: contextmenu

Root: HKCR; Subkey: "Directory\shell\TrustNet"; \
  ValueType: string; ValueName: "SubCommands"; ValueData: ""; \
  Tasks: contextmenu

Root: HKCR; Subkey: "Directory\shell\TrustNet\shell\sign"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Sign Folder"; \
  Tasks: contextmenu

Root: HKCR; Subkey: "Directory\shell\TrustNet\shell\sign\command"; \
  ValueType: string; ValueName: ""; \
  ValueData: """{app}\{#AppExe}"" sign ""%1"""; \
  Tasks: contextmenu

Root: HKCR; Subkey: "Directory\shell\TrustNet\shell\verify"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Verify Folder"; \
  Tasks: contextmenu

Root: HKCR; Subkey: "Directory\shell\TrustNet\shell\verify\command"; \
  ValueType: string; ValueName: ""; \
  ValueData: """{app}\{#AppExe}"" verify ""%1"""; \
  Tasks: contextmenu

; ── .trustsig file association ────────────────────────────────────────────────
Root: HKCR; Subkey: ".trustsig"; \
  ValueType: string; ValueName: ""; ValueData: "TrustNet.Signature"; \
  Flags: uninsdeletekey

Root: HKCR; Subkey: "TrustNet.Signature"; \
  ValueType: string; ValueName: ""; ValueData: "TrustNet Signature File"; \
  Flags: uninsdeletekey

Root: HKCR; Subkey: "TrustNet.Signature\DefaultIcon"; \
  ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"

Root: HKCR; Subkey: "TrustNet.Signature\shell\open\command"; \
  ValueType: string; ValueName: ""; \
  ValueData: """{app}\{#AppExe}"" verify ""%1"""

; ── Auto-start node at login ──────────────────────────────────────────────────
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "TrustNetNode"; \
  ValueData: """{app}\{#AppExe}"" node start"; \
  Flags: uninsdeletevalue; Tasks: startnode

[Run]
; Generate keys silently on first install
Filename: "{app}\{#AppExe}"; \
  Parameters: "keygen"; \
  StatusMsg: "Generating your cryptographic keys..."; \
  Flags: runhidden waituntilterminated

; Start the node
Filename: "{app}\{#AppExe}"; \
  Parameters: "node start"; \
  StatusMsg: "Starting TrustNet node..."; \
  Flags: runhidden waituntilterminated nowait; \
  Tasks: startnode

[UninstallRun]
Filename: "{app}\{#AppExe}"; Parameters: "node stop"; Flags: runhidden

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(
    HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    // Notify Windows of registry/association changes
    RegWriteStringValue(HKEY_LOCAL_MACHINE,
      'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
      'TRUSTNET_HOME', ExpandConstant('{app}'));
  end;
end;
