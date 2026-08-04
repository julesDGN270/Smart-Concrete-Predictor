; ============================================================
; Script Inno Setup - Smart Concrete Predictor
; Construit un vrai installeur Windows (.exe d'installation) a
; partir de dist\SmartConcretePredictor.exe (deja construit par
; build_windows.bat).
;
; A compiler avec Inno Setup (gratuit) :
;   https://jrsoftware.org/isdl.php
; Une fois installe, ouvre ce fichier .iss avec "Inno Setup
; Compiler" et clique sur "Compile" (ou touche F9).
; ============================================================

#define MyAppName "Smart Concrete Predictor"
#define MyAppVersion "2.0"
#define MyAppPublisher "Jules DEGNON"
#define MyAppExeName "SmartConcretePredictor.exe"

[Setup]
AppId={{8E4A2F1A-3B7C-4D2E-9F1A-SCP2026DEGNON}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=SmartConcretePredictor_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
; Pas besoin d'admin si installe pour l'utilisateur courant seulement :
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis supplementaires:"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent
