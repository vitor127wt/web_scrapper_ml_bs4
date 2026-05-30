import asyncio
from bs4 import BeautifulSoup
from playwright.sync_api._generated import Page
import controlar_aba
from bs4._typing import _SomeTags
from bs4._typing import _AtMostOneTag
from bs4.element import PageElement
from playwright._impl._browser_context import Browser
from browser_create import criar_contexto, criar_aba
produtos = []


async def buscar(item: str, browser: Browser, paginas: int = 1):
    aba = await criar_aba(await criar_contexto(browser))
    await controlar_aba.carregar_pagina(aba=aba, url=f'https://lista.mercadolivre.com.br/{item}')
    await controlar_aba.scroll_pagina(aba=aba, quantidade=10)
    for _ in range(paginas):
        raw_html = BeautifulSoup(aba.content(), 'html.parser')
        cards = extrair_cards(raw_html)
        extrair_produtos(cards=cards)


def extrair_produtos(cards):
    global produtos
    card_content = conteudo_card(card)
    for card in cards:
        produto = {
            'imagem': imagem_extrair(card),
            'nome': None,
            'vendedor': None,
            'valor': None,
            'frete_gratis': None,
            'frete_full': None,
            'parcelamento_vezes': None,
            'parcelamento_juros': None,
            'desconto': None,
            'criterio_desconto': None,

        }
        produtos.append(produto)


def extrair_cards(html: BeautifulSoup):
    grid = html.find('ol', class_='ui-search-layout')
    cards = grid.find_all('div', class_='andes-card')
    return cards


def conteudo_card(card: _AtMostOneTag):
    return card.find('div', class_='poly-card__content')

# Extrair informações


def imagem_extrair(card: _AtMostOneTag):
    imagem_element = card.find('img', class_='poly-component_picture')
    return imagem_element.get('src')
