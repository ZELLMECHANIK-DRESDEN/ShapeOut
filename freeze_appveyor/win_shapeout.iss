; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "ShapeOut"
#define MyzmAppName "ᶻᵐShapeOut"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "ZellMechanik Dresden"
#define MyAppURL "http://zellmechanik-dresden.com"
#define MyAppPlatform "win32"
#define MyAppExeName "ShapeOut.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{9607CB56-B737-44CD-ABBC-CAC320CE7C74}
AppName={#MyzmAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename={#MyAppName}_{#MyAppVersion}_{#MyAppPlatform}_setup
Compression=lzma
SolidCompression=yes
ChangesAssociations=yes
PrivilegesRequired=none

[Registry]
Root: HKCR; Subkey: ".zmso"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "{#MyAppName}"; ValueType: string; ValueName: ""; ValueData: "ShapeOut Session"; Flags: uninsdeletekey
Root: HKCR; Subkey: "{#MyAppName}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppName}.EXE,0"
Root: HKCR; Subkey: "{#MyAppName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppName}.EXE"" ""%1""" 


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\projects\shapeout\dist\ShapeOut\ShapeOut.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\shapeout\dist\ShapeOut\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include the entire R installation
Source: "C:\Program Files\R\*"; DestDir: "{app}\R"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyzmAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyzmAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyzmAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
/////////////////////////////////////////////////////////////////////
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;


/////////////////////////////////////////////////////////////////////
function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;


/////////////////////////////////////////////////////////////////////
function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
// Return Values:
// 1 - uninstall string is empty
// 2 - error executing the UnInstallString
// 3 - successfully executed the UnInstallString

  // default return value
  Result := 0;

  // get the uninstall string of the old app
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

/////////////////////////////////////////////////////////////////////
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;
