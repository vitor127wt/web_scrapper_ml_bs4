import pandas as pd
from pathlib import Path
from extrair_produtos_paginacao import gerar_lista_produtos

PASTA_EXCEL = Path('relatorios')
PASTA_EXCEL.mkdir(exist_ok=True)


def exportar_xlsx(lista_produtos, nome):
    nome_arquivo = PASTA_EXCEL / f'{nome}.xlsx'
    try:
        df = pd.DataFrame(lista_produtos)
        df.to_excel(nome_arquivo, index=False, engine='openpyxl')
    except Exception as e:
        print(e)
