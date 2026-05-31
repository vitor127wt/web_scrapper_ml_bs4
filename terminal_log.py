import ctypes
import sys
import socket
import time

if len(sys.argv) < 3:
    sys.exit()

titulo_janela = sys.argv[1]
porta_escuta = int(sys.argv[2])

# Define o título do terminal do Windows dinamicamente
ctypes.windll.kernel32.SetConsoleTitleW(titulo_janela)

print(f"=========================================")
print(f" {titulo_janela.upper()} ")
print(f"=========================================\n")

# Configura o servidor de rede UDP para escutar as mensagens enviadas pelo main.py
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', porta_escuta))
sock.settimeout(60)  # Auto-fecha a janela se ficar 1 minuto sem receber nada

try:
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            mensagem = data.decode('utf-8')

            # Se receber o comando especial de fechamento, quebra o loop
            if mensagem == "##FECHAR##":
                break

            print(mensagem)
        except socket.timeout:
            print("\n[AVISO] Tempo limite esgotado sem novas tarefas.")
            break
except KeyboardInterrupt:
    pass
finally:
    sock.close()
    # Mantém visível por 5 segundos antes de fechar a janela do Windows
    time.sleep(5)
