from browser_create import instanciar_browser, path_cookies
from bs4 import BeautifulSoup

path_cookies = r'.\cookies\cookies_ML.json'
item = input()
item = item.replace(' ', '-')
url = f'https://lista.mercadolivre.com.br/{item}'

startup = True
while True:
    if startup:
        navegador = instanciar_browser(headless=False)
        startup = False
    try:

        html = BeautifulSoup(aba.content(), 'html.parser')
        with open('html.html', 'w', encoding='utf-8') as f:
            f.write(html.prettify())
            f.close()

        if 'account-verification' in aba.url:
            print('Redirecionado para Loguin')

        grid = html.find('ol', class_='ui-search-layout')
        with open('html_grid.html', 'w', encoding='utf-8') as f:
            f.write(grid.prettify())
            f.close()

        cards = grid.find_all('div', class_='andes-card')
    except Exception as e:
        print(f'Erro: {e}')
    finally:
        navegador.close()
