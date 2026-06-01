import json
import re
from pathlib import Path
from bs4 import BeautifulSoup


def extrair_link_proxima_pagina(html: str):
    json_limpo_raw = extrair_json_limpo(html=html)
    json_dict = json.loads(json_limpo_raw)
    try:
        link = json_dict['appProps']['sharedState']['search']['pagination']['next_page']['url']
    except Exception as e:
        print(e)
    return link


def gerar_lista_produtos(html: str):

    json_limpo_raw = extrair_json_limpo(html=html)
    produtos_dict_raw = gerar_dicionario_de_produtos(json_limpo_raw)
    urls_imagens = extrair_links_imagens(json_limpo_raw)
    produtos_dict_limpos = gerar_produtos_limpos(
        produtos_dict_raw, urls_imagens)
    return produtos_dict_limpos


def extrair_json_limpo(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    script_tag = soup.find(
        'script', id='__NORDIC_RENDERING_CTX__')
    if script_tag is None:
        raise TypeError('script_tag é None')
    conteudo_script_string = script_tag.string

    match = re.search(r'_n\.ctx\.r\s*=\s*({)', conteudo_script_string)

    if not match:
        print('Match nao achou nada')
        return None

    inicio_json = match.start(1)
    contador_chaves = 0
    posicao_final = 0

    for i in range(inicio_json, len(conteudo_script_string)):
        char = conteudo_script_string[i]
        if char == r'{':
            contador_chaves += 1
        elif char == r'}':
            contador_chaves -= 1
        if contador_chaves == 0:
            posicao_final = i + 1
            break

    if posicao_final > inicio_json:
        return conteudo_script_string[inicio_json:posicao_final]
    else:
        return None


def gerar_dicionario_de_produtos(json_limpo_str: str) -> dict:

    json_dict = json.loads(json_limpo_str)
    resultados = json_dict['appProps']['sharedState']['search']['results']
    produtos_list = []

    for index, card in enumerate(resultados):
        produto_tmp = {}
        if card.get('polycard'):
            produto_tmp['id'] = card.get('polycard').get('metadata').get('id')
            componente = card.get('polycard').get('components')

            for item in componente:
                produto_tmp[f'{item['type']}'] = item
            produtos_list.append(produto_tmp)
    return produtos_list


def extrair_links_imagens(json_limpo_str: str) -> dict:
    imagens_links = {}
    json_dict = json.loads(json_limpo_str)
    lista_produtos = json_dict['appProps']['pageProps']['initialState']['seo']['schema']['product_list']
    for i, item in enumerate(lista_produtos):
        imagens_links[f'{i}-produto'] = {
            'id_dados': item.get('id'),
            'name': item.get('name'),
            'url': item.get('item_offered').get('url'),
            'image': item.get('image')
        }
    return imagens_links


def gerar_produtos_limpos(produtos_raw: list, urls_imagens_raw: dict) -> dict:
    produtos = []
    for item in urls_imagens_raw:
        produtos.append({
            'id': urls_imagens_raw[item].get('id_dados'),
            'name': None,
            'url': urls_imagens_raw[item].get('url'),
            'image': urls_imagens_raw[item].get('image'),
            'valor': None,
            'desconto': None,
            'desconto_condition': None,
            'parcelamento': None,
            'sem_juros': None,
            'frete': None,
            'full': None,
            'internacional': None
        })
    for item in produtos:
        item['name'] = pegar_name(produtos_raw, id=item['id'])
        item['valor'] = pegar_valor(produtos_raw, id=item['id'])
        item['desconto'] = pegar_desconto(produtos_raw, id=item['id'])
        item['desconto_condition'] = pegar_desconto_condition(
            produtos_raw, id=item['id'])
        item['parcelamento'] = pegar_parcelamento(produtos_raw, id=item['id'])
        item['sem_juros'] = pegar_juros(produtos_raw, id=item['id'])
        item['frete'] = pegar_frete(produtos_raw, id=item['id'])
        item['full'] = pegar_full(produtos_raw, id=item['id'])
        item['internacional'] = pegar_internacional(
            produtos_raw, id=item['id'])
    return produtos


def checar_id(id_1: str, id_2):
    if id_1 == id_2:
        return True
    return False


def pegar_name(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            return item['title']['title']['text']
    return None


def pegar_valor(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            return item['price']['price']['current_price']['value']
    return None


def pegar_desconto(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                desconto_raw = item['price']['price']['discount_label']['text']
                desconto_limpo = ''
                for c in desconto_raw:
                    if c.isdigit():
                        desconto_limpo += c
                return desconto_limpo
            except:
                return None
    return None


def pegar_desconto_condition(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                id.isalpha
                desconto_raw = item['price']['price']['discount_label']['text']
                desconto_condition_limpo = ''
                for c in desconto_raw:
                    if c.isalpha() and c != '%':
                        desconto_condition_limpo += c
                return desconto_condition_limpo.strip()
            except:
                return None
    return None


def pegar_parcelamento(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                parcelamento_raw = item['price']['price']['installments']['text']
                parcelamento_limpo = ''
                for c in parcelamento_raw:
                    if c.isdigit():
                        parcelamento_limpo += c
                if parcelamento_limpo.isdigit():
                    return int(parcelamento_limpo)
                return parcelamento_limpo
            except:
                return 0
    return 0


def pegar_juros(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                juros = item['price']['price']['installments']['no_interest']
                return juros
            except:
                return False
    return False


def pegar_frete(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                frete = item['shipping_v2']['shipping_v2'][0]['values'][0]['pill']['text']
                return frete
            except:
                return False
    return False


def pegar_full(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                full = item['shipping_v2']['shipping_v2'][0]['values'][1]['icon']['alt_text']

                return full
            except:
                return False
    return False


def pegar_internacional(produtos_raw: list, id: str):
    for item in produtos_raw:
        if checar_id(item['id'], id):
            try:
                internacional = item['cbt']['cbt']['alt_text']
                if internacional:
                    return True
            except:
                return False
    return False


# caminho = Path(__file__).resolve().parent / 'testes'

# html_f = caminho / 'html.html'

# json_f = caminho / 'teste.json'
# json_f_links = caminho / 'teste_links.json'


# with open(html_f, 'r', encoding='utf-8') as f:
#     html = f.read()

# lista = gerar_lista_produtos(html)
# lista_links = extrair_links_paginas(html)

# with open(json_f, 'w', encoding='utf-8') as j:
#     json.dump(lista, j, ensure_ascii=False)
# with open(json_f_links, 'w', encoding='utf-8') as j:
#     json.dump(lista_links, j, ensure_ascii=False)
