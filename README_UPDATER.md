# Sistema de Atualização Automática

## Visão Geral

O `UpdaterService` é um componente responsável por gerenciar o processo de verificação, download e instalação de atualizações de software. Ele foi projetado seguindo os princípios SOLID para ser facilmente reutilizável em diferentes projetos.

## Características Principais

- ✅ Verificação automática de novas versões
- ✅ Download de arquivos de atualização
- ✅ Prompt interativo para o usuário aceitar ou recusar atualizações
- ✅ Instalação automática de atualizações
- ✅ Integração completa com o sistema de logging
- ✅ Configurável através de variáveis de ambiente

## Requisitos

- Python 3.7+
- Bibliotecas: `requests`, `packaging`, `tkinter`
- Arquivo de configuração `.env` com as variáveis necessárias

## Instalação

```bash
pip install requests packaging
```

## Configuração

O serviço de atualização pode ser configurado através do arquivo `.env` na raiz do projeto:

```
# Configurações de atualização
APP_NAME=NomeDoAplicativo
APP_VERSION=v1.0.0
UPDATE_URL=https://exemplo.com/atualizacoes/
VERSION_FILE=latest_version.txt
```

### Variáveis de Configuração

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `APP_NAME` | Nome da aplicação | "Aplicação" |
| `APP_VERSION` | Versão atual da aplicação | "v0.0.0" |
| `UPDATE_URL` | URL base para verificação de atualizações | "" |
| `VERSION_FILE` | Nome do arquivo que contém a versão mais recente | "latest_version.txt" |

## Estrutura do Servidor de Atualizações

O serviço espera uma estrutura específica no servidor de atualizações:

1. Um arquivo de texto (por padrão, `latest_version.txt`) contendo a versão mais recente (ex: `v1.0.1`)
2. Arquivos de instalação nomeados no formato: `nome-do-aplicativo-vX.Y.Z.exe` (ex: `nomedoaplicativo-v1.0.1.exe`)

Exemplo da estrutura do servidor:
```
/atualizacoes/
  ├── latest_version.txt    # Contém "v1.0.1"
  ├── nomedoaplicativo-v1.0.0.exe
  └── nomedoaplicativo-v1.0.1.exe
```

## Uso Básico

### Verificação e Atualização Simples

```python
from src.utils.updater import check_and_update

# Verifica se há atualizações e, se houver, permite que o usuário atualize
check_and_update()
```

### Usando a Classe UpdaterService

```python
from src.utils.updater import UpdaterService

# Inicializa o serviço de atualização
updater = UpdaterService(
    app_name="Meu Aplicativo",
    current_version="v1.0.0",
    update_url="https://meuservidor.com/atualizacoes/",
    version_file="versao.txt"
)

# Verifica por atualizações
latest_version = updater.get_latest_version()
if latest_version:
    print(f"Versão mais recente: {latest_version}")
    
    # Baixa a atualização
    update_path = updater.download_update(latest_version)
    if update_path:
        print(f"Atualização baixada em: {update_path}")
        
        # Pergunta ao usuário se deseja atualizar
        if updater.prompt_user_for_update(latest_version):
            # Instala a atualização
            updater.install_update(update_path)
```

### Verificação Silenciosa

```python
from src.utils.updater import check_and_update

# Verifica e atualiza sem mostrar diálogos para o usuário
check_and_update(silent=True)
```

### Download Sem Instalação Automática

```python
from src.utils.updater import check_and_update

# Baixa a atualização, mas não instala automaticamente
check_and_update(auto_install=False)
```

## Referência da API

### Classe UpdaterService

#### `__init__(app_name=None, current_version=None, update_url=None, version_file=None)`

Inicializa o serviço de atualização.

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `app_name` | str | Nome da aplicação | Valor de `APP_NAME` |
| `current_version` | str | Versão atual da aplicação | Valor de `APP_VERSION` |
| `update_url` | str | URL base para verificação de atualizações | Valor de `UPDATE_URL` |
| `version_file` | str | Nome do arquivo que contém a versão mais recente | `"latest_version.txt"` |

#### `get_latest_version()`

Obtém a versão mais recente disponível no servidor.

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Versão mais recente | str | A versão mais recente disponível |
| Falha | None | Retorna None em caso de falha |

#### `download_update(latest_version, target_path=None)`

Baixa o arquivo de atualização.

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `latest_version` | str | Versão a ser baixada | - |
| `target_path` | str | Caminho onde salvar o arquivo | Diretório atual |

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Caminho do arquivo | str | Caminho completo do arquivo baixado |
| Falha | None | Retorna None em caso de falha |

#### `prompt_user_for_update(latest_version)`

Pergunta ao usuário se deseja atualizar.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `latest_version` | str | Versão disponível para atualização |

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Resposta do usuário | bool | `True` se aceitar, `False` se recusar |

#### `install_update(update_path)`

