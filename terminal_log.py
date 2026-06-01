import ctypes
import sys
import socket
import time

if len(sys.argv) < 3:
    print('Erro: Argumentos de inicialização insuficientes')
    time.sleep(5)
    sys.exit()

titulo_janela = sys.argv[1]
porta_escuta = int(sys.argv[2])

try:
    # Define o título do terminal do Windows dinamicamente
    ctypes.windll.kernel32.SetConsoleTitleW(titulo_janela)
    kernel32 = ctypes.windll.kernel32
    h_input = kernel32.GetStdHandle(-10)
    modo_atual = ctypes.c_ulong()
    kernel32.GetConsoleMode(h_input, ctypes.byref(modo_atual))
    kernel32.SetConsoleMode(h_input, modo_atual.value & ~0x0040)
except Exception as e:
    print(e)
    pass

print(f"=========================================")
print(f" {titulo_janela.upper()} ")
print(f"=========================================\n")

# Configura o servidor de rede UDP para escutar as mensagens enviadas pelo main.py
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(('127.0.0.1', porta_escuta))
    sock.listen(1)
    # Auto-fecha a janela se ficar 1 minuto sem receber nada
    # sock.settimeout(60)
except Exception as e:
    print(f'Error: nao foi possivel abrir a porta {porta_escuta}. {e}')
    time.sleep(5)
    sys.exit()

try:
    conexao, endereco = sock.accept()
    buffer = ''
    while True:
        dados = conexao.recv(8192)
        if not dados:
            print('\n[SISTEMA] Conexão encerrada pelo processo principal')
            break
        buffer += dados.decode('utf-8', errors='ignore')

        while '\n' in buffer:
            linha, buffer = buffer.split('\n', 1)
            print(linha)
except KeyboardInterrupt:
    pass
except Exception as e:
    print(e)
finally:
    sock.close()
    print('\nEncerrando terminal em 5 segundos')
    time.sleep(5)
