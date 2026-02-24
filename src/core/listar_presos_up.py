from src.utils import config
from src.utils.excel_loader import carregar_dados_excel, preso_existe_no_excel
import pandas as pd
import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import re
import traceback

# Número máximo de tentativas para operações de rede
MAX_TENTATIVAS = 3
# Tempo de espera entre tentativas em segundos
TEMPO_ESPERA = 2

def formatar_data(data_str):
    """
    Formata uma string de data para o formato dd/mm/aaaa.
    
    Args:
        data_str: String com a data em qualquer formato
        
    Returns:
        String formatada como dd/mm/aaaa ou string original se não for possível formatar
    """
    if not data_str or not isinstance(data_str, str):
        return data_str
    
    # Remove espaços extras
    data_str = data_str.strip()
    
    # Padrões comuns de data
    # Formato: dd/mm/aaaa ou d/m/aaaa
    padrao1 = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})')
    # Formato: aaaa/mm/dd ou aaaa-mm-dd
    padrao2 = re.compile(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})')
    
    match1 = padrao1.search(data_str)
    match2 = padrao2.search(data_str)
    
    try:
        if match1:
            # Formato dd/mm/aaaa ou d/m/aaaa
            dia, mes, ano = match1.groups()
            # Garantir que dia e mês tenham 2 dígitos
            dia = dia.zfill(2)
            mes = mes.zfill(2)
            # Se o ano tiver 2 dígitos, assumir 20xx
            if len(ano) == 2:
                ano = '20' + ano
            return f"{dia}/{mes}/{ano}"
        elif match2:
            # Formato aaaa/mm/dd ou aaaa-mm-dd
            ano, mes, dia = match2.groups()
            # Garantir que dia e mês tenham 2 dígitos
            dia = dia.zfill(2)
            mes = mes.zfill(2)
            return f"{dia}/{mes}/{ano}"
        else:
            # Se não conseguir reconhecer o formato, retornar a string original
            return data_str
    except Exception:
        # Em caso de erro, retornar a string original
        return data_str

def calcular_idade(data_nascimento):
    """
    Calcula a idade com base na data de nascimento.
    
    Args:
        data_nascimento: String com a data de nascimento no formato dd/mm/aaaa
        
    Returns:
        Idade em anos ou string vazia se não for possível calcular
    """
    if not data_nascimento or not isinstance(data_nascimento, str):
        return ""
    
    try:
        # Tenta diferentes formatos de data
        for formato in ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']:
            try:
                data_nasc = datetime.strptime(data_nascimento, formato)
                hoje = datetime.now()
                idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
                return idade
            except ValueError:
                continue
    except Exception:
        pass
    
    return ""

def tratar_ala_cela(ala_cela_str):
    """
    Trata a string de ala e cela para extrair corretamente os valores.
    
    Args:
        ala_cela_str: String com informações de ala e cela (ex: "ALA: ENTRADA / 407")
        
    Returns:
        Tupla com (ala, cela)
    """
    if not ala_cela_str or not isinstance(ala_cela_str, str):
        return ("", "")
    
    # Remove a parte "ALA: " e qualquer espaço extra
    ala_cela_str = ala_cela_str.replace("ALA:", "").strip()
    
    # Verifica se contém a barra de separação
    if "/" in ala_cela_str:
        partes = ala_cela_str.split("/")
        ala = partes[0].strip()
        cela = "/".join(partes[1:]).strip()  # Une novamente caso haja mais de uma barra
        return (ala, cela)
    else:
        # Se não tiver barra, assume que é tudo ala
        return (ala_cela_str, "")

def tratar_cpf(cpf_str):
    """Remove o prefixo 'CPF: ' e retorna apenas o número do CPF."""
    if not cpf_str or not isinstance(cpf_str, str):
        return cpf_str
    
    return cpf_str.replace("CPF:", "").strip()

def tratar_mae(mae_str):
    """Remove o prefixo 'M E: ' e retorna apenas o nome da mãe."""
    if not mae_str or not isinstance(mae_str, str):
        return mae_str
    
    return mae_str.replace("M E:", "").strip()

def tratar_sentenca_dias(sentenca_str):
    """Remove ' DIAS' do final da string de sentença."""
    if not sentenca_str or not isinstance(sentenca_str, str):
        return sentenca_str
    
    return sentenca_str.replace(" DIAS", "").strip()


