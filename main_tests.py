import requests
import json
from bs4 import BeautifulSoup


with open(r'.\cookies\lista.mercadolivre.com.br_cookies.json', 'r', encoding='utf-8') as f:
    cookies_json = json.load(f)

jar = requests.utils.cookiejar_from_dict({})

for c in cookies_json:
    jar.set(
        name=c.get('name'),
        value=c.get('value'),
        domain=c.get('domain'),
        path=c.get('path'),
    )

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0'
}
request = requests.get(
    'https://lista.mercadolivre.com.br/fone-de-ouvido',
    cookies=jar,
    headers=headers)

soup = BeautifulSoup(request.text, 'html.parser')

html_formatado = soup.prettify()

with open('html.html', 'w', encoding='utf-8') as f:
    f.write(html_formatado)
