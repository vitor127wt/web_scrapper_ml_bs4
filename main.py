import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import subprocess
import sys
import time
import random
import socket
from pathlib import Path
import requests
from extrair_produtos_paginacao import extrair_link_proxima_pagina, gerar_lista_produtos
from exportar_xlsx import exportar_xlsx
from capturar_cookies import cookies

LIMITE_TASKS = 3
MAX_THREADS = 3
CONCORRENCIA_GLOBAL = 4
fila_busca = queue.Queue()
lock_sys = threading.Lock()

threads_ativas = 0
total_threads_criadas = 0

buscas_ativas_global = 0

PASTA_COOKIES = Path('cookies')
PASTA_TOKENS = Path('tokens_controle')
PASTA_TOKENS.mkdir(exist_ok=True)

for token_velho in PASTA_TOKENS.glob('*.txt'):
    try:
        token_velho.unlink()
    except:
        pass


def abrir_terminal(titulo, porta_log):
    # Abri um novo terminal de log
    subprocess.Popen([sys.executable, 'terminal_log.py', titulo, str(
        porta_log)], creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', porta_log))
        return sock
    except:
        return None


def log(conexao, mensagem: str):
    # Envia uma str atravez de uma porta UDP para o terminal alvo
    if conexao:
        mensagem = f'{mensagem}\n'
        conexao.sendall(mensagem.encode('utf-8'))


def alocar_porta_livre():
    # Aloca uma porta UDP livre no sistema
    sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    porta = sock.getsockname()[1]
    sock.close()
    return porta


def nova_task(session: requests.Session, item_inicial, nome_task, porta_thread, paginas=1):
    porta_task_tcp = alocar_porta_livre()
    socket_janela = abrir_terminal(
        f'Terminal de busca: {nome_task}', porta_task_tcp)

    global buscas_ativas_global
    erro = False
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=0, i",
        "sec-ch-ua": r"\"Chromium\";v=\"148\", \"Google Chrome\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
        "sec-ch-ua-platform": r"\"Windows\"",
        "sec-ch-ua-platform-version": r"\"19.0.0\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }
    time.sleep(0.3)
    url_atual = f'https://lista.mercadolivre.com.br/{item_inicial}'
    pagina_atual = 1
    if paginas > 5:
        paginas = 5
    produtos_final = []
    log(socket_janela, f'Iniciando tentativa de busca de {item_inicial}')
    while url_atual and pagina_atual <= paginas:
        try:
            resposta = session.get(url_atual, headers=headers, timeout=15)
            if resposta.status_code == 200:
                log(socket_janela,
                    f'[STATUS CODE]: {resposta.status_code} \n Iniciando raspagem da pagina {pagina_atual}.')
                html = resposta.text
                try:
                    produtos_tmp = gerar_lista_produtos(html=html)
                except Exception as e:
                    erro = True
                    log(socket_janela, e)

                for produto in produtos_tmp:
                    produtos_final.append(produto)
                url_atual = extrair_link_proxima_pagina(html=html)
                pagina_atual += 1
                time.sleep(random.uniform(2, 4))
            else:
                log(socket_janela, f'BLOQUEIO: {resposta.status_code}')
                url_atual = None
        except Exception as e:
            log(socket_janela, e)
            url_atual = None
    if produtos_final:
        log(socket_janela, 'Exportando para XLSX')
        exportar_xlsx(produtos_final, nome=f'{item_inicial[0]}')
        log(socket_janela,
            f'Exportado com sucesso, arquivo: {item_inicial}.xlsx criado.')
    if not erro:
        log(porta_thread, f'Task: {nome_task} concluida')
        time.sleep(5)
        socket_janela.close()


def main_thread_loop(nome_thread, item_inicial):
    porta_thread_tcp = alocar_porta_livre()
    socket_janela = abrir_terminal(
        f'TERMINAL: {nome_thread}', porta_thread_tcp)
    global threads_ativas, buscas_ativas_global

    time.sleep(0.4)
    log(socket_janela, f'{nome_thread} INICIADA')
    with requests.Session() as session:
        log(socket_janela, 'Nova sessão iniciada')
        cookies_path = PASTA_COOKIES / 'lista.mercadolivre.com.br_cookies.json'
        cookies_raw = cookies(cookies_path)
        for cookie in cookies_raw:
            name = cookie.get('name')
            value = cookie.get('value')
            if name and value:
                domain = cookie.get('domain')
                path = cookie.get('path')
                session.cookies.set(name, value, domain=domain, path=path)
        log(socket_janela, 'Cookies Injetados com Sucesso')
        with ThreadPoolExecutor(max_workers=4) as executor:
            task_count = 0
            proximo_item = item_inicial[0]
            tasks_ativas = []
            while proximo_item is not None or len(tasks_ativas) > 0:
                tasks_ativas = [f for f in tasks_ativas if not f.done()]
                if proximo_item is None:
                    try:
                        proximo_item = fila_busca.get_nowait()
                    except queue.Empty:
                        proximo_item = None
                while proximo_item is not None and len(tasks_ativas) < 4:

                    task_count += 1
                    nome_task = f'task-{task_count}-{nome_thread}'
                    with lock_sys:
                        buscas_ativas_global += 1
                        if buscas_ativas_global >= CONCORRENCIA_GLOBAL and threads_ativas < MAX_THREADS and not fila_busca.empty():
                            checar_e_iniciar_thread()
                    log(socket_janela, f'Iniciando: {nome_task}')
                    try:
                        f = executor.submit(
                            nova_task, session, proximo_item, nome_task, socket_janela, item_inicial[1])
                        tasks_ativas.append(f)
                    except RuntimeError as e:
                        log(socket_janela,
                            f'[AVISO] Abortando agendamento do item {proximo_item}. Interpretador em desligamento')
                        log(socket_janela, e)
                        proximo_item = None
                        break
                    fila_busca.task_done()
                    try:
                        proximo_item = fila_busca.get_nowait()
                    except queue.Empty:
                        proximo_item = None
                time.sleep(0.3)

    log(socket_janela, 'Tarefas concluidas, encerrando Thread')
    with lock_sys:
        threads_ativas -= 1
    log(socket_janela, 'Thread encerrada')
    time.sleep(5)
    socket_janela.close()


def checar_e_iniciar_thread():
    global threads_ativas, total_threads_criadas
    if not fila_busca.empty() and threads_ativas < MAX_THREADS:
        threads_ativas += 1
        total_threads_criadas += 1

        item_inicial = fila_busca.get()

        t = threading.Thread(
            target=main_thread_loop,
            args=(f'Thread-{total_threads_criadas}', item_inicial),
            name=f'Thread-{total_threads_criadas}'
        )
        t.start()

        print(f'[SYS] Distribuição de carga. {t.name} Iniciada')


if __name__ == '__main__':
    while True:
        item = input('Digite um item para busca: ')
        if item.lower() in ['sair', 'exit', 'close', 'fechar']:
            break
        while True:
            paginas = input('Quantas paginas deseja buscar ?: ')
            if paginas.isdigit():
                break
            else:
                print('Por favor, digite somente numeros')

        if item:
            item_formatado = item.replace(' ', '-')

            busca = (item_formatado, int(paginas))

            fila_busca.put(busca)
            print(f'Item {item_formatado} inserido na fila')

            with lock_sys:
                if threads_ativas == 0:
                    checar_e_iniciar_thread()
