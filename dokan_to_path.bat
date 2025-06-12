@echo off
setlocal enabledelayedexpansion

:: Obter o diretorio atual do script
set "SCRIPT_DIR=%~dp0"
:: Remover a barra final
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Caminhos que precisam ser adicionados ao PATH
set "DRIVER_PATH=%SCRIPT_DIR%\driver"
set "LIB_PATH=%SCRIPT_DIR%\lib"

:: Verificar se os caminhos ja existem no PATH
echo Verificando PATH do sistema...

:: Verificar DRIVER_PATH
echo %PATH% | findstr /C:"%DRIVER_PATH%" >nul
if errorlevel 1 (
    echo Adicionando %DRIVER_PATH% ao PATH
    setx PATH "%PATH%;%DRIVER_PATH%" /M
) else (
    echo %DRIVER_PATH% ja esta no PATH
)

:: Verificar LIB_PATH
echo %PATH% | findstr /C:"%LIB_PATH%" >nul
if errorlevel 1 (
    echo Adicionando %LIB_PATH% ao PATH
    setx PATH "%PATH%;%LIB_PATH%" /M
) else (
    echo %LIB_PATH% ja esta no PATH
)

:: Verificar se o servico Dokan esta instalado e iniciado
sc query dokan2 >nul 2>&1
if errorlevel 1 (
    echo O servico Dokan2 nao esta instalado. Tentando instalar...
    sc create dokan2 binPath= "%DRIVER_PATH%\dokan2.sys" type= kernel start= auto
    if errorlevel 1 (
        echo Falha ao criar o servico Dokan2. Execute este script como administrador.
    ) else (
        echo Servico Dokan2 criado com sucesso.
        sc start dokan2
        if errorlevel 1 (
            echo Falha ao iniciar o servico Dokan2.
        ) else (
            echo Servico Dokan2 iniciado com sucesso.
        )
    )
) else (
    echo Servico Dokan2 ja esta instalado.
    sc query dokan2 | findstr /C:"RUNNING" >nul
    if errorlevel 1 (
        echo Iniciando o servico Dokan2...
        sc start dokan2
    ) else (
        echo Servico Dokan2 ja esta em execucao.
    )
)

echo Configuracao concluida.
exit /b 0