@echo off
chcp 65001 >nul
setlocal
title TU3D - Reconstruccion 3D
if "%~1"=="" (
  echo Arrastra el ZIP de fotos ^(o la carpeta^) sobre este archivo.
  echo O ejecuta:  reconstruir.bat escaneo.zip [--metodo openmvs] [--calidad alta]
  pause
  exit /b 1
)
set "PY="
where py >nul 2>nul
if %errorlevel%==0 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ ^(tilda "Add python.exe to PATH"^).
  pause
  exit /b 1
)
echo Instalando/actualizando trimesh (limpieza de malla)...
%PY% -m pip install --quiet --disable-pip-version-check trimesh numpy scipy networkx
%PY% "%~dp0reconstruir.py" %*
echo.
pause
