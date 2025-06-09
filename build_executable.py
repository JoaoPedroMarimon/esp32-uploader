# build_executable_fixed.py
import os
import base64
import subprocess
import sys

def embed_firmware_in_script(firmware_path, script_path, output_path):
    """
    Embute o arquivo firmware.bin no script Python
    """
    print(f"Lendo firmware de: {firmware_path}")
    
    # Lê o arquivo firmware
    try:
        with open(firmware_path, 'rb') as f:
            firmware_data = f.read()
    except FileNotFoundError:
        print(f"❌ Arquivo {firmware_path} não encontrado!")
        return False
    
    # Codifica em base64
    firmware_b64 = base64.b64encode(firmware_data).decode('utf-8')
    print(f"Firmware codificado: {len(firmware_b64)} caracteres")
    
    # Lê o script original
    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # Substitui a linha do firmware_data
    new_content = script_content.replace(
        'self.firmware_data = None',
        f'self.firmware_data = """{firmware_b64}"""'
    )
    
    # Salva o script modificado
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Script com firmware embutido salvo em: {output_path}")
    return True

def install_requirements():
    """Instala dependências necessárias"""
    print("Instalando dependências...")
    
    requirements = [
        'pyinstaller',
        'pyserial',
        'esptool'
    ]
    
    for req in requirements:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', req], 
                          check=True, capture_output=True)
            print(f"✅ {req} instalado")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {req}")
            return False
    
    return True

def create_executable_with_esptool(script_path):
    """Cria o executável usando PyInstaller com esptool embutido"""
    print("Criando executável com esptool embutido...")
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # Arquivo único
        '--console',                    # Com console (CLI)
        '--name=ESP32AutoFlasher',      # Nome do executável
        '--hidden-import=esptool',      # Força inclusão do esptool
        '--hidden-import=esptool.cmds', # Submódulos do esptool
        '--hidden-import=esptool.loader',
        '--hidden-import=esptool.util',
        '--hidden-import=serial',
        '--hidden-import=serial.tools.list_ports',
        '--collect-all=esptool',        # Coleta todos os arquivos do esptool
        script_path
    ]
    
    # Adiciona ícone se existir
    if os.path.exists('esp32.ico'):
        cmd.extend(['--icon=esp32.ico'])
    
    try:
        print("Executando PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executável criado com sucesso!")
        print("Saída do PyInstaller:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def test_esptool_import():
    """Testa se esptool pode ser importado"""
    try:
        import esptool
        print("✅ esptool pode ser importado")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar esptool: {e}")
        return False

def main():
    print("🔧 ESP32 Auto Flasher - Build Script CORRIGIDO")
    print("=" * 50)
    
    # Verifica arquivos necessários
    firmware_path = 'firmware.bin'
    script_path = 'esp32_compiler.py'
    
    if not os.path.exists(firmware_path):
        print(f"❌ Arquivo {firmware_path} não encontrado!")
        print("Coloque seu arquivo firmware.bin nesta pasta.")
        return
    
    if not os.path.exists(script_path):
        print(f"❌ Arquivo {script_path} não encontrado!")
        print("Certifique-se de que o script principal está nesta pasta.")
        return
    
    # 1. Instala dependências
    if not install_requirements():
        print("❌ Falha ao instalar dependências")
        return
    
    # 2. Testa import do esptool
    if not test_esptool_import():
        print("❌ esptool não pode ser importado")
        return
    
    # 3. Embute firmware no script
    embedded_script = 'esp32_compiler_embedded.py'
    if not embed_firmware_in_script(firmware_path, script_path, embedded_script):
        return
    
    # 4. Cria executável com esptool embutido
    if create_executable_with_esptool(embedded_script):
        print("\n🎉 BUILD CONCLUÍDO!")
        print("Executável criado em: dist/ESP32AutoFlasher.exe")
        print("\n📋 TESTE RECOMENDADO:")
        print("1. Conecte um ESP32 ao PC")
        print("2. Execute: dist/ESP32AutoFlasher.exe")
        print("3. Verifique se não há mais erro de esptool")
        
        # Limpeza
        try:
            os.remove(embedded_script)
            print("Arquivos temporários removidos.")
        except:
            pass
    else:
        print("❌ Falha ao criar executável")

if __name__ == "__main__":
    main()