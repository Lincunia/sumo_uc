@ECHO OFF
SETLOCAL enabledelayedexpansion

:: Get the python files
SET file_list=
for /f "delims=" %%i in ('DIR /b src\*.py') do (
    ECHO Found file: %%i
    SET "file_list=!file_list! src\%%i"
)

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

CALL "%gt_dir%\bin\xgettext.exe" ^
    -d mesages ^
    --keyword=gettext_str ^
    -o "%current_dir%\locale\messages.pot" ^
    %file_list% ^
    --from-code=UTF-8

:: We get 'Bad file descriptor', but it creates the .po files
CALL "%gt_dir%\bin\msginit.exe" --input="%current_dir%\locale\messages.pot" ^
    --locale=es_ES.UTF8 ^
    --output-file="%current_dir%\locale\es\LC_MESSAGES\messages.po" ^
    --no-translator
CALL "%gt_dir%\bin\msginit.exe" --input="%current_dir%\locale\messages.pot" ^
    --locale=es_ES.UTF8 ^
    --output-file="%current_dir%\locale\en\LC_MESSAGES\messages.po" ^
    --no-translator
