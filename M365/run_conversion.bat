@echo off
REM Check if the environment exists
CALL "C:/Users/Kschellinger/AppData/Local/anaconda3/Scripts/conda.exe" env list | findstr RDRenv
IF ERRORLEVEL 1 (
    REM Create the environment from environment.txt if it doesn't exist
    CALL "C:/Users/Kschellinger/AppData/Local/anaconda3/Scripts/conda.exe" create --name RDRenv --file "C:/Users/kschellinger/AppData/Local/anaconda3/environment.txt"
)

REM Activate the Conda environment
CALL "C:/Users/Kschellinger/AppData/Local/anaconda3/Scripts/activate.bat" RDRenv

REM Run the Python script
python "j:/TAZ_Adustment/sjtdm-modern/M365/ConversionV1.py"
