
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from capturar_cookies import cookies


path_cookies = None
cookies_list = cookies(path_cookies)


def criar_navegador():
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)

        contexto = navegador.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        contexto.add_cookies(cookies=cookies_list)
        return contexto


def criar_aba(contexto: function):
    aba = contexto.new_page()
    stealth = Stealth()
    stealth.apply_stealth_sync(aba)
    aba.add_init_script("""
        # 1. Remove completamente o rastro de automação do webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        # 2. Simula uma quantidade real de núcleos de processador (bots mostram 0 ou param)
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

        # 3. Mascara os plugins do Chrome (navegadores de automação vêm vazios)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
                { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }
            ]
        });

        # 4. Força uma placa de vídeo residencial falsa para o teste de WebGL do site
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.'; // UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return 'Intel(R) UHD Graphics'; // UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, arguments);
        };
    """)
    return aba
