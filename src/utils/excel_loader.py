import os
import pandas as pd
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

def encontrar_excel_mais_recente() -> Optional[str]:
    """
    Procura na pasta atual por arquivos Excel no formato 'Informações_Presos_YYYYMMDD_HHMMSS.xlsx'
    e retorna o caminho do arquivo mais recente.
    """
    padrao = re.compile(r'Informações_Presos_(\d{8}_\d{6})\.xlsx')
    arquivos = []
    
    # Lista todos os arquivos no diretório atual
    for arquivo in os.listdir('.'):
        match = padrao.match(arquivo)
        if match:
            data_str = match.group(1)
            try:
                # Converte a string de data para objeto datetime
                data = datetime.strptime(data_str, '%Y%m%d_%H%M%S')
                arquivos.append((arquivo, data))
            except ValueError:
                continue
    
    # Se não encontrou nenhum arquivo, retorna None
    if not arquivos:
        return None
    
    # Retorna o caminho do arquivo mais recente
    arquivo_mais_recente = max(arquivos, key=lambda x: x[1])[0]
    return os.path.join('.', arquivo_mais_recente)

def carregar_dados_excel() -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Carrega os dados do Excel mais recente.
    
    Returns:
        Tuple contendo:
        - Dicionário com DataFrames por unidade
        - DataFrame consolidado
        Se não encontrar arquivo, retorna dicionário vazio e DataFrame vazio
    """
    arquivo = encontrar_excel_mais_recente()
    if not arquivo:
        return {}, pd.DataFrame()
    
    try:
        # Carrega todas as abas do Excel
        excel = pd.read_excel(arquivo, sheet_name=None)
        
        # Separa o DataFrame consolidado
        df_consolidado = excel.get('Consolidado', pd.DataFrame())
        
        # Remove a aba consolidado do dicionário se existir
        if 'Consolidado' in excel:
            del excel['Consolidado']
        
        # Dicionário com DataFrames por unidade
        dfs_unidades = {
            unidade: df.copy() for unidade, df in excel.items()
        }
        
        return dfs_unidades, df_consolidado
    
    except Exception as e:
        print(f"Erro ao carregar Excel: {e}")
        return {}, pd.DataFrame()

def preso_existe_no_excel(codigo: str, df_consolidado: pd.DataFrame) -> bool:
    """
    Verifica se um preso já existe no DataFrame consolidado.
    
    Args:
        codigo: Código do preso
        df_consolidado: DataFrame consolidado
    
    Returns:
        bool: True se o preso existe, False caso contrário
    """
    return codigo in df_consolidado['CÓDIGO'].values if not df_consolidado.empty else False 