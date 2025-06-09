# build_executable.py
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

def create_executable(script_path):
    """Cria o executável usando PyInstaller"""
    print("Criando executável...")
    
    cmd = [
        'pyinstaller',
        '--onefile',           # Arquivo único
        '--console',           # COM console (CLI)
        '--name=ESP32AutoFlasher', # Nome do executável
        '--icon=esp32.ico',    # Ícone (opcional)
        '--add-data=*.dll;.',  # Inclui DLLs se necessário
        script_path
    ]
    
    # Remove --icon se não existir o arquivo
    if not os.path.exists('esp32.ico'):
        cmd.remove('--icon=esp32.ico')
        
    # Remove --add-data se não há DLLs
    if not any(f.endswith('.dll') for f in os.listdir('.')):
        cmd = [c for c in cmd if not c.startswith('--add-data')]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executável criado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def main():
    print("🔧 ESP32 Compiler - Build Script")
    print("=" * 40)
    
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
    
    # 2. Embute firmware no script
    embedded_script = 'esp32_compiler_embedded.py'
    if not embed_firmware_in_script(firmware_path, script_path, embedded_script):
        return
    
    # 3. Cria executável
    if create_executable(embedded_script):
        print("\n🎉 BUILD CONCLUÍDO!")
        print("Executável criado em: dist/ESP32AutoFlasher.exe")
        
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