# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não Lançado]

## [1.1.0] - 23-02-2026

### Adicionado
- Coluna **CADASTRO** no Excel: link para a ficha do preso (`Ficha_Menu.php?id_cad_preso={código}`), posicionada logo antes da coluna FOTO
- Função `reordenar_colunas_excel()` para garantir ordem fixa das colunas na exportação
- Múltiplos seletores alternativos para extração do campo RJI na Ficha Preso (`RJI_SELETORES_ALTERNATIVOS`), incluindo fallback pela primeira tabela
- Função `extrair_rji_ficha(page)` para extração robusta do RJI com tentativa de vários seletores
- Tratamento do caso em que não há número de RJI mas consta "POSSUI BIOMETRIA": biometria marcada como "Coletada"
- Versão do sistema exibida dinamicamente no título da janela (ex.: *Sistema de Extração de Dados Prisionais — v1.1.0*)
- Fechamento gracioso da janela: handler `WM_DELETE_WINDOW` que aguarda o término da extração em andamento antes de encerrar, evitando erro EPIPE do Playwright

### Alterado
- **Opções de Execução** renomeado para **Opções de Desenvolvedor** na interface
- Removida a opção "Mostrar navegador durante execução" e todo o código relacionado (navegador sempre em modo headless)
- Coluna **BIOMETRIA COLETADA** renomeada para **BIOMETRIA**
- Ordem das colunas no Excel: RJI e BIOMETRIA logo após as informações pessoais/socioeconômicas; **ÚLTIMO LANÇAMENTO** sempre como última coluna
- Modo teste: em execuções de teste não é carregado o Excel existente, de modo que o arquivo gerado contém apenas os 5 ou 10 registros por unidade processados nessa execução
- Modo teste: limite de presos aplicado antes do filtro por existentes (primeiros N da página por unidade), garantindo o respeito ao limite escolhido
- Parser do RJI (`parsear_rji_biometria`): suporte a número RJI com hífens; sem número mas com texto "POSSUI BIOMETRIA" (ou similar) retorna biometria "Coletada"
- Coluna **FOTO** no Excel passou a armazenar URL completa da imagem (ex.: `https://canaime.com.br/sgp2rr/fotos/presos/arquivo.jpg`) em vez de caminho relativo
- Seletor do **VULGO** na Ficha Preso atualizado para `tr:nth-child(5) .titulobk` (antes `tr:nth-child(4)`)

### Corrigido
- Aviso FutureWarning do pandas no `concat`: uso de `sort=False` e concatenação apenas quando há registros (`len(df_presos) > 0`)
- Modo teste passando a limitar corretamente a 5 ou 10 cadastros por unidade (limite aplicado à lista da página antes do filtro por existentes)
- Captura do RJI e da biometria em mais cenários (seletores alternativos e fallback; texto sem número com "POSSUI BIOMETRIA")
- Erro **EPIPE (broken pipe)** ao fechar o aplicativo: fechamento do navegador/Playwright em bloco `finally` após a extração e handler de fechamento da janela para encerramento gracioso

## [1.0.0] - 20-12-2023

### Adicionado
- Interface gráfica para seleção de unidades prisionais
- Painel de opções com modo de teste e visibilidade do navegador
- Extração automática de dados do sistema Canaimé
- Formatação de datas no padrão DD/MM/AAAA
- Cálculo automático de idade a partir da data de nascimento
- Tratamento de campos CPF e MÃE (removendo prefixos)
- Limpeza do campo "SENTENÇA DIAS" (removendo sufixo)
- Exportação para Excel com abas por unidade e consolidado
- Sistema de atualização automática via GitHub

## Como interpretar as versões

As versões seguem o padrão MAJOR.MINOR.PATCH, onde:
- MAJOR: Mudanças incompatíveis com versões anteriores
- MINOR: Adição de funcionalidades mantendo compatibilidade
- PATCH: Correções de bugs mantendo compatibilidade
