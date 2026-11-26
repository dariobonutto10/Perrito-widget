@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando dependencias (solo la primera vez)...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo No se pudo instalar. Revisa que Python este instalado y agregado al PATH.
  pause
  exit /b 1
)
echo Iniciando perrito... (cierra esta ventana o usa el icono de la bandeja para salir)
python perrito_widget.py
if errorlevel 1 pause