def _rank_conduta(texto):
    """Retorna o rank de gravidade da conduta (6=mais grave, 1=menos grave).
    Ordem: FECHADO > PREVENTIVADO > SEMI ABERTO > ABERTO > ALVARÁ > EXTINTO.
    Variações (ex: FECHADO FEDERAL) são tratadas pelo termo principal."""
    if not texto:
        return 0
    t = texto.upper()
    if 'FECHADO' in t:
        return 6
    if 'PREVENTIVADO' in t:
        return 5
    if 'SEMI' in t and 'ABERTO' in t:
        return 4
    if 'ABERTO' in t:
        return 3
    if 'ALVARÁ' in t or 'ALVARA' in t.replace('Á', 'A'):
        return 2
    if 'EXTINTO' in t:
        return 1
    return 0


def extrair_conduta_mais_gravosa(elementos):
    """
    Extrai a conduta mais gravosa de uma lista de elementos.
    Ordem de gravidade (mais grave primeiro): FECHADO > PREVENTIVADO > SEMI ABERTO > ABERTO > ALVARÁ > EXTINTO.
    Variações (ex: FECHADO FEDERAL) são tratadas pelo termo principal.
    Funciona com lista ou item único.
    
    Args:
        elementos: Objeto locator do Playwright com vários elementos
        
    Returns:
        str: A conduta mais gravosa ou string vazia
    """
    textos = []
    try:
        for i in range(elementos.count()):
            txt = elementos.nth(i).text_content()
            if txt and txt.strip():
                textos.append(txt.strip())
    except Exception:
        pass
    
    if not textos:
        return ""
    return max(textos, key=_rank_conduta)


def parsear_rji_biometria(texto_raw):
    """
    Parseia o texto do RJI para extrair número e status da biometria.
    - Se não houver nenhum número no texto, o preso ainda não tem RJI -> ("", "Não coletada")
    - O número RJI pode ter tamanhos variados.
    - O texto após o número indica se a biometria foi coletada.
    
    Ex: "19279433565 POSSUI BIOMETRIA" -> ("19279433565", "Coletada")
    Ex: "17000004189 Biometria Coletada" -> ("17000004189", "Coletada")
    Ex: "17000004189" -> ("17000004189", "Não coletada")
    Ex: "17000004189 Não coletada" -> ("17000004189", "Não coletada")
    Ex: "POSSUI BIOMETRIA" (sem número) -> ("", "Não coletada") - ainda não tem RJI
    Ex: "Não coletada" (sem número) -> ("", "Não coletada") - ainda não tem RJI
    
    Args:
        texto_raw: Texto bruto do campo RJI
        
    Returns:
        tuple: (numero_rji, status_biometria)
    """
    if not texto_raw or not isinstance(texto_raw, str):
        return ("", "Não coletada")
    
    texto = texto_raw.strip()
    if not texto:
        return ("", "Não coletada")
    
    # Busca a primeira sequência de dígitos (e hífens) - RJI pode ter formatos como "123-456" ou "123456"
    match_numero = re.search(r'(\d[\d\-]*)', texto)
    if not match_numero:
        # Sem número de RJI: ainda não tem RJI, mas o texto pode indicar biometria coletada
        resto_lower = texto.lower()
        positivos = ('possui biometria', 'biometria coletada', 'biometria realizada',
                     'coletada', 'realizada')
        if any(p in resto_lower for p in positivos):
            return ("", "Coletada")
        return ("", "Não coletada")
    
    numero = match_numero.group(1)
    # Texto após o número (indica status da biometria)
    pos_fim = match_numero.end()
    resto = texto[pos_fim:].strip() if pos_fim < len(texto) else ""
    
    if not resto:
        return (numero, "Não coletada")
    
    resto_lower = resto.lower()
    # Textos que indicam biometria NÃO coletada
    negativos = ('não coletada', 'nao coletada', 'não realizada', 'nao realizada',
                 'nao coletado', 'não coletado', 'não possui', 'nao possui')
    if any(n in resto_lower for n in negativos):
        return (numero, "Não coletada")
    
    # Textos que indicam biometria coletada (possui, coletada, realizada, etc.)
    positivos = ('possui biometria', 'biometria coletada', 'biometria realizada',
                 'coletada', 'realizada')
    if any(p in resto_lower for p in positivos):
        return (numero, "Coletada")
    
    # Texto ambíguo ou desconhecido -> considerar não coletada
    return (numero, "Não coletada")


def extrair_rji_ficha(page):
    """
    Extrai o texto do campo RJI da página Ficha Preso.
    Tenta múltiplos seletores pois a estrutura da tabela pode variar entre cadastros.
    
    Returns:
        str: Texto bruto do campo RJI ou string vazia se não encontrar
    """
    seletores = getattr(config, 'RJI_SELETORES_ALTERNATIVOS', ['tr:nth-child(3) .titulobk'])
    for seletor in seletores:
        try:
            loc = page.locator(seletor)
            if loc.count() > 0:
                texto = loc.first.text_content()
                if texto and texto.strip():
                    return texto.strip()
        except Exception:
            pass
    # Fallback: na primeira tabela, pegar a 3ª linha (estrutura típica da Ficha Preso)
    try:
        rows = page.locator('table').first.locator('tr').all()
        if len(rows) >= 3:
            texto = rows[2].text_content()
            if texto and texto.strip():
                return texto.strip()
    except Exception:
        pass
    return ""


