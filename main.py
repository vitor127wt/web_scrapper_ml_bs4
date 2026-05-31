from browser_create import path_cookies
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import threading
import queue
import subprocess
import sys
import time
import random
import socket
import asyncio
import browser_create
from buscar_produtos import buscar
LIMITE_TASKS = 3
MAX_THREADS = 3
CONCORRENCIA_GLOBAL = 4
fila_busca = queue.Queue()
lock_sys = threading.Lock()

threads_ativas = 0
total_threads_criadas = 0

buscas_ativas_global = 0


def abrir_terminal(titulo, porta_log):
    # Abri um novo terminal de log
    return subprocess.Popen([sys.executable, 'terminal_log.py', titulo, str(porta_log)],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)


def print_log(porta, mensagem):
    # Envia uma str atravez de uma porta UDP para o terminal alvo
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(mensagem.encode('utf-8'), ('127.0.0.1', porta))
    except:
        pass


def alocar_porta_livre():
    # Aloca uma porta UDP livre no sistema
    sock = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 0))
    porta = sock.getsockname()[1]
    sock.close()
    return porta


async def nova_task(browser, item, nome_task, porta_thread):
    global buscas_ativas_global

    porta_task = alocar_porta_livre()
    abrir_terminal(f'Terminal de busca: {nome_task}', porta_task)
    await asyncio.sleep(0.4)

    contexto = await browser_create.criar_contexto(browser)

    aba = await browser_create.criar_aba(contexto)

    produtos = await buscar(item=item, aba=aba)

    print_log(porta_task, '##FECHAR##')


async def main_thread_loop(nome_thread, item_inicial):
    global threads_ativas, buscas_ativas_global
    porta_thread = alocar_porta_livre()
    abrir_terminal(f'TERMINAL: {nome_thread}', porta_thread)
    await asyncio.sleep(0.5)

    print_log(porta_thread, f'{nome_thread} INICIADA')

    # navegador = browser_create.instanciar_browser()

    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=True)

        tarefas_ativas = set()

        task_count = 0

        proximo_item = item_inicial

        while proximo_item is not None or tarefas_ativas:

            while proximo_item is not None and len(tarefas_ativas) < LIMITE_TASKS:
                task_count += 1
                nome_task = f'Task-{task_count} da {nome_thread}'

                with lock_sys:
                    buscas_ativas_global += 1
                    if buscas_ativas_global >= CONCORRENCIA_GLOBAL and threads_ativas < MAX_THREADS and not fila_busca.empty():
                        checar_e_iniciar_thread()

                print_log(porta_thread, f'Iniciando em paralelo: {nome_task}')

                t = asyncio.create_task(
                    nova_task(navegador, proximo_item, nome_task, porta_thread))
                tarefas_ativas.add(t)

                t.add_done_callback(lambda task: tarefas_ativas.remove(task))
                t.add_done_callback(lambda task: fila_busca.task_done())

                try:
                    proximo_item = fila_busca.get_nowait()
                except queue.Empty:
                    proximo_item = None

            await asyncio.sleep(0.5)

            if proximo_item is None and tarefas_ativas:
                await asyncio.gather(*tarefas_ativas, return_exceptions=True)

        print_log(porta_thread, 'Tarefas concluidas, encerrando Thread')
        print_log(porta_thread, '##FECHAR##')
        await navegador.close()

    with lock_sys:
        threads_ativas -= 1
    print_log(porta_thread, 'Thread encerrada')


def disparar_thread(nome_thread, item_inicial):
    asyncio.run(main_thread_loop(nome_thread, item_inicial))


def checar_e_iniciar_thread():
    global threads_ativas, total_threads_criadas
    if not fila_busca.empty() and threads_ativas < MAX_THREADS:
        threads_ativas += 1
        total_threads_criadas += 1

        item_inicial = fila_busca.get()

        t = threading.Thread(
            target=disparar_thread,
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
        if item:
            item_formatado = item.replace(' ', '-')

            fila_busca.put(item_formatado)
            print(f'Item {item_formatado} inserido na fila')

            with lock_sys:
                if threads_ativas == 0:
                    checar_e_iniciar_thread()
