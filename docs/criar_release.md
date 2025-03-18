# Guia para Criar Releases no GitHub

Este guia detalha o processo de criação de uma nova Release no GitHub para o PAMC-ADM, possibilitando o funcionamento do sistema de atualização automática.

## Pré-requisitos

1. Acesso de administrador ao repositório GitHub do projeto
2. Versão compilada do software (.exe)
3. Atualização da versão no arquivo `src/utils/config.py`

## Passo a Passo

### 1. Preparação

1. Certifique-se de que todas as alterações foram concluídas e testadas
2. Atualize a versão no arquivo `src/utils/config.py`:

   ```python
   APP_VERSION = "v1.0.1"  # Altere para a nova versão
   ```

3. Faça commit e push dessas alterações para o repositório

### 2. Compilação

1. Compile o projeto como um arquivo executável (.exe)
2. Nomeie o arquivo de forma descritiva (ex: `pamc-adm-v1.0.1.exe`)

### 3. Criação da Release no GitHub

1. Acesse o repositório no GitHub
2. Clique na aba "Releases" no menu lateral
3. Clique no botão "Draft a new release" (Rascunhar uma nova release)
4. Preencha os campos:
   - **Tag version:** Insira o número da versão, começando com 'v' (ex: `v1.0.1`)
   - **Target:** Selecione a branch principal (geralmente `main` ou `master`)
   - **Release title:** Título descritivo (ex: "PAMC-ADM v1.0.1 - Melhorias na interface")
   - **Description:** Descreva em detalhes as mudanças, novas funcionalidades e correções

### 4. Upload do Executável

1. Na seção "Attach binaries" (ou similar), clique em "Upload a binary"
2. Selecione o arquivo executável compilado
3. Aguarde o upload terminar

### 5. Publicação

1. Verifique se todas as informações estão corretas
2. Clique no botão "Publish release" para publicar

## Notas Importantes

- **Versionamento:** Use [Versionamento Semântico](https://semver.org/lang/pt-BR/):
  - MAJOR.MINOR.PATCH (ex: 1.0.1)
  - Incremente MAJOR para mudanças incompatíveis com versões anteriores
  - Incremente MINOR para adicionar funcionalidades mantendo compatibilidade
  - Incremente PATCH para correções de bugs

- **Notas de Release:** Seja claro e objetivo, liste todas as mudanças importantes para os usuários

- **Executável:** Certifique-se de que o executável funciona corretamente antes de fazer upload

## Verificação

Após publicar a release:

1. Abra uma versão anterior do PAMC-ADM
2. O sistema de atualização automática deve detectar a nova versão
3. O diálogo deve mostrar as notas de versão que você incluiu na descrição

## Solução de Problemas

- **Release não detectada:** Verifique se a tag da versão está no formato correto (começando com 'v')
- **Executável não baixado:** Certifique-se de que o upload foi concluído e o arquivo está acessível publicamente
- **Versão não atualizada:** Confirme que a versão em `config.py` foi alterada e o commit foi enviado 