def reordenar_colunas_excel(df, excluir_up=False):
    """
    Reordena as colunas do DataFrame conforme config.COLUNAS.
    Garante que ÚLTIMO LANÇAMENTO seja sempre a última coluna.
    
    Args:
        df: DataFrame a reordenar
        excluir_up: Se True, não inclui a coluna UP na saída
        
    Returns:
        DataFrame com colunas reordenadas
    """
    colunas_desejadas = [c for c in config.COLUNAS if c in df.columns and (not excluir_up or c != 'UP')]
    # Garante que ÚLTIMO LANÇAMENTO seja a última coluna
    if 'ÚLTIMO LANÇAMENTO' in df.columns and colunas_desejadas and colunas_desejadas[-1] != 'ÚLTIMO LANÇAMENTO':
        colunas_desejadas = [c for c in colunas_desejadas if c != 'ÚLTIMO LANÇAMENTO'] + ['ÚLTIMO LANÇAMENTO']
    extras = [c for c in df.columns if c not in config.COLUNAS and (not excluir_up or c != 'UP')]
    return df[colunas_desejadas + extras].copy()


def retry_em_caso_de_erro(func, *args, **kwargs):
    """
    Função para retentar operações em caso de erro de rede.
    
    Args:
        func: A função a ser executada
        *args, **kwargs: Argumentos para a função
        
    Returns:
        O resultado da função ou None em caso de falha após as tentativas
    """
    for tentativa in range(MAX_TENTATIVAS):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if tentativa < MAX_TENTATIVAS - 1:
                print(f"Erro na tentativa {tentativa+1}/{MAX_TENTATIVAS}: {str(e)}")
                print(f"Tentando novamente em {TEMPO_ESPERA} segundos...")
                time.sleep(TEMPO_ESPERA)
            else:
                print(f"Falha após {MAX_TENTATIVAS} tentativas: {str(e)}")
                raise

def navegar_para_url(page, url):
    """
    Navega para uma URL específica e aguarda o carregamento da página.
    Não depende de networkidle para evitar timeouts com requisições contínuas.
    
    Args:
        page: Objeto page do Playwright
        url: URL para navegação
    """
    print(f"[LOG] navegar_para_url: Navegando para {url}")
    sys.stdout.flush()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"[LOG] navegar_para_url: domcontentloaded alcançado")
        sys.stdout.flush()
        # Aguarda um pouco para garantir que a página carregou
        time.sleep(2)
        print(f"[LOG] navegar_para_url: Navegação concluída. URL atual: {page.url}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[LOG] navegar_para_url: ERRO ao navegar: {str(e)}")
        sys.stdout.flush()
        # Tenta continuar mesmo assim
        try:
            time.sleep(2)
        except:
            pass

