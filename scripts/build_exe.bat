@echo off
setlocal
echo ==========================================
echo Gerando Executavel MikroTik Routes
echo ==========================================

:: Mudar para o diretorio raiz do projeto (um nivel acima da pasta scripts)
pushd "%~dp0.."

:: Verificar se o ambiente virtual existe e ativar se necessario
if exist .venv\Scripts\activate.bat (
    echo Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

:: Garantir que as dependencias estao instaladas
echo Verificando dependencias...
pip install -r requirements.txt -q
pip install pyinstaller -q

:: Encerrar o processo se ele estiver rodando (evita erro de permissao negada)
taskkill /f /im MikroTikRoutes.exe 2>nul

:: Remover pastas de build anteriores para evitar conflitos
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo Iniciando processo do PyInstaller...
echo Isso pode levar alguns minutos...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --collect-all customtkinter ^
    --collect-all pystray ^
    --collect-all PIL ^
    --add-data "app/assets;app/assets" ^
    --icon "app/assets/icon.ico" ^
    --name "MikroTikRoutes" ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo SUCESSO!
    echo O executavel foi gerado em: dist\MikroTikRoutes.exe
    echo ==========================================
) else (
    echo.
    echo ########## ERRO NA GERACAO ##########
    echo Verifique as mensagens acima.
)

popd
pause
