import json

def cookies(filePath: str) -> list:
    with open(filePath, 'r', encoding='utf-8') as f:
        cookies_raw = json.load(f)
        f.close()

    cookies = []

    for cookie in cookies_raw:
        new_cookie = cookie.copy()
        
        valor_sameSite = str(new_cookie['sameSite']).capitalize()
        
        if valor_sameSite in ["Strict", "Lax", "None"]:
            new_cookie['sameSite'] = valor_sameSite
        else:
            del new_cookie['sameSite']
        cookies.append(new_cookie)
    return cookies