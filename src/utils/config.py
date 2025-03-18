# Configurações do Sistema
import os

# Configurações de Atualização
APP_NAME = "PAMC-ADM"
APP_VERSION = "v1.0.0"
GITHUB_REPO = "A-Assuncao/PAMC-ADM"  # Formato: "dono/repositório"

# URLs do sistema
URL_LISTA_PRESOS = 'https://canaime.com.br/sgp2rr/areas/impressoes/UND_ChamadaFOTOS_todos2.php?id_und_prisional='
URL_INFORMES = 'https://canaime.com.br/sgp2rr/areas/unidades/Informes_LER.php?id_cad_preso='
URL_FICHA_PRESO = 'https://canaime.com.br/sgp2rr/areas/unidades/Ficha_Preso_index.php?id_cad_preso='
URL_CADASTRO = 'https://canaime.com.br/sgp2rr/areas/unidades/cadastro.php?id_cad_preso='
URL_CERTIDAO_CARCERARIA = 'https://canaime.com.br/sgp2rr/areas/impressoes/UND_CertidaoCarceraria.php?id_cad_preso='
URL_FICHA_CARCERARIA = 'https://canaime.com.br/sgp2rr/areas/impressoes/UND_FichaCarceraria.php?id_cad_preso='
INICIO_URL_FOTOS = 'https://canaime.com.br/sgp2rr/fotos/presos/'
URL_UNIDADE = 'https://canaime.com.br/sgp2rr/areas/impressoes/UND_ChamadaFOTOS_todos2.php?id_und_prisional='

# Lista de unidades prisionais disponíveis
UNIDADES_PRISIONAIS = ['PAMC', 'CPBV', 'CPFBV', 'CPP', 'CABV', 'UPRRO', 'CME', 'DICAP']

# Dicionário com descrições detalhadas das unidades prisionais
DESCRICOES_UNIDADES = {
    'PAMC': 'Penitenciária Agrícola do Monte Cristo',
    'CPBV': 'Cadeia Pública Masculina de Boa Vista',
    'CPFBV': 'Cadeia Pública Feminina de Boa Vista',
    'CPP': 'Centro de Progressão Penitenciária',
    'CABV': 'Casa do Albergado de Boa Vista',
    'UPRRO': 'Unidade Prisional de Rorainópolis',
    'CME': 'Central de Monitoração Eletrônica',
    'DICAP': 'Divisão de Inteligência e Captura'
}

# Diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Timeout para requisições em milissegundos
TIMEOUT = 0

# Ordem das colunas no arquivo final
COLUNAS = [
    # 1. Identificação e Localização na Instituição
    'UP',
    'ALA',
    'CELA',
    'CÓDIGO',
    'FOTO',
    
    # 2. Dados Pessoais e Documentação
    'NOME',
    'VULGO',
    'SEXO',
    'DATA NASC.',
    'IDADE',
    'ALTURA',
    'COR / ETNIA',
    'CPF',
    'RG',
    
    # 3. Filiação
    'MÃE',
    'PAI',
    
    # 4. Endereço
    'ENDEREÇO',
    'CIDADE',
    'ESTADO',
    'PAÍS',
    
    # 5. Informações Socioeconômicas
    'ESTADO CIVIL',
    'QTD FILHOS',
    'ESCOLARIDADE',
    'PROFISSÃO',
    'RELIGIÃO',
    
    # 6. Dados Criminais e Processuais
    'CONDUTA',
    'CONDENADO?',
    'REU',
    'DATA PRISÃO',
    'DOM. CRIMINAL',
    'CRIME',
    'ARTIGO',
    'PROCESSO',
    'REGIME',
    'MODUS OPERANDI',
    'SENTENÇA DIAS',
    'DATA ÚLTIMO LANÇAMENTO',
    'ÚLTIMO LANÇAMENTO',
]

# Seletores para a lista de presos (primeira página)
SELETORES_LISTA_PRESOS = {
    'containers_informacoes': '.titulobkSingCAPS',
    'fotos': 'img',
}

# Localizadores organizados por URL para extração de dados
LOCALIZADORES = {
    # Página de ficha do preso
    'URL_FICHA_PRESO': {
        'VULGO': 'tr:nth-child(4) .titulobk',
    },
    
    # Página de cadastro do preso
    'URL_CADASTRO': {
        'SEXO': 'tr:nth-child(5) .titulobk:nth-child(2)',
        'DATA NASC.': 'tr:nth-child(5) .titulobk~ .titulobk',
        'RG': 'tr:nth-child(13) .titulobk:nth-child(2)',
        'PAI': 'tr:nth-child(4) .titulobk',
        'ENDEREÇO': 'tr:nth-child(24) .titulobk',
        'CIDADE': 'tr:nth-child(8) .titulobk',
        'ESTADO': 'tr:nth-child(9) .titulobk',
        'PAÍS': 'tr:nth-child(10) .titulobk',
    },
    
    # Página de informes do preso
    'URL_INFORMES': {
        'ALTURA': 'tr:nth-child(19) .tituloVerde .titulobk',
        'COR / ETNIA': 'tr:nth-child(16) .titulobk',
        'QTD FILHOS': '.titulobk~ .titulobk+ .titulobk',
        'ESCOLARIDADE': 'tr:nth-child(4) .titulobk',
        'PROFISSÃO': 'tr:nth-child(11) .titulobk',
        'RELIGIÃO': 'tr:nth-child(8) .titulobk',
        'MODUS OPERANDI': 'tr:nth-child(25) .titulobk',
    },
    
    # Página de certidão carcerária
    'URL_CERTIDAO_CARCERARIA': {
        'CONDUTA': 'table+ table span.titulobk',
        'DATA ÚLTIMO LANÇAMENTO': 'table+ table .titulobk:nth-child(2)',
        'ÚLTIMO LANÇAMENTO': '.titulobk div',
    },
    
    # Página de ficha carcerária
    'URL_FICHA_CARCERARIA': {
        'ESTADO CIVIL': 'tr:nth-child(11) .titulobk:nth-child(2)',
        'DATA PRISÃO': 'tr:nth-child(25) .titulobk:nth-child(2)',
        'DOM. CRIMINAL': 'tr:nth-child(26) .titulobk',
        'CONDENADO?': 'tr:nth-child(28) .titulobk:nth-child(2)',
        'CRIME': 'tr:nth-child(27) .titulobk',
        'ARTIGO': 'tr:nth-child(25) .titulobk~ .titulobk',
        'PROCESSO': 'tr:nth-child(30) .titulobk',
        'REU': 'tr:nth-child(31) .titulobk~ .titulobk',
        'REGIME': 'tr:nth-child(28) .titulobk~ .titulobk',
        'SENTENÇA DIAS': 'tr:nth-child(25) .titulobk~ .titulobk',
    }
}

LISTA_URLS_INFO_PRESO = [
    URL_FICHA_PRESO,
    URL_INFORMES,
    URL_FICHA_CARCERARIA,
    URL_CERTIDAO_CARCERARIA,
    URL_CADASTRO
]



# Requisitos para o sistema de atualização
# pip install requests packaging
