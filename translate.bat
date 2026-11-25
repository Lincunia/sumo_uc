@ECHO off
SETLOCAL enabledelayedexpansion

SET current_dir=%CD%
SET file_list=

:: Get the python files
for /f "delims=" %%i in ('DIR /b src\*.py') do (
    ECHO Found file: %%i
    SET "file_list=!file_list! %%i"
)

SET gt_dir "%~1"
::IF NOT EXIST !gt_dir! (
::    ECHO "The !gt_dir! directory does not exist, please set the directory for the gettext bin"
::    EXIT /B 1
::)

echo %current_dir%
echo %gt_dir%
::CALL %gt_dir%\bin\xgettext.exe -d mesages --keyword=gettext_str -o %current_dir%\locale\messages.pot !file_list! --from-code=UTF-8
::CALL %gt_dir%\bin\msginit.exe --input=%current_dir%\locale\messages.pot --%current_dir%\locale=es_ES.UTF8 --output-file=%current_dir%\locale\es\LC_MESSAGES\messages.po --no-translator
::CALL %gt_dir%\bin\msginit.exe --input=%current_dir%\locale\messages.pot --%current_dir%\locale=en_US.UTF8 --output-file=%current_dir%\locale\en\LC_MESSAGES\messages.po --no-translator
::CALL %gt_dir%\bin\msgfmt.exe %current_dir%\locale\es\LC_MESSAGES\messages.po -o %current_dir%\locale\es\LC_MESSAGES\messages.mo
::CALL %gt_dir%\bin\msgfmt.exe %current_dir%\locale\en\LC_MESSAGES\messages.po -o %Ccurrent_dirD%\locale\en\LC_MESSAGES\messages.mo
