@echo off
title Automatizador SEPE
echo ==========================================
echo INICIANDO AUTOMATIZADOR DE RELATORIOS...
echo ==========================================
echo.

:: Verifica se python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python antes de executar este programa.
    echo.
    pause
    exit
)

:: Executa o programa principal
python main_app.py

:: Se o programa fechar por erro, pausa para leitura
if %errorlevel% neq 0 (
    echo.
    echo [ATENCAO] O programa fechou com erro. Veja a mensagem acima.
    pause
)