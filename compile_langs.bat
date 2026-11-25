@ECHO OFF

:: Set arguments
IF %~1 == "" (
    ECHO "Usage on CMD: translate.bat <path to gnuwin32>"
    EXIT /B 1
)

SET "ArgPath=%~1"
FOR %%I in ("%ArgPath%") DO SET "gt_dir=%%~fI"

IF NOT EXIST !gt_dir! (
    ECHO "The !gt_dir! directory does not exist, please set the directory for the gettext bin"
    EXIT /B 1
)

SET current_dir=%CD%

CALL "%gt_dir%\bin\msgfmt.exe" "%current_dir%\locale\es\LC_MESSAGES\messages.po" ^
    -o "%current_dir%\locale\es\LC_MESSAGES\messages.mo"
CALL "%gt_dir%\bin\msgfmt.exe" "%current_dir%\locale\en\LC_MESSAGES\messages.po" ^
    -o "%current_dir%\locale\en\LC_MESSAGES\messages.mo"