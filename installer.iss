; Script Inno Setup - genere l'installeur Windows "Smart Concrete Predictor Setup.exe"
; Outil gratuit : https://jrsoftware.org/isinfo.php
;
; Usage (sur Windows) :
;   1. pyinstaller build_windows.spec   (produit dist/SmartConcretePredictor/)
;   2. Ouvrir ce fichier dans Inno Setup Compiler puis "Compile"
;      (ou en ligne de commande : ISCC installer.iss)
;   3. Le programme d'installation est genere dans Output/
;
; Ce script est aussi execute automatiquement par le workflow
; .github/workflows/build-windows.yml sur chaque publication de version.

#define MyAppName "Smart Concrete Predictor"
#define MyAppVersion "2.0"
#define MyAppPublisher "Jules DEGNON"
#define MyAppExeName "SmartConcretePredictor.exe"

[Setup]
AppId={{6E9C0E6E-6F1B-4B2E-9C90-SMARTCONCRETE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=SmartConcretePredictor_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "dist\SmartConcretePredictor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent
