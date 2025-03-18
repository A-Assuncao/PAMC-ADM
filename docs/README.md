# Guia de Utilização do PAMC-ADM v1.0.0

<p align="center">
  <img src="../assets/icone.ico" alt="PAMC-ADM Logo" width="120"/>
</p>

Este guia apresenta as funcionalidades e instruções detalhadas para utilização do sistema PAMC-ADM, uma ferramenta projetada para extração e processamento de dados de presos do sistema Canaimé.

## Sumário

- [Visão Geral](#visão-geral)
- [Primeiros Passos](#primeiros-passos)
- [Interface Principal](#interface-principal)
- [Seleção de Unidades](#seleção-de-unidades)
- [Opções de Execução](#opções-de-execução)
- [Processo de Extração](#processo-de-extração)
- [Relatório Excel](#relatório-excel)
- [Atualizações](#atualizações)
- [Solução de Problemas](#solução-de-problemas)

## Visão Geral

O PAMC-ADM é um sistema de extração de dados que permite coletar informações detalhadas dos presos registrados no sistema Canaimé. A ferramenta automatiza o processo que normalmente seria feito manualmente, poupando tempo e reduzindo erros.

<p align="center">
  <img src="img/visao_geral.png" alt="Visão Geral do PAMC-ADM" width="650"/>
  <br><small><i>Figura 1: Visão geral da aplicação PAMC-ADM</i></small>
</p>

**Principais recursos:**
- Extração automática de dados de presos
- Processamento inteligente de informações
- Formatação e padronização dos dados
- Geração de relatórios estruturados em Excel
- Interface gráfica intuitiva

## Primeiros Passos

### Requisitos do Sistema

- Windows 7 ou superior
- Conexão com a rede onde o sistema Canaimé está disponível
- Credenciais de acesso válidas ao sistema Canaimé

### Inicialização do Programa

1. Execute o arquivo `PAMC-ADM.exe` (ou através do comando `python run.py` se estiver usando a versão de desenvolvimento)
2. O sistema verificará automaticamente se existem atualizações disponíveis

<p align="center">
  <img src="img/verificacao_atualizacao.png" alt="Verificação de Atualizações" width="500"/>
  <br><small><i>Figura 2: Tela de verificação de atualizações</i></small>
</p>

3. A interface principal será exibida após a verificação de atualizações

## Interface Principal

A interface do PAMC-ADM é composta pelos seguintes elementos:

<p align="center">
  <img src="img/interface_principal.png" alt="Interface Principal" width="700"/>
  <br><small><i>Figura 3: Interface principal com seus principais componentes</i></small>
</p>

1. **Cabeçalho**: Título e subtítulo do sistema
2. **Painel de Seleção de Unidades**: Lista de unidades prisionais disponíveis
3. **Painel de Opções**: Configurações para a execução
4. **Barra de Progresso**: Exibe o andamento da extração
5. **Área de Log**: Mostra mensagens detalhadas sobre o processo
6. **Botões de Ação**: Iniciar, Cancelar e outras opções

## Seleção de Unidades

### Unidades Disponíveis

O sistema oferece acesso às seguintes unidades prisionais:
- **PAMC**: Penitenciária Agrícola do Monte Cristo
- **CPBV**: Cadeia Pública Masculina de Boa Vista
- **CPFBV**: Cadeia Pública Feminina de Boa Vista
- **CPP**: Centro de Progressão Penitenciária
- **CABV**: Casa do Albergado de Boa Vista
- **UPRRO**: Unidade Prisional de Rorainópolis
- **CME**: Central de Monitoração Eletrônica
- **DICAP**: Divisão de Inteligência e Captura

<p align="center">
  <img src="img/selecao_unidades.png" alt="Seleção de Unidades" width="600"/>
  <br><small><i>Figura 4: Painel de seleção de unidades prisionais</i></small>
</p>

### Como Selecionar

1. Marque as caixas de seleção (checkboxes) correspondentes às unidades das quais deseja extrair dados
2. Utilize os botões "Selecionar Todos" ou "Limpar Seleção" para agilizar o processo
3. É possível selecionar qualquer combinação de unidades para extração simultânea

## Opções de Execução

<p align="center">
  <img src="img/opcoes_execucao.png" alt="Opções de Execução" width="550"/>
  <br><small><i>Figura 5: Painel de opções de execução</i></small>
</p>

### Modo de Teste

- **Ativar modo de teste**: Limita o número de registros processados para verificar o funcionamento
- **5 cadastros por unidade**: Processa apenas 5 registros de cada unidade selecionada
- **10 cadastros por unidade**: Processa até 10 registros de cada unidade selecionada

O modo de teste é útil para:
- Verificar se o sistema está funcionando corretamente
- Validar a formatação do relatório sem esperar o processamento completo
- Testar diferentes configurações rapidamente

### Visualização do Navegador

- **Mostrar navegador**: Quando marcada, esta opção exibe o navegador durante a automação

<p align="center">
  <img src="img/navegador_visivel.png" alt="Navegador Visível" width="600"/>
  <br><small><i>Figura 6: Exemplo do navegador sendo exibido durante a automação</i></small>
</p>

- Quando não marcada, o processo ocorre em segundo plano (headless)

Recomendações:
- Mostre o navegador quando estiver aprendendo a usar o sistema ou para depuração
- Deixe desmarcado para operação normal, aumentando a velocidade do processamento

## Processo de Extração

### Iniciar a Extração

1. Selecione as unidades desejadas
2. Configure as opções de execução conforme necessário
3. Clique no botão "Processar Selecionados"

<p align="center">
  <img src="img/botao_processar.png" alt="Botão Processar" width="300"/>
  <br><small><i>Figura 7: Botão para iniciar o processamento</i></small>
</p>

4. Informe suas credenciais do sistema Canaimé quando solicitado

<p align="center">
  <img src="img/tela_login.png" alt="Tela de Login" width="450"/>
  <br><small><i>Figura 8: Tela de login no sistema Canaimé</i></small>
</p>

5. Aguarde o processo de login e extração

### Monitoramento do Progresso

<p align="center">
  <img src="img/progresso_extracao.png" alt="Progresso da Extração" width="650"/>
  <br><small><i>Figura 9: Interface exibindo o progresso da extração</i></small>
</p>

Durante a extração, você poderá acompanhar:
- Percentual de conclusão na barra de progresso
- Detalhes das operações na área de log
- Informações sobre os presos sendo processados
- Eventuais erros ou avisos

### Cancelamento

Para interromper o processo a qualquer momento:
1. Clique no botão "Cancelar"

<p align="center">
  <img src="img/botao_cancelar.png" alt="Botão Cancelar" width="300"/>
  <br><small><i>Figura 10: Botão para cancelar o processamento</i></small>
</p>

2. O sistema finalizará o processamento atual e encerrará de forma segura
3. Os dados já coletados serão preservados no relatório

## Relatório Excel

### Estrutura do Relatório

<p align="center">
  <img src="img/abas_excel.png" alt="Abas do Excel" width="700"/>
  <br><small><i>Figura 11: Exemplo das abas do relatório Excel gerado</i></small>
</p>

O arquivo Excel gerado contém as seguintes abas:
1. Uma aba para cada unidade prisional processada
2. Uma aba "Consolidado" com todos os registros

<p align="center">
  <img src="img/estrutura_relatorio.png" alt="Estrutura do Relatório" width="750"/>
  <br><small><i>Figura 12: Exemplo da estrutura do relatório Excel</i></small>
</p>

Cada aba contém colunas organizadas nas seguintes categorias:
- **Identificação e Localização**: UP, ALA, CELA, CÓDIGO, FOTO
- **Dados Pessoais**: NOME, VULGO, SEXO, DATA NASC., IDADE, etc.
- **Filiação**: MÃE, PAI
- **Endereço**: ENDEREÇO, CIDADE, ESTADO, PAÍS
- **Informações Socioeconômicas**: ESTADO CIVIL, QTD FILHOS, etc.
- **Dados Criminais**: CONDUTA, CRIME, ARTIGO, PROCESSO, etc.

### Características Especiais

- As datas são formatadas no padrão DD/MM/AAAA
- A idade é calculada automaticamente a partir da data de nascimento
- Os campos CPF e MÃE têm os prefixos removidos
- As informações de ALA e CELA são extraídas corretamente
- Os registros são ordenados por ALA, CELA e NOME para fácil localização

### Localização do Arquivo

<p align="center">
  <img src="img/caminho_arquivo.png" alt="Caminho do Arquivo" width="650"/>
  <br><small><i>Figura 13: Mensagem indicando o caminho do arquivo gerado</i></small>
</p>

Ao final do processamento, o sistema informará o caminho completo onde o arquivo Excel foi salvo. Por padrão, o arquivo será nomeado com data e hora da extração.

## Atualizações

### Verificação de Atualizações

O sistema verifica automaticamente por novas versões ao ser iniciado. Quando uma atualização estiver disponível:

<p align="center">
  <img src="img/dialogo_atualizacao.png" alt="Diálogo de Atualização" width="500"/>
  <br><small><i>Figura 14: Diálogo informando sobre nova versão disponível</i></small>
</p>

1. Um diálogo será exibido informando sobre a nova versão
2. As notas da versão serão apresentadas com as melhorias e correções
3. Você poderá escolher atualizar imediatamente ou continuar na versão atual

### Processo de Atualização

Se optar por atualizar:
1. O sistema baixará automaticamente o novo instalador

<p align="center">
  <img src="img/download_atualizacao.png" alt="Download da Atualização" width="550"/>
  <br><small><i>Figura 15: Progresso do download da atualização</i></small>
</p>

2. O instalador será executado ao término do download
3. Siga as instruções do instalador para concluir a atualização
4. Inicie o PAMC-ADM normalmente após a atualização

## Solução de Problemas

### Erros Comuns

| Problema | Possível Causa | Solução |
|----------|----------------|---------|
| Falha na autenticação | Credenciais incorretas ou problemas no Canaimé | Verifique suas credenciais e se o sistema Canaimé está acessível |
| Erro na extração de dados | Mudanças na estrutura das páginas do Canaimé | Verifique se está usando a versão mais recente do PAMC-ADM |
| Lentidão excessiva | Problemas de conexão ou alto volume de dados | Reduza o número de unidades processadas simultaneamente |
| Arquivo Excel não gerado | Erros durante o processamento | Verifique as mensagens de erro no log e tente novamente |

<p align="center">
  <img src="img/mensagem_erro.png" alt="Mensagem de Erro" width="600"/>
  <br><small><i>Figura 16: Exemplo de mensagem de erro</i></small>
</p>

### Suporte

Para problemas não cobertos neste guia, entre em contato com o suporte técnico ou abra uma issue no repositório GitHub do projeto:
[https://github.com/A-Assuncao/PAMC-ADM/issues](https://github.com/A-Assuncao/PAMC-ADM/issues)

---

**Desenvolvido com ♥ para otimizar os processos de gestão prisional** 