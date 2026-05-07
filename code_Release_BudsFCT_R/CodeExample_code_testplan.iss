; -- CodeExample1.iss --
;
; This script shows various things you can achieve using a [Code] section.

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppName=OSENSTester
AppVersion={#MyAppVersion}
WizardStyle=modern
DisableWelcomePage=no
DefaultDirName=D:\Overlay\
DefaultGroupName=OSENSTester
OutputDir=Output
OutputBaseFilename=SetupBudsFCT_R_Code_{#MyAppVersion}
InfoBeforeFile=CodeReadme.txt
Compression=lzma
SolidCompression=yes

[Dirs]
Name:"D:\vault\StationLog";


[Files]
Source: "Overlay\*"; DestDir: "D:\Overlay"; Flags: recursesubdirs
Source: "BMT\*"; DestDir: "D:\BMT"; Flags: recursesubdirs
Source: "Calibration_Tool\*"; DestDir: "D:\Calibration_Tool"; Flags: recursesubdirs
Source: "OSENSTester\*"; DestDir: "D:\OSENSTester"; Flags: recursesubdirs
; 将整个 site-packages 安装到 C 盘固定路径（供 Python/工具链使用）
Source: "site-packages\*"; DestDir: "C:\Python\Lib\site-packages"; Flags: recursesubdirs
Source: "testerconfig\*"; DestDir: "{%USERPROFILE}\testerconfig"; Flags: recursesubdirs

[Run]


[Icons]
Name: "{userdesktop}\OSENSTester"; Filename: "D:\OSENSTester\OSENSTester.exe"
Name: "{userdesktop}\CalibrationTool"; Filename: "D:\Calibration_Tool\CalibrationTool.exe"

[InstallDelete]
; 在安装前删除旧的文件夹，确保是干净的安装（即“覆盖”而非“合并”）
Type: filesandordirs; Name: "D:\OSENSTester"
Type: filesandordirs; Name: "{%USERPROFILE}\testerconfig"
Type: filesandordirs; Name: "D:\Overlay"
Type: filesandordirs; Name: "D:\BMT"
Type: filesandordirs; Name: "D:\Calibration_Tool"

[Code]
function DeleteExistingShortcut(): Boolean;
var
  ShortcutPath: string;
begin
  Result := False;
  ShortcutPath := ExpandConstant('{userdesktop}\OSENSTester.lnk');
  
  // 检查文件是否存在
  if FileExists(ShortcutPath) then
  begin
    if DeleteFile(ShortcutPath) then
    begin
      Log('已删除旧的桌面快捷方式: ' + ShortcutPath);
      Result := True;
    end
    else
    begin
      Log('删除旧的桌面快捷方式失败: ' + ShortcutPath);
    end;
  end
  else
  begin
    Log('旧的桌面快捷方式不存在: ' + ShortcutPath);
  end;
end;

function InitializeSetup(): Boolean;
begin
  DeleteExistingShortcut();
  Result := True; // 继续安装
end;