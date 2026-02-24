# Análise Técnica: Requests vs Playwright para Extração de Dados

## 📊 Situação Atual (Playwright)

### Padrão de Requisições
- **Por preso**: 5 URLs sequenciais
  - Ficha Preso
  - Informes
  - Ficha Carcerária
  - Certidão Carcerária
  - Cadastro

### Tempo de Processamento Atual
- **Navegação**: ~2-3 segundos por URL (domcontentloaded + sleep de 2s)
- **Extração**: ~0.5-1 segundo por URL (localizadores CSS)
- **Total por preso**: ~12-18 segundos
- **Para 1739 presos**: ~6-9 horas (processamento sequencial)

### Recursos Utilizados
- Navegador Chromium completo
- Renderização de JavaScript
- Execução de CSS
- Overhead de automação de browser

---

## 🚀 Proposta: Requests + Paralelização

### Arquitetura Proposta

```
┌─────────────────────────────────────────┐
│  Login (Playwright ou Requests)         │
│  - Obter cookies/sessão                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Pool de Workers (ThreadPoolExecutor)   │
│  - 10-20 workers paralelos              │
│  - Cada worker processa um preso        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Para cada preso (paralelo):            │
│  1. Requisição HTTP GET (requests)      │
│  2. Parse HTML (BeautifulSoup/lxml)    │
│  3. Extração via seletores CSS/XPath   │
│  4. Armazenamento no DataFrame          │
└─────────────────────────────────────────┘
```

### Tempo Estimado com Requests

#### Por Requisição:
- **HTTP GET**: 100-500ms (sem renderização)
- **Parse HTML**: 50-200ms (BeautifulSoup)
- **Extração**: 10-50ms (seletores)
- **Total por URL**: ~160-750ms

#### Com Paralelização (15 workers):
- **5 URLs por preso**: ~0.8-3.75 segundos (sequencial por preso)
- **Com paralelização de presos**: ~0.05-0.25 segundos por preso
- **Para 1739 presos**: ~1.5-7 minutos (vs 6-9 horas atual)

### Ganho de Performance Estimado

| Métrica | Playwright | Requests + Paralelo | Ganho |
|---------|-----------|---------------------|-------|
| Tempo por preso | 12-18s | 0.05-0.25s | **50-360x mais rápido** |
| Tempo total (1739 presos) | 6-9 horas | 1.5-7 min | **50-360x mais rápido** |
| Uso de CPU | Médio | Alto | Mais eficiente |
| Uso de RAM | Alto (~500MB) | Baixo (~50MB) | 10x menos |
| Uso de rede | Alto (renderização) | Baixo (apenas HTML) | 5-10x menos |

---

## ⚖️ Análise de Viabilidade

### ✅ Vantagens do Requests

1. **Performance**
   - 50-360x mais rápido com paralelização
   - Sem overhead de renderização de browser
   - Uso eficiente de recursos

2. **Escalabilidade**
   - Fácil ajustar número de workers
   - Melhor controle de rate limiting
   - Processamento em lote eficiente

3. **Manutenibilidade**
   - Código mais simples
   - Menos dependências (sem Playwright)
   - Mais fácil de debugar

4. **Recursos**
   - Menor uso de RAM
   - Menor uso de CPU (exceto durante paralelização)
   - Sem necessidade de instalar navegadores

### ⚠️ Desafios e Riscos

#### 1. **Autenticação e Sessão**
- **Desafio**: Manter cookies/sessão válidos
- **Solução**: 
  - Usar `requests.Session()` para manter cookies
  - Extrair cookies do Playwright após login
  - Ou fazer login via requests (mais complexo)

#### 2. **Proteções Anti-Bot**
- **Risco**: Sistema pode detectar requests automatizados
- **Indicadores de bot**:
  - User-Agent padrão
  - Falta de headers de browser
  - Muitas requisições simultâneas
  - Padrão de requisições não humano
- **Mitigações**:
  - Headers realistas (User-Agent, Accept, etc.)
  - Delays aleatórios entre requisições
  - Rate limiting inteligente
  - Rotação de User-Agents

#### 3. **JavaScript Dinâmico**
- **Risco**: Se o site renderiza conteúdo via JS, requests não funcionará
- **Análise necessária**: Verificar se as páginas são renderizadas no servidor
- **Solução alternativa**: Usar Selenium/Playwright apenas para páginas JS-heavy

#### 4. **CSRF Tokens**
- **Risco**: Algumas páginas podem exigir tokens CSRF
- **Solução**: Extrair tokens do HTML ou cookies

#### 5. **Seletores CSS**
- **Desafio**: Converter seletores Playwright para BeautifulSoup/lxml
- **Solução**: 
  - BeautifulSoup suporta seletores CSS via `.select()`
  - Ou usar XPath (mais poderoso)

#### 6. **Rate Limiting do Servidor**
- **Risco**: Muitas requisições paralelas podem ser bloqueadas
- **Solução**:
  - Implementar rate limiting (ex: 10-20 req/s)
  - Retry com backoff exponencial
  - Detecção de bloqueios (429, 403)

---

## 🔧 Implementação Técnica

### Estrutura Proposta