def listar_presos_up(page, caminho_saida=None, interface=None, unidades_selecionadas=None, modo_teste=False, limite_teste=10):
    """
    Extrai dados de presos de todas as unidades prisionais e cria um arquivo Excel.
    Verifica se já existe um arquivo Excel com dados e só extrai informações de presos novos.
    
    Args:
        page: Objeto page do Playwright para navegação
        caminho_saida: Caminho opcional para salvar o arquivo Excel
        interface: Objeto da interface SeletorUnidades para atualizar o progresso
        unidades_selecionadas: Lista de códigos das unidades a serem processadas. Se None, processa todas.
        modo_teste: Se True, ativa o modo de teste limitando o número de presos por unidade
        limite_teste: Número máximo de presos a processar por unidade no modo de teste
        
    Returns:
        dict: Dicionário com DataFrames consolidado, por unidade e caminho do arquivo Excel
    """
    print("[LOG] ===== listar_presos_up() INICIADA =====")
    print(f"[LOG] Parâmetros recebidos:")
    print(f"[LOG]   - page: {type(page)} (None? {page is None})")
    print(f"[LOG]   - caminho_saida: {caminho_saida}")
    print(f"[LOG]   - interface: {type(interface)} (None? {interface is None})")
    print(f"[LOG]   - unidades_selecionadas: {unidades_selecionadas}")
    print(f"[LOG]   - modo_teste: {modo_teste}")
    print(f"[LOG]   - limite_teste: {limite_teste}")
    
    # Verificar se page é válido
    if page is None:
        print("[LOG] ERRO CRÍTICO: page é None!")
        return None
    
    try:
        current_url = page.url
        print(f"[LOG] URL atual da página: {current_url}")
    except Exception as e:
        print(f"[LOG] ERRO ao obter URL da página: {str(e)}")
        return None
    
    # Em modo teste: não carregar Excel existente, para que a saída tenha apenas os 5/10 por unidade
    if modo_teste:
        print("[LOG] Modo teste: não carregando Excel existente (saída terá apenas os presos processados)")
        dfs_unidades_existentes, df_consolidado_existente = {}, pd.DataFrame()
    else:
        print("[LOG] Carregando dados do Excel existente...")
        try:
            dfs_unidades_existentes, df_consolidado_existente = carregar_dados_excel()
            print(f"[LOG] Excel carregado: {len(dfs_unidades_existentes)} unidades, {len(df_consolidado_existente)} registros consolidados")
        except Exception as e:
            print(f"[LOG] ERRO ao carregar Excel: {str(e)}")
            dfs_unidades_existentes, df_consolidado_existente = {}, pd.DataFrame()
    
    # Dicionário para armazenar os DataFrames de cada unidade
    print("[LOG] Inicializando estruturas de dados...")
    dfs_unidades = dfs_unidades_existentes.copy() if dfs_unidades_existentes else {}
    
    # Inicializa o DataFrame consolidado com as colunas corretas
    df_consolidado = df_consolidado_existente.copy() if not df_consolidado_existente.empty else pd.DataFrame(columns=config.COLUNAS)
    print(f"[LOG] DataFrame consolidado inicializado com {len(df_consolidado)} registros e {len(df_consolidado.columns)} colunas")
    
    # Verificar se deve usar a interface ou console
    usando_interface = interface is not None
    print(f"[LOG] Usando interface: {usando_interface}")
    
    # Define quais unidades serão processadas
    if unidades_selecionadas:
        unidades_para_processar = unidades_selecionadas
        print(f"[LOG] Usando unidades selecionadas: {unidades_para_processar}")
    else:
        unidades_para_processar = config.UNIDADES_PRISIONAIS
        print(f"[LOG] Usando todas as unidades: {unidades_para_processar}")
    
    # Contador para acompanhar o progresso
    total_unidades = len(unidades_para_processar)
    print(f"[LOG] Total de unidades a processar: {total_unidades}")
    print("[LOG] ===== INICIANDO LOOP DE PROCESSAMENTO DE UNIDADES =====")
    
    for i, up in enumerate(unidades_para_processar):
        print(f"[LOG] ===== PROCESSANDO UNIDADE {i+1}/{total_unidades}: {up} =====")
        # Atualiza a barra de progresso e o status na interface
        percentual = (i / total_unidades) * 100
        mensagem = f"Processando unidade: {up} ({i+1}/{total_unidades})"
        
        if usando_interface:
            interface.atualizar_progresso(mensagem, percentual)
            
            # Verificar se o usuário cancelou o processamento
            if interface.verificar_cancelamento():
                print("Processamento cancelado pelo usuário")
                return None
        else:
            print(mensagem)
        
        # Navegar para a página da unidade
        url = config.URL_UNIDADE + up
        print(f"[LOG] Navegando para URL da unidade {up}: {url}")
        sys.stdout.flush()
        try:
            print(f"[LOG] Executando navegar_para_url()...")
            sys.stdout.flush()
            navegar_para_url(page, url)
            print(f"[LOG] Navegação para unidade {up} concluída. URL atual: {page.url}")
            sys.stdout.flush()
        except Exception as e:
            erro = f"Erro ao acessar unidade {up}: {str(e)}"
            print(f"[LOG] ERRO: {erro}")
            print(f"[LOG] Traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            continue
        
        # Localizar containers com informações dos presos
        print(f"[LOG] Localizando containers de presos na página...")
        print(f"[LOG] Seletor usado: {config.SELETORES_LISTA_PRESOS['containers_informacoes']}")
        try:
            containers = page.locator(config.SELETORES_LISTA_PRESOS['containers_informacoes'])
            print(f"[LOG] Locator criado. Contando elementos...")
            count_containers = containers.count()
            print(f"[LOG] Número de containers encontrados: {count_containers}")
            lista_containers = containers.all()
            print(f"[LOG] Lista de containers obtida: {len(lista_containers)} elementos")
            
            # Localizar links das fotos
            print(f"[LOG] Localizando fotos...")
            fotos = page.locator(config.SELETORES_LISTA_PRESOS['fotos'])
            count_fotos = fotos.count()
            print(f"[LOG] Número de fotos encontradas: {count_fotos}")
            # Normalizar os links de foto para URLs completas usando INICIO_URL_FOTOS
            lista_link = []
            for foto in fotos.all():
                src = foto.get_attribute('src') or ""
                if src:
                    nome_arquivo = src.split('/')[-1]
                    link_completo = config.INICIO_URL_FOTOS + nome_arquivo
                else:
                    link_completo = ""
                lista_link.append(link_completo)
            print(f"[LOG] Lista de links de fotos obtida: {len(lista_link)} elementos")
            
            # Se estiver em modo de teste, limita ANTES de processar (para garantir o limite)
            if modo_teste:
                limite_aplicar = int(limite_teste)
                lista_containers = lista_containers[:limite_aplicar]
                lista_link = lista_link[:limite_aplicar] if lista_link else []
                print(f"[LOG] Modo teste ativo: limitando a {limite_aplicar} presos por unidade")
            
            # Coletar códigos dos presos (após aplicar limite do modo teste)
            print(f"[LOG] Coletando códigos dos presos...")
            codigos_site = []
            for idx, container in enumerate(lista_containers):
                try:
                    texto = container.text_content()
                    codigo = texto.split('\n')[0][2:].strip()
                    codigos_site.append(codigo)
                    if idx < 3:  # Log dos primeiros 3 para debug
                        print(f"[LOG]   Preso {idx+1}: código={codigo}")
                except Exception as e:
                    print(f"[LOG] ERRO ao processar container {idx}: {str(e)}")
            
            print(f"[LOG] Total de códigos coletados: {len(codigos_site)}")
            
            # Verificar quais códigos já existem no Excel
            print(f"[LOG] Verificando códigos existentes no Excel...")
            codigos_existentes = set(df_consolidado['CÓDIGO'].values) if not df_consolidado.empty else set()
            print(f"[LOG] Códigos existentes no Excel: {len(codigos_existentes)}")
            
            # Filtrar apenas os containers dos presos que não existem no Excel
            indices_novos = [i for i, codigo in enumerate(codigos_site) if codigo not in codigos_existentes]
            print(f"[LOG] Índices de novos presos: {len(indices_novos)}")
            lista_containers = [lista_containers[i] for i in indices_novos]
            lista_link = [lista_link[i] for i in indices_novos] if lista_link else []
            
            print(f"Unidade {up}: {len(indices_novos)} novos presos encontrados de um total de {len(codigos_site)}")
            
        except Exception as e:
            erro = f"Erro ao localizar elementos na página da unidade {up}: {str(e)}"
            print(erro)
            continue
        
        print(f"[LOG] Total de presos a processar nesta unidade: {len(lista_containers)}")
        
        # DataFrame para armazenar os dados dos presos desta unidade
        df_presos = pd.DataFrame(columns=config.COLUNAS)
        print(f"[LOG] DataFrame criado com {len(config.COLUNAS)} colunas")
        
        # Para cada container de preso
        print(f"[LOG] ===== INICIANDO PROCESSAMENTO DE PRESOS =====")
        for index, container_preso in enumerate(lista_containers):
            print(f"[LOG] Processando preso {index+1}/{len(lista_containers)}")
            # Atualizar progresso para cada grupo de presos (a cada 10)
            if usando_interface and index % 10 == 0:
                perc_presos = (index / len(lista_containers)) * 100
                sub_percentual = percentual + (perc_presos / total_unidades)
                interface.atualizar_progresso(f"Extraindo dados: {up} - Preso {index+1}/{len(lista_containers)}", sub_percentual)
                
                # Verificar cancelamento
                if interface.verificar_cancelamento():
                    print("Processamento cancelado pelo usuário")
                    return None
            
            codigo, nome, mae, cpf, ala_cela = container_preso.text_content().split('\n')
            # Obter a foto correspondente ao índice atual
            link = lista_link[index] if index < len(lista_link) else ""
            
            # Aplicar strip para remover espaços extras
            codigo = codigo[2:].strip()
            nome = nome.strip()
            mae = tratar_mae(mae)
            cpf = tratar_cpf(cpf)
            ala, cela = tratar_ala_cela(ala_cela)
            
            # Adicionando dados ao DataFrame da unidade
            novo_registro = pd.DataFrame([{
                'UP': up,
                'CÓDIGO': codigo, 
                'CADASTRO': config.URL_FICHA_MENU + codigo,
                'NOME': nome, 
                'MÃE': mae, 
                'CPF': cpf, 
                'ALA': ala, 
                'CELA': cela, 
                'FOTO': link
            }])
            
            # Garantir que o novo_registro tenha todas as colunas do df_presos
            for col in df_presos.columns:
                if col not in novo_registro.columns:
                    novo_registro[col] = None
            
            df_presos = pd.concat([df_presos, novo_registro], ignore_index=True)
        
        # Atualizar progresso ao iniciar a coleta de informações detalhadas
        print(f"[LOG] ===== INICIANDO COLETA DE DETALHES DOS PRESOS =====")
        print(f"[LOG] Total de presos para coletar detalhes: {len(df_presos)}")
        if usando_interface:
            interface.atualizar_progresso(f"Coletando detalhes dos presos da unidade {up}", percentual)
        
        # Mapeamento de URLs para as chaves no dicionário LOCALIZADORES
        url_para_chave = {
            config.URL_FICHA_PRESO: 'URL_FICHA_PRESO',
            config.URL_CADASTRO: 'URL_CADASTRO',
            config.URL_INFORMES: 'URL_INFORMES',
            config.URL_CERTIDAO_CARCERARIA: 'URL_CERTIDAO_CARCERARIA',
            config.URL_FICHA_CARCERARIA: 'URL_FICHA_CARCERARIA'
        }
        print(f"[LOG] URLs a processar: {len(url_para_chave)}")
        
        for j, codigo in enumerate(df_presos['CÓDIGO']):
            print(f"[LOG] ===== Processando detalhes do preso {j+1}/{len(df_presos)}: código {codigo} =====")
            # Atualizar progresso para cada conjunto de detalhes
            if usando_interface and j % 5 == 0:
                perc_detalhes = (j / len(df_presos)) * 100
                sub_percentual = percentual + (perc_detalhes / total_unidades)
                interface.atualizar_progresso(f"Extraindo detalhes: {up} - Preso {j+1}/{len(df_presos)}", sub_percentual)
                
                # Verificar cancelamento
                if interface.verificar_cancelamento():
                    print("Processamento cancelado pelo usuário")
                    return None
            
            # Iterar por cada URL (página) uma única vez
            print(f"[LOG] Processando {len(config.LISTA_URLS_INFO_PRESO)} URLs para o preso {codigo}")
            for url_idx, url in enumerate(config.LISTA_URLS_INFO_PRESO):
                print(f"[LOG]   URL {url_idx+1}/{len(config.LISTA_URLS_INFO_PRESO)}: {url}")
                # Obter a chave correspondente para o dicionário LOCALIZADORES
                chave_url = url_para_chave.get(url)
                
                if not chave_url:
                    print(f"[LOG]   AVISO: URL {url} não possui mapeamento para LOCALIZADORES. Pulando.")
                    continue
                
                # Verificar se há campos para extrair desta URL
                if not config.LOCALIZADORES[chave_url]:
                    print(f"[LOG]   Nenhum localizador configurado para {chave_url}. Pulando.")
                    continue
                
                print(f"[LOG]   Localizadores disponíveis: {list(config.LOCALIZADORES[chave_url].keys())}")
                
                # Acessar a URL apenas uma vez
                try:
                    url_completa = url + codigo
                    print(f"[LOG]   Navegando para: {url_completa}")
                    navegar_para_url(page, url_completa)
                    print(f"[LOG]   Navegação concluída. URL atual: {page.url}")
                    
                    # Extrair todos os campos desta URL de uma só vez
                    for localizador in config.LOCALIZADORES[chave_url]:
                        try:
                            elementos = retry_em_caso_de_erro(page.locator, config.LOCALIZADORES[chave_url][localizador])
                            
                            if localizador == 'CONDUTA' and url == config.URL_FICHA_CARCERARIA:
                                # Conduta: pegar todos os itens e retornar o mais gravoso
                                texto = extrair_conduta_mais_gravosa(elementos)
                                df_presos.loc[df_presos['CÓDIGO'] == codigo, localizador] = texto
                            elif localizador == 'RJI' and url == config.URL_FICHA_PRESO:
                                # RJI: extração robusta com múltiplos seletores + parse do número (pode ter hífen) e biometria
                                raw = extrair_rji_ficha(page)
                                numero_rji, status_biometria = parsear_rji_biometria(raw)
                                df_presos.loc[df_presos['CÓDIGO'] == codigo, 'RJI'] = numero_rji
                                df_presos.loc[df_presos['CÓDIGO'] == codigo, 'BIOMETRIA'] = status_biometria
                            elif url == config.URL_CERTIDAO_CARCERARIA:
                                # Para URL_CERTIDAO_CARCERARIA, sempre pegar o último item
                                if elementos.count() > 0:
                                    texto = retry_em_caso_de_erro(elementos.last.text_content).strip()
                                else:
                                    texto = ""
                                df_presos.loc[df_presos['CÓDIGO'] == codigo, localizador] = texto
                            else:
                                # Para outras URLs, sempre pegar o primeiro item
                                if elementos.count() > 0:
                                    texto = retry_em_caso_de_erro(elementos.first.text_content).strip()
                                else:
                                    texto = ""
                                df_presos.loc[df_presos['CÓDIGO'] == codigo, localizador] = texto
                            
                        except Exception as e:
                            tipo_item = "especial" if localizador in ('CONDUTA', 'RJI') else ("último" if url == config.URL_CERTIDAO_CARCERARIA else "primeiro")
                            erro = f"Erro ao obter {localizador} ({tipo_item}) na URL {url} para o código {codigo}: {str(e)}"
                            print(erro)
                            
                except Exception as e:
                    erro = f"Erro ao acessar URL {url} para o código {codigo}: {str(e)}"
                    print(erro)
            
            # Exibir ID e nome do preso após processar todos os seus detalhes
            nome_preso = df_presos.loc[df_presos['CÓDIGO'] == codigo, 'NOME'].values[0] if len(df_presos[df_presos['CÓDIGO'] == codigo]) > 0 else "Nome não encontrado"
            print(f"Preso processado: {codigo} - {nome_preso}")
            if usando_interface:
                interface.atualizar_progresso(f"Preso processado: {codigo} - {nome_preso}", None)
        
        # Armazena o DataFrame no dicionário
        if len(df_presos) > 0:
            if up in dfs_unidades:
                dfs_unidades[up] = pd.concat([dfs_unidades[up], df_presos], ignore_index=True, sort=False)
            else:
                dfs_unidades[up] = df_presos.copy()
            df_consolidado = pd.concat([df_consolidado, df_presos], ignore_index=True, sort=False)
    
    # Aplicar tratamentos finais em todos os DataFrames
    for up, df in dfs_unidades.items():
        # Formatar datas
        if 'DATA NASC.' in df.columns:
            df['DATA NASC.'] = df['DATA NASC.'].apply(formatar_data)
        
        if 'DATA PRISÃO' in df.columns:
            df['DATA PRISÃO'] = df['DATA PRISÃO'].apply(formatar_data)
        
        # Calcular idade
        if 'DATA NASC.' in df.columns:
            df['IDADE'] = df['DATA NASC.'].apply(calcular_idade)
        
        # Tratar sentença dias
        if 'SENTENÇA DIAS' in df.columns:
            df['SENTENÇA DIAS'] = df['SENTENÇA DIAS'].apply(tratar_sentenca_dias)
        
        # Ordenar o DataFrame por ALA, CELA, NOME
        if 'ALA' in df.columns and 'CELA' in df.columns and 'NOME' in df.columns:
            df = df.sort_values(by=['ALA', 'CELA', 'NOME'])
        
        # Atualizar o DataFrame no dicionário
        dfs_unidades[up] = df
    
    # Também aplicar os mesmos tratamentos ao DataFrame consolidado
    if 'DATA NASC.' in df_consolidado.columns:
        df_consolidado['DATA NASC.'] = df_consolidado['DATA NASC.'].apply(formatar_data)
    
    if 'DATA PRISÃO' in df_consolidado.columns:
        df_consolidado['DATA PRISÃO'] = df_consolidado['DATA PRISÃO'].apply(formatar_data)
    
    if 'DATA NASC.' in df_consolidado.columns:
        df_consolidado['IDADE'] = df_consolidado['DATA NASC.'].apply(calcular_idade)
    
    if 'SENTENÇA DIAS' in df_consolidado.columns:
        df_consolidado['SENTENÇA DIAS'] = df_consolidado['SENTENÇA DIAS'].apply(tratar_sentenca_dias)
    
    # Ordenar o DataFrame consolidado por UP (conforme a ordem em config.UNIDADES_PRISIONAIS), depois ALA, CELA, NOME
    if len(df_consolidado) > 0:
        # Criar um mapeamento de UP para posição na lista
        ordem_up = {up: i for i, up in enumerate(config.UNIDADES_PRISIONAIS)}
        
        # Adicionar coluna temporária para ordenação
        df_consolidado['_ORDEM_UP'] = df_consolidado['UP'].map(ordem_up)
        
        # Ordenar o DataFrame
        colunas_ordenacao = ['_ORDEM_UP']
        if 'ALA' in df_consolidado.columns:
            colunas_ordenacao.append('ALA')
        if 'CELA' in df_consolidado.columns:
            colunas_ordenacao.append('CELA')
        if 'NOME' in df_consolidado.columns:
            colunas_ordenacao.append('NOME')
        
        df_consolidado = df_consolidado.sort_values(by=colunas_ordenacao)
        
        # Remover a coluna temporária (se existir)
        if '_ORDEM_UP' in df_consolidado.columns:
            df_consolidado = df_consolidado.drop(columns=['_ORDEM_UP'])
    
    # Atualizar a interface indicando que o processamento foi concluído
    if usando_interface:
        interface.atualizar_progresso("Processamento concluído! Salvando arquivo...", 95)
    
    # Tenta criar um backup silencioso no disco F
    try:
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"Informações_Presos_{data_hora}.xlsx"
        caminho_backup = os.path.join("F:", "PAMC-ADM_Backup", nome_arquivo)
        
        # Tenta criar o diretório de backup se não existir
        os.makedirs(os.path.dirname(caminho_backup), exist_ok=True)
        
        # Tenta salvar o backup silenciosamente
        with pd.ExcelWriter(caminho_backup, engine='xlsxwriter') as writer:
            if len(dfs_unidades) > 1:
                reordenar_colunas_excel(df_consolidado).to_excel(writer, sheet_name='Consolidado', index=False)
            for up, df in dfs_unidades.items():
                df_sem_up = df.drop(columns=['UP']) if 'UP' in df.columns else df.copy()
                reordenar_colunas_excel(df_sem_up, excluir_up=True).to_excel(writer, sheet_name=up, index=False)
    except:
        pass  # Ignora silenciosamente qualquer erro
    
    # Define o caminho de saída do Excel
    if caminho_saida is None:
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"Informações_Presos_{data_hora}.xlsx"
        
        if usando_interface:
            # Exibe diálogo para escolher onde salvar o arquivo
            root = tk.Tk()
            root.withdraw()  # Esconde a janela principal
            
            caminho_saida = filedialog.asksaveasfilename(
                title="Salvar relatório de presos",
                initialfile=nome_arquivo,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            # Se o usuário cancelar, interrompe o processamento
            if not caminho_saida:
                if usando_interface:
                    interface.atualizar_progresso("Operação cancelada pelo usuário.", 0)
                print("Usuário cancelou seleção. Operação cancelada.")
                return None
        else:
            caminho_saida = os.path.join(config.BASE_DIR, '..', 'output', nome_arquivo)
        
        # Garante que o diretório de saída exista, se for um caminho padrão
        if os.path.dirname(caminho_saida) and not os.path.exists(os.path.dirname(caminho_saida)):
            os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    
    # Cria o arquivo Excel
    try:
        if usando_interface:
            interface.atualizar_progresso("Criando arquivo Excel...", 98)
            
        with pd.ExcelWriter(caminho_saida, engine='xlsxwriter') as writer:
            if len(dfs_unidades) > 1:
                reordenar_colunas_excel(df_consolidado).to_excel(writer, sheet_name='Consolidado', index=False)
            for up, df in dfs_unidades.items():
                df_sem_up = df.drop(columns=['UP']) if 'UP' in df.columns else df.copy()
                reordenar_colunas_excel(df_sem_up, excluir_up=True).to_excel(writer, sheet_name=up, index=False)
        
        if usando_interface:
            interface.atualizar_progresso(f"Arquivo Excel criado com sucesso: {caminho_saida}", 100)
        print(f"Arquivo Excel criado com sucesso: {caminho_saida}")
        
        # Mostrar mensagem de sucesso
        if not usando_interface:
            messagebox.showinfo("Sucesso", f"Arquivo Excel criado com sucesso!\n\nCaminho: {caminho_saida}")
    except Exception as e:
        erro_msg = f"Erro ao criar arquivo Excel: {e}"
        if usando_interface:
            interface.atualizar_progresso(erro_msg, 0)
        print(erro_msg)
        
        # Tenta salvar em um local alternativo em caso de erro
        try:
            caminho_alternativo = os.path.join(os.path.expanduser('~'), 'presos_unidades_backup.xlsx')
            with pd.ExcelWriter(caminho_alternativo, engine='xlsxwriter') as writer:
                if len(dfs_unidades) > 1:
                    reordenar_colunas_excel(df_consolidado).to_excel(writer, sheet_name='Consolidado', index=False)
            
            msg_backup = f"Arquivo de backup criado em: {caminho_alternativo}"
            if usando_interface:
                interface.atualizar_progresso(msg_backup, 100)
            print(msg_backup)
            
            if not usando_interface:
                messagebox.showinfo("Backup Criado", f"Arquivo de backup criado em:\n{caminho_alternativo}")
            
            caminho_saida = caminho_alternativo
        except Exception as e2:
            erro_backup = f"Erro ao criar arquivo de backup: {e2}"
            if usando_interface:
                interface.atualizar_progresso(erro_backup, 0)
            print(erro_backup)
            return None
    
    print("[LOG] ===== listar_presos_up() FINALIZADA =====")
    print(f"[LOG] Retornando resultado com {len(dfs_unidades)} unidades e {len(df_consolidado)} registros consolidados")
    resultado = {'consolidado': df_consolidado, 'unidades': dfs_unidades, 'caminho_excel': caminho_saida}
    print(f"[LOG] Caminho do Excel: {caminho_saida}")
    return resultado

