@echo off
title PortfolioLens Frontend
cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo Installing frontend packages...
  call npm install
)

call npm run dev
pause