```python
# Exemplo conceitual (não implementar ainda)

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ExtratorRequests:
    def __init__(self, cookies_do_playwright):
        self.session = requests.Session()
        self.session.cookies.update(cookies_do_playwright)
        # Configurar headers realistas
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0...',
            'Accept': 'text/html,application/xhtml+xml...',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Referer': 'https://canaime.com.br/...'
        })
        
    def extrair_dados_preso(self, codigo):
        """Extrai dados de um preso usando requests"""
        dados = {}
        
        for url_base in LISTA_URLS_INFO_PRESO:
            url = url_base + codigo
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrair campos usando seletores CSS
            for campo, seletor in LOCALIZADORES[url_base].items():
                elemento = soup.select_one(seletor)
                dados[campo] = elemento.text.strip() if elemento else ""
        
        return dados
    
    def processar_presos_paralelo(self, codigos, max_workers=15):
        """Processa múltiplos presos em paralelo"""
        resultados = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.extrair_dados_preso, codigo): codigo 
                for codigo in codigos
            }
            
            for future in as_completed(futures):
                codigo = futures[future]
                try:
                    resultados[codigo] = future.result()
                except Exception as e:
                    print(f"Erro ao processar {codigo}: {e}")
        
        return resultados
```

### Conversão de Seletores

**Playwright**:
```python
page.locator('tr:nth-child(5) .titulobk:nth-child(2)')
```

**BeautifulSoup**:
```python
soup.select_one('tr:nth-child(5) .titulobk:nth-child(2)')
```
✅ **Compatível** - BeautifulSoup suporta seletores CSS similares

---

## 📈 Estimativa de Ganho Real

### Cenário Conservador (10 workers, rate limit)
- **Tempo por preso**: ~0.2-0.5s
- **Tempo total (1739 presos)**: ~6-15 minutos
- **Ganho**: **24-90x mais rápido**

### Cenário Otimista (20 workers, sem rate limit)
- **Tempo por preso**: ~0.05-0.15s
- **Tempo total (1739 presos)**: ~1.5-4 minutos
- **Ganho**: **90-360x mais rápido**

### Considerações
- **Rate limiting**: Pode reduzir ganho para 10-30x
- **Proteções anti-bot**: Pode exigir delays, reduzindo para 5-15x
- **Overhead de paralelização**: Threading tem overhead, mas ainda muito melhor

---

## 🎯 Recomendação

### ✅ **VIÁVEL e RECOMENDADO** com ressalvas:

#### Implementação Híbrida (Melhor Abordagem):

1. **Login**: Manter Playwright (já funciona)
   - Extrair cookies após login
   - Passar cookies para sessão requests

2. **Extração**: Migrar para Requests + Paralelização
   - Ganho de 10-50x mesmo com rate limiting
   - Muito mais eficiente

3. **Fallback**: Manter Playwright como backup
   - Se requests falhar (anti-bot, JS necessário)
   - Usar Playwright apenas quando necessário

#### Estratégia de Implementação:

**Fase 1 - Prova de Conceito** (1-2 dias):
- Implementar extrator básico com requests
- Testar com 10-20 presos
- Validar extração de dados
- Verificar se há proteções anti-bot

**Fase 2 - Otimização** (2-3 dias):
- Implementar paralelização
- Adicionar rate limiting
- Headers realistas
- Tratamento de erros robusto

**Fase 3 - Produção** (1-2 dias):
- Integrar com código existente
- Manter fallback para Playwright
- Testes completos
- Documentação

---

## ⚠️ Riscos a Considerar

### Alto Risco
1. **Detecção de Bot**: Sistema pode bloquear muitas requisições simultâneas
2. **Mudanças no Site**: Seletores podem quebrar se HTML mudar
3. **JavaScript Necessário**: Se conteúdo for renderizado via JS, requests não funcionará

### Médio Risco
1. **CSRF Tokens**: Pode exigir extração adicional
2. **Rate Limiting**: Pode exigir ajustes de velocidade
3. **Sessão Expirada**: Cookies podem expirar durante processamento longo

### Baixo Risco
1. **Conversão de Seletores**: BeautifulSoup suporta CSS similar
2. **Parsing HTML**: Bibliotecas maduras e confiáveis
3. **Tratamento de Erros**: Padrões bem estabelecidos

---

## 💡 Conclusão

### Viabilidade: **ALTA** ✅

**Ganho estimado**: 10-50x mais rápido (mesmo com rate limiting conservador)

**Esforço de implementação**: Médio (3-7 dias)

**Risco**: Médio (mitigável com fallback para Playwright)

### Recomendação Final:

**Implementar versão híbrida:**
- Login via Playwright (já funciona)
- Extração via Requests + Paralelização (ganho massivo)
- Fallback automático para Playwright se requests falhar

**Benefícios:**
- Performance 10-50x melhor
- Menor uso de recursos
- Código mais simples
- Mantém robustez (fallback)

**Próximos Passos:**
1. Criar POC (Proof of Concept) com 10-20 presos
2. Validar se funciona sem proteções anti-bot
3. Se funcionar, implementar versão completa
4. Se não funcionar, manter Playwright atual

---

## 📝 Notas Técnicas

### Bibliotecas Necessárias
- `requests`: HTTP client
- `beautifulsoup4`: Parsing HTML
- `lxml`: Parser rápido (opcional, mais rápido que html.parser)
- `concurrent.futures`: Paralelização

### Exemplo de Conversão de Seletor

**Atual (Playwright)**:
```python
elementos = page.locator('tr:nth-child(5) .titulobk:nth-child(2)')
texto = elementos.first.text_content()
```

**Proposto (BeautifulSoup)**:
```python
elemento = soup.select_one('tr:nth-child(5) .titulobk:nth-child(2)')
texto = elemento.get_text(strip=True) if elemento else ""
```

### Headers Realistas
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Referer': 'https://canaime.com.br/sgp2rr/areas/index_areas.php'
}
```

---

**Data da Análise**: 2025-01-XX
**Autor**: Análise Técnica - PAMC-ADM
**Versão**: 1.0

