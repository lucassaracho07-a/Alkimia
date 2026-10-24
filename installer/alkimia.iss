; Instalador de ALKIMIA POS.
; Compilar con Inno Setup 6:
;   ISCC.exe /DAppVersion=2.0.0 installer\alkimia.iss
;
; La configuración y las credenciales se guardan en %LOCALAPPDATA%\ALKIMIA,
; por lo que se conservan al actualizar o desinstalar.

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif

#define AppName "ALKIMIA POS"
#define AppPublisher "Lucas Saracho"
#define AppExeName "ALKIMIA.exe"

[Setup]
AppId={{1C2BC524-1B53-42E7-9F78-6039F92D2CE5}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\ALKIMIA
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=ALKIMIA-Setup-{#AppVersion}
SetupIconFile=..\assets\alkimia.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AllowNoIcons=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\dist\ALKIMIA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall
