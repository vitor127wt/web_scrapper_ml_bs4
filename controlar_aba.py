import asyncio
from playwright.sync_api._generated import Page
import random
import time


def pause(min: int | float = 1, max: int | float = 3):
    time.sleep(random.uniform(min, max))


async def scroll_pagina(aba: Page, quantidade: int = 1):
    scroll_pixel = random.randint(300, 800)
    for _ in range(quantidade):
        aba.evaluate(f'window.scrollBy(0, {scroll_pixel})')
        await mover_mouse_random(aba=aba)
        pause(0.3, 0.6)


async def mover_mouse_random(aba: Page):
    aba.mouse.move(random.randint(100, 500), random.randint(100, 500))


def fechar(aba: Page):
    aba.close()


async def carregar_pagina(aba: Page, url: str):
    await aba.goto(url=url, wait_until='networkidle')
