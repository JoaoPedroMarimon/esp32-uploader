import os
import sys
import subprocess
import serial.tools.list_ports
import tempfile
import base64
import time

class ESP32AutoFlasher:
    def __init__(self):
        # Firmware binário embutido (será preenchido durante o build)
        self.firmware_data = None
        
    def print_header(self):
        """Imprime cabeçalho do programa"""
        print("=" * 60)
        print("           ESP32 AUTO FLASHER")
        print("       Compilação Automática de Firmware")
        print("=" * 60)
        print()
        
    def log(self, message, status="INFO"):
        """Imprime mensagem com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        status_symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌", 
            "WARNING": "⚠️",
            "PROGRESS": "🔄"
        }
        symbol = status_symbols.get(status, "📌")
        print(f"[{timestamp}] {symbol} {message}")
        
    def find_esp32_ports(self):
        """Encontra portas COM com ESP32 conectado"""
        self.log("Procurando dispositivos ESP32...", "PROGRESS")
        
        esp32_ports = []
        all_ports = []
        
        for port in serial.tools.list_ports.comports():
            all_ports.append(f"{port.device} - {port.description}")
            
            # Procura por dispositivos que podem ser ESP32
            esp32_indicators = [
                'cp210', 'ch340', 'ftdi', 'usb-serial', 
                'silicon labs', 'qinheng', 'uart'
            ]
            
            description_lower = port.description.lower()
            if any(indicator in description_lower for indicator in esp32_indicators):
                esp32_ports.append(port.device)
                self.log(f"ESP32 detectado: {port.device} - {port.description}", "SUCCESS")
        
        if not esp32_ports and all_ports:
            # Se não encontrou ESP32 específico, tenta primeira porta disponível
            first_port = all_ports[0].split(" - ")[0]
            esp32_ports.append(first_port)
            self.log(f"Usando porta genérica: {first_port}", "WARNING")
        
        if not esp32_ports:
            self.log("Nenhuma porta COM encontrada!", "ERROR")
            return None
            
        return esp32_ports[0]  # Retorna primeira porta encontrada
        
    def check_esptool(self):
        """Verifica se esptool está disponível"""
        try:
            # Tenta importar esptool como módulo Python
            import esptool
            return True
        except ImportError:
            try:
                # Tenta executar esptool.py como comando
                result = subprocess.run(['esptool.py', '--help'], 
                                      capture_output=True, text=True, timeout=10)
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                try:
                    # Tenta esptool sem .py
                    result = subprocess.run(['esptool', '--help'], 
                                          capture_output=True, text=True, timeout=10)
                    return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    return False
            
    def install_esptool(self):
        """Tenta instalar esptool se estiver rodando como script Python"""
        if getattr(sys, 'frozen', False):
            # Rodando como executável - esptool deve estar embutido
            self.log("ERRO: esptool não está incluído no executável!", "ERROR")
            self.log("O executável precisa ser recompilado com esptool incluído.", "ERROR")
            return False
        else:
            # Rodando como script Python - pode instalar
            self.log("esptool não encontrado. Instalando...", "PROGRESS")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'esptool'], 
                              check=True, capture_output=True, timeout=60)
                self.log("esptool instalado com sucesso!", "SUCCESS")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                self.log(f"Erro ao instalar esptool: {e}", "ERROR")
                return False
            
    def extract_firmware(self):
        """Extrai o firmware embutido para um arquivo temporário"""
        if not self.firmware_data:
            # Procura por firmware.bin na pasta atual
            local_firmware = "firmware.bin"
            if os.path.exists(local_firmware):
                self.log(f"Usando firmware local: {local_firmware}", "INFO")
                return local_firmware
            else:
                self.log("Firmware não encontrado (nem embutido nem local)!", "ERROR")
                return None
        
        # Decodifica o firmware de base64
        try:
            self.log("Extraindo firmware embutido...", "PROGRESS")
            firmware_bytes = base64.b64decode(self.firmware_data)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
            temp_file.write(firmware_bytes)
            temp_file.close()
            
            self.log(f"Firmware extraído: {len(firmware_bytes)} bytes", "SUCCESS")
            return temp_file.name
        except Exception as e:
            self.log(f"Erro ao extrair firmware: {e}", "ERROR")
            return None
            
    def flash_esp32(self, port, firmware_path):
        """Faz o upload do firmware para o ESP32"""
        try:
            # Tenta usar esptool como módulo Python primeiro
            try:
                import esptool
                use_module = True
                self.log("Usando esptool como módulo Python", "INFO")
            except ImportError:
                use_module = False
                self.log("Usando esptool como comando externo", "INFO")
            
            # 1. Apaga a flash do ESP32
            self.log(f"Apagando flash do ESP32 na porta {port}...", "PROGRESS")
            
            if use_module:
                # Usar esptool como módulo
                import esptool
                erase_args = ['--port', port, 'erase_flash']
                esptool.main(erase_args)
            else:
                # Usar como comando externo
                erase_cmd = ['esptool.py', '--port', port, 'erase_flash']
                result = subprocess.run(erase_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    # Tenta sem .py
                    erase_cmd = ['esptool', '--port', port, 'erase_flash']
                    result = subprocess.run(erase_cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        self.log(f"Erro ao apagar flash: {result.stderr}", "ERROR")
                        return False
                
            self.log("Flash apagada com sucesso!", "SUCCESS")
            
            # 2. Faz upload do firmware
            self.log("Enviando firmware para ESP32...", "PROGRESS")
            
            if use_module:
                # Usar esptool como módulo
                upload_args = ['--port', port, '--baud', '460800', 
                             'write_flash', '--flash_size=detect', '0x0', firmware_path]
                try:
                    esptool.main(upload_args)
                    self.log("FIRMWARE ENVIADO COM SUCESSO!", "SUCCESS")
                    return True
                except SystemExit as e:
                    if e.code == 0:
                        self.log("FIRMWARE ENVIADO COM SUCESSO!", "SUCCESS")
                        return True
                    else:
                        # Tenta com baudrate menor
                        self.log("Tentando com baudrate menor...", "WARNING")
                        upload_args[3] = '115200'
                        try:
                            esptool.main(upload_args)
                            self.log("FIRMWARE ENVIADO COM SUCESSO (baudrate baixo)!", "SUCCESS")
                            return True
                        except SystemExit as e2:
                            if e2.code == 0:
                                self.log("FIRMWARE ENVIADO COM SUCESSO (baudrate baixo)!", "SUCCESS")
                                return True
                            else:
                                self.log(f"Erro no upload: código {e2.code}", "ERROR")
                                return False
            else:
                # Usar como comando externo
                upload_cmd = [
                    'esptool.py', '--port', port, '--baud', '460800',
                    'write_flash', '--flash_size=detect', '0x0', firmware_path
                ]
                
                result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    self.log("FIRMWARE ENVIADO COM SUCESSO!", "SUCCESS")
                    return True
                else:
                    # Tenta esptool sem .py
                    upload_cmd[0] = 'esptool'
                    result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        self.log("FIRMWARE ENVIADO COM SUCESSO!", "SUCCESS")
                        return True
                    else:
                        # Tenta com baudrate menor
                        self.log("Tentando com baudrate menor...", "WARNING")
                        upload_cmd[4] = '115200'
                        
                        result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=90)
                        
                        if result.returncode == 0:
                            self.log("FIRMWARE ENVIADO COM SUCESSO (baudrate baixo)!", "SUCCESS")
                            return True
                        else:
                            self.log(f"Erro no upload: {result.stderr}", "ERROR")
                            return False
                
        except subprocess.TimeoutExpired:
            self.log("Timeout - Operação demorou muito tempo", "ERROR")
            self.log("Verifique a conexão com o ESP32", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"Erro inesperado: {e}", "ERROR")
            return False
            
    def cleanup_temp_files(self, filepath):
        """Remove arquivos temporários"""
        try:
            if filepath and os.path.exists(filepath) and 'temp' in filepath:
                os.unlink(filepath)
                self.log("Arquivos temporários removidos", "INFO")
        except Exception:
            pass
            
    def run(self):
        """Execução principal do programa"""
        self.print_header()
        
        # 1. Verificar porta
        port = self.find_esp32_ports()
        if not port:
            self.log("FALHA: Nenhum dispositivo ESP32 encontrado!", "ERROR")
            self.log("Certifique-se de que:", "INFO")
            self.log("- ESP32 está conectado via USB", "INFO")
            self.log("- Drivers estão instalados", "INFO")
            self.log("- Cabo USB funciona para dados", "INFO")
            return False
            
        # 2. Verificar esptool
        if not self.check_esptool():
            if not self.install_esptool():
                self.log("FALHA: Não foi possível instalar esptool!", "ERROR")
                return False
                
        # 3. Extrair firmware
        firmware_path = self.extract_firmware()
        if not firmware_path:
            self.log("FALHA: Firmware não encontrado!", "ERROR")
            return False
            
        # 4. Flash ESP32
        success = self.flash_esp32(port, firmware_path)
        
        # 5. Limpeza
        self.cleanup_temp_files(firmware_path)
        
        # 6. Resultado final
        print()
        if success:
            print("🎉" * 20)
            self.log("PROCESSO CONCLUÍDO COM SUCESSO!", "SUCCESS")
            self.log("ESP32 programado e pronto para uso!", "SUCCESS")
            print("🎉" * 20)
        else:
            print("💥" * 20)
            self.log("PROCESSO FALHOU!", "ERROR")
            self.log("Verifique os erros acima e tente novamente", "ERROR")
            print("💥" * 20)
            
        return success

def main():
    # Verifica se está rodando como executável ou script
    if getattr(sys, 'frozen', False):
        # Rodando como executável
        app_path = os.path.dirname(sys.executable)
    else:
        # Rodando como script Python
        app_path = os.path.dirname(os.path.abspath(__file__))
    
    # Muda para o diretório do executável
    os.chdir(app_path)
    
    # Cria e executa o flasher
    flasher = ESP32AutoFlasher()
    success = flasher.run()
    
    # Pausa para ver resultado (apenas em Windows)
    if os.name == 'nt':  # Windows
        print()
        input("Pressione Enter para fechar...")
    
    # Código de saída
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()