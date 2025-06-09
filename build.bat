@echo off
chcp 65001 > nul
title ESP32 Auto Flasher Builder

echo.
echo ╔══════════════════════════════════════╗
echo ║        ESP32 Auto Flasher            ║
echo ║         Build Script                 ║
echo ╚══════════════════════════════════════╝
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Instale Python em: https://python.org
    echo Marque a opção "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

:: Verificar se firmware.bin existe
if not exist "firmware.bin" (
    echo.
    echo ❌ Arquivo firmware.bin não encontrado!
    echo.
    echo Coloque seu arquivo firmware.bin nesta pasta.
    echo Este deve ser o arquivo .bin gerado pela compilação do seu código ESP32.
    echo.
    pause
    exit /b 1
)

echo ✅ Firmware encontrado
for %%A in (firmware.bin) do echo    Tamanho: %%~zA bytes

:: Verificar se script principal existe
if not exist "esp32_compiler.py" (
    echo.
    echo ❌ Script esp32_compiler.py não encontrado!
    pause
    exit /b 1
)

echo ✅ Script principal encontrado

:: Perguntar se deseja continuar
echo.
set /p "continuar=Deseja continuar com o build? (S/n): "
if /i "%continuar%"=="n" exit /b 0

echo.
echo 🔧 Iniciando processo de build...
echo.

:: Executar build
python build_executable.py

:: Verificar se deu certo
if exist "dist\ESP32AutoFlasher.exe" (
    echo.
    echo ╔══════════════════════════════════════╗
    echo ║            BUILD SUCESSO!            ║
    echo ╚══════════════════════════════════════╝
    echo.
    echo ✅ Executável criado: dist\ESP32AutoFlasher.exe
    
    :: Mostrar tamanho do arquivo
    for %%A in (dist\ESP32AutoFlasher.exe) do echo    Tamanho: %%~zA bytes
    
    echo.
    echo 📁 Abrir pasta dist?
    set /p "abrir=Digite S para abrir ou Enter para continuar: "
    if /i "%abrir%"=="s" explorer dist
    
) else (
    echo.
    echo ❌ Build falhou!
    echo Verifique os logs acima para detalhes.
)

echo.
echo Pressione qualquer tecla para fechar...
pause >nul