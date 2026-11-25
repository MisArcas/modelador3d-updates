# TU3D - Reconstrucción 3D (PowerShell)
# Uso:  powershell -ExecutionPolicy Bypass -File reconstruir.ps1 escaneo.zip [--metodo openmvs] [--calidad alta]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args2)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if (-not $Args2 -or $Args2.Count -eq 0) {
  Write-Host 'Indicá el ZIP de fotos:  .\reconstruir.ps1 escaneo.zip' -ForegroundColor Yellow
  exit 1
}
$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $py = @('py', '-3') }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $py = @('python') }
else { Write-Host 'No se encontró Python. Instalalo desde https://www.python.org/downloads/' -ForegroundColor Red; exit 1 }
$exe = $py[0]; $pre = @(); if ($py.Count -gt 1) { $pre = $py[1..($py.Count - 1)] }
Write-Host 'Instalando/actualizando trimesh (limpieza de malla)...'
& $exe @pre -m pip install --quiet --disable-pip-version-check trimesh numpy scipy networkx
& $exe @pre (Join-Path $PSScriptRoot 'reconstruir.py') @Args2