Instala a atualização baixada.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `update_path` | str | Caminho para o arquivo de atualização |

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Sucesso | bool | `True` se a instalação iniciou com sucesso |

#### `check_and_update(silent=False, auto_install=True)`

Verifica por atualizações e, se disponível, permite que o usuário escolha se deseja atualizar.

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `silent` | bool | Se `True`, não exibe diálogos para o usuário | `False` |
| `auto_install` | bool | Se `True`, instala automaticamente após o download | `True` |

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Resultado | bool | `True` se uma atualização foi processada |

### Função check_and_update

#### `check_and_update(current_version=None, silent=False, auto_install=True)`

Função de conveniência para verificar e atualizar o software.

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `current_version` | str | Versão atual da aplicação | Valor de `APP_VERSION` |
| `silent` | bool | Se `True`, não exibe diálogos para o usuário | `False` |
| `auto_install` | bool | Se `True`, instala automaticamente após o download | `True` |

| Retorno | Tipo | Descrição |
|---------|------|-----------|
| Resultado | bool | `True` se uma atualização foi processada |

## Fluxo de Atualização

O processo de atualização segue um fluxo bem definido, desde a verificação até a instalação.

Para uma representação visual completa do fluxo de atualização, consulte [docs/updater_flow.md](docs/updater_flow.md), que inclui:

- Diagrama de sequência Mermaid detalhando todas as interações
- Descrição passo a passo do processo de atualização
- Explicação dos diferentes modos de operação

## Tratamento de Erros

O serviço de atualização trata diversos cenários de erro:

- Falha na conexão com o servidor
- Arquivo de versão indisponível
- Formato de versão inválido
- Falha no download da atualização
- Erro de permissão ao salvar o arquivo
- Falha ao iniciar o instalador

Todos os erros são registrados pelo sistema de logging da aplicação para facilitar a solução de problemas.

## Casos de Uso Avançados

### Implementação de uma Política de Atualização Personalizada

```python
from src.utils.updater import UpdaterService
from packaging import version

class CustomUpdater(UpdaterService):
    def should_update(self, latest_version):
        # Política personalizada: só atualiza se a diferença for significativa
        current = version.parse(self.current_version)
        latest = version.parse(latest_version)
        
        # Só atualiza se a versão principal (major) ou secundária (minor) mudou
        if latest.major > current.major or latest.minor > current.minor:
            return True
        return False
    
    def check_and_update(self, silent=False, auto_install=True):
        latest_version = self.get_latest_version()
        if not latest_version:
            return False
            
        if not self.should_update(latest_version):
            return False
            
        # Continua com o processo de atualização...
        # Resto da implementação similar ao método original
```

### Cronograma de Verificação de Atualizações

```python
import schedule
import time
from src.utils.updater import check_and_update

def setup_update_schedule():
    # Verifica atualizações diariamente às 9h
    schedule.every().day.at("09:00").do(check_and_update, silent=True)
    
    # Executa em uma thread separada
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
```

## Extensões Possíveis

- Implementação de canais de atualização (estável, beta, nightly)
- Suporte a atualizações incrementais/delta
- Verificação de integridade de arquivos (checksum)
- Suporte a rollback automático em caso de falha
- Integração com outros mecanismos de instalação (MSI, AppImage, etc.)

## Boas Práticas

1. **Sempre informe claramente ao usuário**:
   - Quais mudanças estão incluídas na atualização
   - O tamanho aproximado do download
   - O impacto da atualização (ex: necessidade de reiniciar)

2. **Forneça opções para o usuário**:
   - Permitir adiar a atualização
   - Opção para desativar verificações automáticas
   - Possibilidade de fazer backup antes da atualização

3. **Segurança**:
   - Implemente verificação de integridade dos arquivos baixados
   - Use HTTPS para o servidor de atualizações
   - Considere assinar digitalmente os pacotes de atualização

4. **Resiliência**:
   - Implemente mecanismos de retry para downloads interrompidos
   - Permita retomar downloads parciais
   - Garanta que a aplicação possa se recuperar de uma atualização mal-sucedida

## Solução de Problemas

### Erros Comuns

| Problema | Possível Causa | Solução |
|----------|-----------------|---------|
| `Não foi possível verificar atualizações` | URL de atualização não configurada ou servidor inacessível | Verifique a configuração `UPDATE_URL` e a conectividade com o servidor |
| `Falha ao baixar a atualização` | Arquivo não encontrado no servidor ou problemas de rede | Confirme se o arquivo existe no servidor e com o nome correto |
| `Falha ao iniciar a nova versão` | Permissões insuficientes ou arquivo corrompido | Verifique as permissões do arquivo baixado e tente baixar novamente |

### Logs para Diagnóstico

Para diagnosticar problemas, verifique os logs da aplicação:

```python
from src.utils.logger import Logger

# Configurar o logger para modo debug
logger = Logger.get_logger(level="DEBUG")

# Agora utilize o updater normalmente
from src.utils.updater import check_and_update
check_and_update()
``` 