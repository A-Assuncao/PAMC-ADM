#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serviço de Atualização Automática

Este módulo fornece funcionalidades para verificar, baixar e instalar atualizações
de software automaticamente. Ele segue os princípios SOLID e é projetado para ser
facilmente reutilizável em diferentes projetos.

Exemplo de uso:
    
    # Uso básico com a função de conveniência
    from src.utils.updater import check_and_update
    
    # Verifica e atualiza automaticamente
    check_and_update()
    
    # Ou usando a classe diretamente para mais controle
    from src.utils.updater import UpdaterService
    
    updater = UpdaterService(app_name="Minha Aplicação", current_version="v1.0.0")
    latest = updater.get_latest_version()
    if latest:
        if updater.prompt_user_for_update(latest):
            update_path = updater.download_update(latest)
            if update_path:
                updater.install_update(update_path)
"""

import os
import sys
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
from packaging import version
from urllib.parse import urljoin
from pathlib import Path
import json

# Importar as configurações de src.utils.config
from src.utils import config

# Logger para registrar eventos
try:
    from src.utils.logger import Logger
except ImportError:
    # Logger simples caso o módulo logger não esteja disponível
    class Logger:
        @staticmethod
        def get_logger():
            return type('', (), {'info': print, 'error': print, 'warning': print, 'debug': print})()
        
        @staticmethod
        def capture_error(e, context=None):
            print(f"Erro: {str(e)}, Contexto: {context}")

# Configurações de atualização
APP_NAME = getattr(config, 'APP_NAME', "PAMC-ADM")
APP_VERSION = getattr(config, 'APP_VERSION', "v1.0.0")
UPDATE_URL = getattr(config, 'UPDATE_URL', "")
VERSION_FILE = getattr(config, 'VERSION_FILE', "latest_version.txt")
GITHUB_REPO = getattr(config, 'GITHUB_REPO', "A-Assuncao/PAMC-ADM")

class UpdaterService:
    """
    Classe responsável por gerenciar o processo de atualização do software.
    
    Esta classe segue o princípio de responsabilidade única (S do SOLID) ao
    lidar exclusivamente com a lógica de atualização do software. Ela fornece
    métodos para verificar, baixar e instalar atualizações, além de interagir
    com o usuário através de interfaces gráficas simples.
    
    Atributos:
        app_name (str): Nome da aplicação para exibição e nomeação de arquivos.
        current_version (str): Versão atual da aplicação, usada para comparação.
        update_url (str): URL base onde as atualizações estão hospedadas.
        version_file (str): Nome do arquivo que contém a versão mais recente.
        logger (Logger): Instância do logger para registro de eventos.
    
    Exemplo:
        updater = UpdaterService(
            app_name="Minha Aplicação", 
            current_version="v1.0.0",
            update_url="https://exemplo.com/atualizacoes/"
        )
        
        if updater.check_and_update():
            print("Atualização concluída com sucesso")
    """
    
    def __init__(self, app_name=None, current_version=None, update_url=None, version_file=None):
        """
        Inicializa o serviço de atualização.
        
        Args:
            app_name (str, optional): Nome da aplicação. Default é valor de settings ou "Aplicação".
            current_version (str, optional): Versão atual da aplicação. Default é valor de settings ou "v0.0.0".
            update_url (str, optional): URL base para verificação de atualizações. Default é valor de settings ou "".
            version_file (str, optional): Nome do arquivo que contém a versão mais recente. Default é 
                                          valor de settings ou "latest_version.txt".
        """
        self.app_name = app_name or APP_NAME
        self.current_version = current_version or APP_VERSION
        self.update_url = update_url or UPDATE_URL
        self.version_file = version_file or VERSION_FILE
        self.logger = Logger.get_logger()
        
    def get_latest_version(self):
        """
        Obtém a versão mais recente disponível nas releases do GitHub.
        
        Este método se conecta à API do GitHub e verifica a release mais recente
        do repositório configurado.
        
        Returns:
            dict or None: Dicionário com informações da release mais recente ou None se:
                         - Ocorrer um erro de conexão com o GitHub
                         - Não houver releases disponíveis
                         - Ocorrer qualquer outra exceção durante o processo
        
        Raises:
            Não lança exceções, captura-as internamente e retorna None.
        """
        try:
            # Construir URL da API do GitHub para a release mais recente
            github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            self.logger.debug(f"Verificando versão em: {github_api_url}")
            
            # Realizar a requisição
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(github_api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parsear a resposta JSON
            release_data = response.json()
            latest_version = release_data.get("tag_name", "").strip()
            
            if not latest_version:
                self.logger.warning("Versão não encontrada na resposta da API do GitHub.")
                return None
                
            self.logger.info(f"Versão mais recente encontrada: {latest_version}")
            return {
                "version": latest_version,
                "data": release_data
            }
        except requests.RequestException as e:
            self.logger.error(f"Erro ao verificar atualizações no GitHub: {str(e)}")
            Logger.capture_error(e, context={"github_repo": GITHUB_REPO})
            return None
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Erro ao processar resposta da API do GitHub: {str(e)}")
            Logger.capture_error(e)
            return None
    
    def download_update(self, release_info, target_path=None):
        """
        Baixa o arquivo de atualização a partir das releases do GitHub.
        
        Busca o asset com extensão .exe na release especificada e o baixa.
        
        Args:
            release_info (dict): Dicionário com informações da release, incluindo a versão e os dados completos.
            target_path (str, optional): Caminho completo onde salvar o arquivo. 
                                         Se None, usa o diretório atual.
            
        Returns:
            str or None: Caminho completo do arquivo baixado ou None se:
                         - Não houver assets compatíveis na release
                         - Ocorrer um erro de conexão com o servidor
                         - Não for possível salvar o arquivo no destino
                         - Ocorrer qualquer outra exceção durante o processo
        
        Raises:
            Não lança exceções, captura-as internamente e retorna None.
        """
        try:
            # Obter a versão
            version_tag = release_info["version"]
            release_data = release_info["data"]
            
            # Procurar por assets .exe
            assets = release_data.get("assets", [])
            exe_assets = [asset for asset in assets if asset.get("name", "").lower().endswith(".exe")]
            
            if not exe_assets:
                self.logger.warning(f"Nenhum arquivo .exe encontrado na release {version_tag}")
                return None
                
            # Usar o primeiro asset .exe encontrado
            asset = exe_assets[0]
            download_url = asset.get("browser_download_url")
            filename = asset.get("name")
            
            if not download_url:
                self.logger.warning(f"URL de download não encontrado para a release {version_tag}")
                return None
            
            # Definir caminho de destino se não fornecido
            if target_path is None:
                target_path = os.path.join(os.getcwd(), filename)
            
            # Baixar o arquivo
            self.logger.info(f"Baixando atualização de: {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Cria o diretório de destino se não existir
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            
            # Baixa o arquivo em chunks para não sobrecarregar a memória
            with open(target_path, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            
            self.logger.info(f"Atualização baixada em: {target_path}")
            return target_path
        except requests.RequestException as e:
            self.logger.error(f"Erro ao baixar atualização: {str(e)}")
            Logger.capture_error(e, context={"version": release_info.get("version")})
            return None
        except IOError as e:
            self.logger.error(f"Erro ao salvar arquivo de atualização: {str(e)}")
            Logger.capture_error(e, context={"target_path": target_path})
            return None
    
    def prompt_user_for_update(self, release_info):
        """
        Pergunta ao usuário se deseja atualizar.
        
        Exibe uma caixa de diálogo usando tkinter, mostrando a versão atual
        e a nova versão disponível, e pergunta se o usuário deseja atualizar.
        
        Args:
            release_info (dict): Dicionário com informações da release, incluindo a versão.
            
        Returns:
            bool: True se o usuário aceitar a atualização, False se:
                  - O usuário recusar a atualização
                  - Ocorrer qualquer erro ao exibir a caixa de diálogo
                  - Tkinter não estiver disponível
        
        Raises:
            Não lança exceções, captura-as internamente e retorna False.
        """
        try:
            root = tk.Tk()
            root.withdraw()  # Oculta a janela principal
            
            latest_version = release_info["version"]
            
            # Extrair descrição da release
            release_data = release_info["data"]
            release_notes = release_data.get("body", "").strip() or "Novos recursos e correções de bugs."

            message = (
                f"Uma nova versão do {self.app_name} ({latest_version}) está disponível.\n"
                f"Versão atual: {self.current_version}\n\n"
                f"Notas da versão:\n{release_notes[:200]}{'...' if len(release_notes) > 200 else ''}\n\n"
                f"Deseja atualizar agora?"
            )
            
            result = messagebox.askyesno("Atualização Disponível", message)
            root.destroy()
            
            self.logger.info(f"Usuário {'aceitou' if result else 'recusou'} a atualização.")
            return result
        except Exception as e:
            self.logger.error(f"Erro ao exibir diálogo de atualização: {str(e)}")
            Logger.capture_error(e)
            return False
    
    def install_update(self, update_path):
        """
        Instala a atualização baixada.
        
        Executa o arquivo de atualização baixado usando subprocess.
        O comportamento exato depende do sistema operacional e do tipo de instalador.
        
        Args:
            update_path (str): Caminho completo para o arquivo executável de atualização.
            
        Returns:
            bool: True se a instalação foi iniciada com sucesso, False se:
                  - Ocorrer qualquer erro ao executar o instalador
                  - O arquivo não existir ou não for executável
                  - O processo não puder ser iniciado
        
        Raises:
            Não lança exceções, captura-as internamente e retorna False.
        """
        try:
            self.logger.info(f"Iniciando instalação da atualização: {update_path}")
            subprocess.Popen(update_path, shell=True)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao iniciar instalação: {str(e)}")
            Logger.capture_error(e, context={"update_path": update_path})
            return False
    
    def check_and_update(self, silent=False, auto_install=True):
        """
        Verifica por atualizações e, se disponível, permite que o usuário escolha se deseja atualizar.
        
        Este método combina os outros métodos da classe para realizar o fluxo completo
        de verificação, download e instalação de atualizações:
        1. Verifica se há uma nova versão disponível
        2. Compara com a versão atual
        3. Se houver uma versão mais recente:
           - Pergunta ao usuário se deseja atualizar (se não for silencioso)
           - Baixa a atualização
           - Instala a atualização (se auto_install for True)
           - Encerra a aplicação atual (se a instalação for bem-sucedida)
        
        Args:
            silent (bool, optional): Se True, não exibe diálogos para o usuário. Default é False.
            auto_install (bool, optional): Se True, instala automaticamente após o download. Default é True.
            
        Returns:
            bool: True se uma atualização foi encontrada e processada com sucesso, False se:
                  - Não houver uma atualização disponível
                  - A verificação da versão falhar
                  - O usuário recusar a atualização
                  - O download da atualização falhar
                  - A instalação da atualização falhar
        
        Raises:
            Não lança exceções, exceto sys.exit(0) que encerra a aplicação se
            auto_install for True e a instalação for bem-sucedida.
        """
        # Verifica se há uma nova versão disponível
        release_info = self.get_latest_version()
        if not release_info:
            self.logger.warning("Não foi possível verificar atualizações.")
            return False
        
        # Obter a versão
        latest_version = release_info["version"]
        
        # Compara versões
        try:
            if version.parse(latest_version) <= version.parse(self.current_version):
                self.logger.info(f"Nenhuma atualização disponível. Versão atual: {self.current_version}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao comparar versões: {str(e)}")
            Logger.capture_error(e, context={
                "latest_version": latest_version, 
                "current_version": self.current_version
            })
            return False
        
        self.logger.info(f"Nova versão disponível: {latest_version}")
        
        # Se modo silencioso, não pergunta ao usuário
        if not silent:
            user_wants_update = self.prompt_user_for_update(release_info)
            if not user_wants_update:
                self.logger.info("Atualização recusada pelo usuário.")
                return False
        
        # Baixa a atualização
        update_path = self.download_update(release_info)
        if not update_path:
            self.logger.error("Falha ao baixar a atualização.")
            return False
        
        # Instala a atualização se auto_install for True
        if auto_install:
            if self.install_update(update_path):
                self.logger.info("Iniciando nova versão. Encerrando aplicação atual.")
                sys.exit(0)
            else:
                self.logger.error("Falha ao iniciar a nova versão.")
                return False
        
        return True


# Função de conveniência para uso direto
def check_and_update(current_version=None, silent=False, auto_install=True):
    """
    Função de conveniência para verificar e atualizar o software.
    
    Esta função simplifica o uso do UpdaterService, criando uma instância
    temporária e chamando o método check_and_update com os parâmetros fornecidos.
    
    Args:
        current_version (str, optional): Versão atual da aplicação. Default é o valor de settings.
        silent (bool, optional): Se True, não exibe diálogos para o usuário. Default é False.
        auto_install (bool, optional): Se True, instala automaticamente após o download. Default é True.
        
    Returns:
        bool: True se uma atualização foi encontrada e processada com sucesso, False caso contrário.
    
    Exemplo:
        # Verifica e atualiza, mostrando diálogos para o usuário
        if check_and_update():
            # A aplicação será encerrada se uma atualização for instalada
            pass
        else:
            # Continue a execução normal
            print("Nenhuma atualização disponível ou processo não concluído")
    """
    updater = UpdaterService(current_version=current_version)
    return updater.check_and_update(silent=silent, auto_install=auto_install)


if __name__ == "__main__":
    # Exemplo de uso direto
    print(f"Verificando atualizações para {APP_NAME} versão {APP_VERSION}...")
    if check_and_update():
        print("Atualização processada com sucesso.")
    else:
        print("Nenhuma atualização disponível ou o processo foi interrompido.")
