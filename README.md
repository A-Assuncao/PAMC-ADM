# PAMC-ADM

<p align="center">
  <img src="assets/icone.ico" alt="PAMC-ADM Logo" width="120"/>
</p>

**PAMC-ADM** é um sistema avançado para extração e processamento de dados de presos do sistema Canaimé, utilizando a biblioteca Playwright para automação de navegação web. Os dados são organizados e exportados para um arquivo Excel estruturado, facilitando a análise e gestão das informações prisionais.

## Sumário

- [Principais Recursos](#principais-recursos)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Como Executar](#como-executar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Interface do Usuário](#interface-do-usuário)
- [Opções de Desenvolvedor](#opções-de-desenvolvedor)
- [Sistema de Atualização](#sistema-de-atualização)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Principais Recursos

- 🖥️ **Interface Gráfica Moderna** - Seleção intuitiva de unidades prisionais com interface amigável
- 🔄 **Processamento Otimizado** - Algoritmo eficiente que visita cada URL apenas uma vez por detento
- 📊 **Exportação Estruturada** - Geração de planilha Excel com abas por unidade e consolidado
- 📋 **Dados Formatados** - Tratamento automático de datas, cálculo de idade e limpeza de campos
- 🔍 **Rastreamento em Tempo Real** - Acompanhamento detalhado do progresso durante a extração
- ⚙️ **Modo de Teste** - Opção para processar número limitado de registros para validação
- 🔧 **Opções Configuráveis** - Personalização da experiência conforme necessidade do usuário
- 🔄 **Atualização Automática** - Sistema integrado de verificação e instalação de novas versões

## Requisitos

- [Python 3.8+](https://www.python.org/) (recomendado Python 3.10 ou superior)
- [Playwright](https://playwright.dev/python/) para automação de navegador
- [Pandas](https://pandas.pydata.org/) para manipulação de dados
- [Openpyxl](https://openpyxl.readthedocs.io/) para geração de arquivos Excel
- [Login-Canaime](https://github.com/A-Assuncao/login-canaime) para autenticação no sistema Canaimé
- [Requests](https://requests.readthedocs.io/) para o sistema de atualização automática
- [Packaging](https://packaging.pypa.io/) para comparação de versões

## Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/PAMC-ADM.git
   cd PAMC-ADM
   ```

2. **Crie e ative um ambiente virtual**:
   ```bash
   python -m venv .venv
   
   # No Windows
   .venv\Scripts\activate
   
   # No Linux/Mac
   source .venv/bin/activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instale o Playwright e os navegadores necessários**:
   ```bash
   playwright install
   ```

## Como Executar

Execute o script principal para iniciar o programa:

```bash
python run.py
```

O aplicativo irá:

1. Apresentar uma interface gráfica para seleção das unidades prisionais
2. Permitir configurar opções de desenvolvedor (modo de teste com 5 ou 10 cadastros por unidade)
3. Realizar a autenticação no sistema Canaimé através da biblioteca login-canaime
4. Extrair os dados dos presos das unidades selecionadas
5. Processar e formatar os dados coletados
6. Exportar os resultados para um arquivo Excel organizado

O título da janela exibe a versão do sistema (ex.: *Sistema de Extração de Dados Prisionais — v1.0.0*).

Para instruções detalhadas de uso, consulte o [Guia de Utilização](docs/README.md).

## Estrutura do Projeto

```
📦 PAMC-ADM/
├── 🚀 run.py                       # Ponto de entrada do aplicativo
├── 📂 src/                         # Código-fonte principal
│   ├── 📄 main.py                  # Função principal e orquestração
│   ├── 📂 core/                    # Lógica de negócio principal
│   │   ├── 📄 listar_presos_up.py  # Processamento de dados dos presos
│   │   └── 📄 __init__.py
│   ├── 📂 ui/                      # Interface de usuário
│   │   ├── 📄 interface_selecao.py # Interface gráfica Tkinter
│   │   └── 📄 __init__.py
│   ├── 📂 utils/                   # Utilitários
│   │   ├── 📄 config.py            # Configurações e constantes
│   │   └── 📄 __init__.py
│   └── 📄 __init__.py
├── 📂 tests/                       # Testes automatizados
└── 📄 README.md                    # Documentação
```

## Funcionalidades

### Extração de Dados

O sistema extrai uma ampla gama de informações dos presos, incluindo:

- **Identificação e localização**: UP, ala, cela, código, link de cadastro (Ficha_Menu), foto (URL completa)
- **Dados Pessoais**: Nome, vulgo, data de nascimento, filiação, documentos (CPF, RG), sexo, altura, cor/etnia
- **Informações Socioeconômicas**: Estado civil, filhos, escolaridade, profissão, religião
- **RJI e Biometria**: Número RJI (suporta hífens) e status da biometria (Coletada/Não coletada), incluindo o caso em que não há número de RJI mas consta "POSSUI BIOMETRIA"
- **Informações Prisionais e processuais**: Conduta, regime, sentença, crimes, artigos, processos, datas, último lançamento

### Processamento de Dados

O sistema aplica automaticamente diversos tratamentos aos dados extraídos:

- **Formatação de Datas**: Padronização para o formato DD/MM/AAAA
- **Cálculo de Idade**: Com base na data de nascimento
- **Extração de Ala e Cela**: Processamento correto de informações de localização
- **Limpeza de Campos**: Remoção de prefixos e sufixos desnecessários
- **Ordenação Inteligente**: Organização lógica dos registros

### Exportação Excel

O resultado final é exportado em um arquivo Excel bem estruturado:

- **Abas por Unidade**: Cada unidade prisional tem sua própria aba (sem coluna UP na aba da unidade)
- **Aba Consolidada**: Reúne todos os dados em uma única visualização
- **Ordem fixa de colunas**: RJI e BIOMETRIA logo após as informações pessoais; coluna **ÚLTIMO LANÇAMENTO** sempre na última posição
- **Coluna CADASTRO**: Link direto para a ficha do preso (`Ficha_Menu.php?id_cad_preso={código}`)
- **Coluna FOTO**: URL completa da foto (ex.: `https://canaime.com.br/sgp2rr/fotos/presos/...`)
- **Ordenação**: Registros ordenados por ala, cela e nome

## Interface do Usuário

O sistema apresenta uma interface gráfica moderna e intuitiva construída com Tkinter:

- **Seleção de Unidades**: Checkboxes para cada unidade prisional
- **Barra de Progresso**: Visualização em tempo real do andamento
- **Log em Tempo Real**: Acompanhamento detalhado das operações
- **Botões de Ação**: Controles claros para iniciar e cancelar o processamento
- **Fechamento gracioso**: Ao fechar a janela, o sistema aguarda a finalização da extração em andamento (se houver) e encerra o navegador corretamente, evitando erros ao sair

## Opções de Desenvolvedor

Na interface, o painel **Opções de Desenvolvedor** permite:

- **Modo de Teste**: Limita o processamento a 5 ou 10 cadastros por unidade (ideal para validar o sistema sem rodar a extração completa). Em modo teste, o Excel existente não é carregado, de modo que o arquivo gerado contém apenas os registros processados nessa execução.
- **Selecionar Unidades**: Escolher quais unidades prisionais processar

## Sistema de Atualização

O PAMC-ADM inclui um sistema de atualização automática que verifica a existência de novas versões no repositório GitHub e permite a atualização com apenas um clique.

Para criar uma nova release:
- Atualize a versão no arquivo `src/utils/config.py`
- Compile o executável atualizado
- Crie uma Release no GitHub adicionando um título e descrição detalhada das mudanças
- Faça upload do executável e publique a release

Para mais detalhes sobre as mudanças entre versões, consulte o [CHANGELOG](CHANGELOG.md).

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Abrir _Issues_ reportando bugs ou sugerindo melhorias
2. Enviar _Pull Requests_ com correções ou novas funcionalidades
3. Melhorar a documentação ou adicionar testes

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE) - veja o arquivo LICENSE para detalhes.

---

**Desenvolvido com ♥ e Python.** 