@ECHO OFF
REM

SET current_dir=%CD%
SET venv_dir=%current_dir%\env

IF NOT EXIST %venv_dir% (
    ECHO "Creating python environment..."
    python -m venv env
)

ECHO "Activating environment..."
CD %venv_dir%
CALL %venv_dir%\Scripts\activate.bat

ECHO "Installing dependencies..."
pip install -r %current_dir%\requirements.txt

ECHO "Running program..."
python %current_dir%\sumo_uc.py

ECHO "Deactivaing environment..."
CALL %venv_dir%\Scripts\deactivate.bat

CD %current_dir%
EXIT /B 1