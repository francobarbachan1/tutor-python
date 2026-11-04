@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tutor de Python
echo.
echo === Tutor de Python ===
echo.

if not exist "tutor.py" (
  echo Primero descomprimi la carpeta entera y despues abri este archivo desde ahi.
  pause
  exit /b
)

rem 1. Python. Si no esta, se instala solo con winget, que viene con Windows 10 y 11.
python -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo No encontre Python. Lo instalo, puede tardar unos minutos...
  winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
  set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
)
python -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo No pude instalar Python solo. Instalalo desde python.org, tilda Add python.exe to PATH y volve a abrir este archivo.
  pause
  exit /b
)

rem 2. Librerias, solo la primera vez.
if not exist ".instalado" (
  echo Instalando las librerias. La primera vez tarda unos minutos...
  python -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo No se pudieron instalar las librerias. Fijate que haya internet y volve a probar.
    pause
    exit /b
  )
  echo listo> ".instalado"
)

rem 3. Entrenar el detector con las dudas de datos\nuestras_dudas.csv
echo.
python entrenar.py
if errorlevel 1 (
  pause
  exit /b
)

rem 4. Clave de Groq. Nunca se guarda en esta carpeta.
if not "%GROQ_API_KEY%"=="" goto prueba
echo.
set /p GROQ_API_KEY=Pega la clave de Groq y toca Enter. Si no tenes, toca Enter solo:
if "%GROQ_API_KEY%"=="" goto prueba
set "GUARDAR=n"
set /p GUARDAR=Queres guardarla en esta compu para no pegarla la proxima vez? Escribi s o n:
if /i "%GUARDAR%"=="s" setx GROQ_API_KEY "%GROQ_API_KEY%" >nul

:prueba
rem 5. Prueba rapida de la IA y despues el tutor en el navegador.
echo.
python probar_groq.py
echo.
echo Abriendo el tutor en el navegador. Para cerrarlo, cerra esta ventana.
start "" cmd /c "ping -n 7 127.0.0.1 >nul & start http://localhost:8501"
python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
