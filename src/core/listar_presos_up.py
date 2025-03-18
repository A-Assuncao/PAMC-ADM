from src.utils import config
import pandas as pd
import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import re

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

def listar_presos_up(page, caminho_saida=None, interface=None, unidades_selecionadas=None, modo_teste=False, limite_teste=10):
    """
    Extrai dados de presos de todas as unidades prisionais e cria um arquivo Excel.
    
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
    # Dicionário para armazenar os DataFrames de cada unidade
    dfs_unidades = {}
    # DataFrame para consolidar todas as unidades
    df_consolidado = pd.DataFrame(columns=config.COLUNAS)
    
    # Verificar se deve usar a interface ou console
    usando_interface = interface is not None
    
    # Define quais unidades serão processadas
    if unidades_selecionadas:
        unidades_para_processar = unidades_selecionadas
    else:
        unidades_para_processar = config.UNIDADES_PRISIONAIS
    
    # Contador para acompanhar o progresso
    total_unidades = len(unidades_para_processar)
    
    for i, up in enumerate(unidades_para_processar):
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
        
        df_presos = pd.DataFrame(columns=config.COLUNAS)
        
        # Navegação com retry para lidar com problemas de conexão
        def navegar_para_url(url):
            return retry_em_caso_de_erro(page.goto, url)
        
        # Navegar para a página da unidade com retry
        navegar_para_url(config.URL_UNIDADE + up)
        
        # Obter todas as fotos e containers de uma vez
        # Usar .all() para obter todos os elementos de imagem, depois coletar os atributos src individualmente
        elementos_foto = retry_em_caso_de_erro(page.locator, config.SELETORES_LISTA_PRESOS['fotos']).all()
        lista_foto = []
        for elemento in elementos_foto:
            try:
                src = retry_em_caso_de_erro(elemento.get_attribute, 'src')
                if src:
                    lista_foto.append(src)
            except Exception as e:
                print(f"Erro ao obter atributo src: {e}")
        
        # Log do número de fotos encontradas
        print(f"Encontradas {len(lista_foto)} fotos na unidade {up}")
        
        lista_containers = retry_em_caso_de_erro(page.locator, config.SELETORES_LISTA_PRESOS['containers_informacoes']).all()
        print(f"Encontrados {len(lista_containers)} containers de presos na unidade {up}")
        
        # Verificar se o número de fotos corresponde ao número de containers
        if len(lista_foto) != len(lista_containers):
            mensagem_diferenca = f"AVISO: Número diferente de fotos ({len(lista_foto)}) e presos ({len(lista_containers)}) na unidade {up}"
            print(mensagem_diferenca)
            if usando_interface:
                interface.atualizar_progresso(mensagem_diferenca, percentual)
            
            # Se não encontramos nenhuma foto, usar URLs vazias
            if len(lista_foto) == 0:
                print(f"ALERTA: Nenhuma foto encontrada para a unidade {up}. Usando links vazios.")
                lista_link = [""] * len(lista_containers)
            # Se temos menos fotos que presos, repetir a última foto ou adicionar vazias
            elif len(lista_foto) < len(lista_containers):
                ultima_foto = lista_foto[-1] if lista_foto else ""
                while len(lista_foto) < len(lista_containers):
                    if ultima_foto:
                        lista_foto.append(ultima_foto)
                    else:
                        lista_foto.append("")
            # Se temos mais fotos que presos, truncar a lista
            else:
                lista_foto = lista_foto[:len(lista_containers)]
        
        # Criar lista de links completos para as fotos
        lista_link = []
        for foto in lista_foto:
            if foto and isinstance(foto, str):
                # Tenta extrair o ID da foto de várias maneiras possíveis
                if "../../fotos/presos/" in foto:
                    # Formato padrão encontrado no HTML
                    caminho_relativo = foto.split("../../fotos/presos/")[-1]
                    link = config.INICIO_URL_FOTOS + caminho_relativo
                elif "/fotos/presos/" in foto:
                    # Alternativa se o caminho estiver em formato diferente
                    caminho_relativo = foto.split("/fotos/presos/")[-1]
                    link = config.INICIO_URL_FOTOS + caminho_relativo
                elif foto.endswith(".jpg") or foto.endswith(".png") or foto.endswith(".jpeg"):
                    # Se apenas temos o nome do arquivo, usamos diretamente
                    link = config.INICIO_URL_FOTOS + foto
                else:
                    print(f"AVISO: Formato de foto não reconhecido: {foto}")
                    link = ""
                
                lista_link.append(link)
            else:
                # Se não puder extrair o caminho, adiciona link vazio
                lista_link.append("")
        
        # Verificar e ajustar os links conforme necessário
        if len(lista_link) != len(lista_containers):
            print(f"ALERTA: Número de links ({len(lista_link)}) diferente do número de presos ({len(lista_containers)}). Ajustando...")
            if len(lista_link) < len(lista_containers):
                lista_link.extend([""] * (len(lista_containers) - len(lista_link)))
            else:
                lista_link = lista_link[:len(lista_containers)]
        
        # Atualizar progresso ao iniciar a coleta de dados dos presos
        if usando_interface:
            interface.atualizar_progresso(f"Coletando informações de {len(lista_containers)} presos da unidade {up}", percentual)
        
        # Se estiver no modo de teste, limita o número de presos a processar
        if modo_teste and limite_teste > 0:
            # Log da limitação
            msg_limite = f"MODO TESTE: Limitando a {limite_teste} presos na unidade {up} (total disponível: {len(lista_containers)})"
            print(msg_limite)
            if usando_interface:
                interface.atualizar_progresso(msg_limite, percentual)
            
            # Limita a lista de containers e links ao número definido no modo de teste
            lista_containers = lista_containers[:limite_teste] if len(lista_containers) > limite_teste else lista_containers
            lista_link = lista_link[:limite_teste] if len(lista_link) > limite_teste else lista_link
        
        # Agora processar os containers junto com seus links correspondentes
        for index, container_preso in enumerate(lista_containers):
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
            novo_registro = {
                'UP': up,
                'CÓDIGO': codigo, 
                'NOME': nome, 
                'MÃE': mae, 
                'CPF': cpf, 
                'ALA': ala, 
                'CELA': cela, 
                'FOTO': link
            }
            df_presos = pd.concat([df_presos, pd.DataFrame([novo_registro])], ignore_index=True)
        
        # Atualizar progresso ao iniciar a coleta de informações detalhadas
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
        
        for j, codigo in enumerate(df_presos['CÓDIGO']):
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
            for url in config.LISTA_URLS_INFO_PRESO:
                # Obter a chave correspondente para o dicionário LOCALIZADORES
                chave_url = url_para_chave.get(url)
                
                if not chave_url:
                    print(f"AVISO: URL {url} não possui mapeamento para LOCALIZADORES. Pulando.")
                    continue
                
                # Verificar se há campos para extrair desta URL
                if not config.LOCALIZADORES[chave_url]:
                    continue
                
                # Acessar a URL apenas uma vez
                try:
                    navegar_para_url(url + codigo)
                    
                    # Extrair todos os campos desta URL de uma só vez
                    for localizador in config.LOCALIZADORES[chave_url]:
                        try:
                            elementos = retry_em_caso_de_erro(page.locator, config.LOCALIZADORES[chave_url][localizador])
                            
                            if url == config.URL_CERTIDAO_CARCERARIA:
                                # Para URL_CERTIDAO_CARCERARIA, sempre pegar o último item
                                if elementos.count() > 0:
                                    texto = retry_em_caso_de_erro(elementos.last.text_content).strip()
                                else:
                                    texto = ""
                            else:
                                # Para outras URLs, sempre pegar o primeiro item
                                if elementos.count() > 0:
                                    texto = retry_em_caso_de_erro(elementos.first.text_content).strip()
                                else:
                                    texto = ""
                                    
                            # Armazenar o valor no DataFrame
                            df_presos.loc[df_presos['CÓDIGO'] == codigo, localizador] = texto
                            
                        except Exception as e:
                            tipo_item = "último" if url == config.URL_CERTIDAO_CARCERARIA else "primeiro"
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
        dfs_unidades[up] = df_presos.copy()
        
        # Adiciona ao DataFrame consolidado
        df_consolidado = pd.concat([df_consolidado, df_presos], ignore_index=True)
    
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
        
        # Remover a coluna temporária
        df_consolidado = df_consolidado.drop(columns=['_ORDEM_UP'])
    
    # Atualizar a interface indicando que o processamento foi concluído
    if usando_interface:
        interface.atualizar_progresso("Processamento concluído! Salvando arquivo...", 95)
    
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
            # Primeira aba é o consolidado
            if len(dfs_unidades) > 1:
                df_consolidado.to_excel(writer, sheet_name='Consolidado', index=False)
            
            # Uma aba para cada unidade sem a coluna UP
            for up, df in dfs_unidades.items():
                # Remove a coluna UP para as abas individuais
                df_sem_up = df.drop(columns=['UP'])
                df_sem_up.to_excel(writer, sheet_name=up, index=False)
        
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
                    df_consolidado.to_excel(writer, sheet_name='Consolidado', index=False)
            
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
    
    return {'consolidado': df_consolidado, 'unidades': dfs_unidades, 'caminho_excel': caminho_saida}

