@echo off
title Hub de Conversores - Projeto Redenção
echo Iniciando o sistema...
:: Verifica se o Python está no PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado! Por favor, instale o Python 3.10 ou superior.
    pause
    exit
)
python hub_principal.py
pause