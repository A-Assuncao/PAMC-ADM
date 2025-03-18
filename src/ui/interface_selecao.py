import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import traceback
import sys
from src.utils import config
from typing import List, Callable
import queue
from datetime import datetime

# Definindo esquema de cores moderno
CORES = {
    'primaria': '#1976D2',  # Azul principal
    'primaria_escuro': '#1565C0',  # Azul escuro para hover
    'secundaria': '#4CAF50',  # Verde para ações positivas
    'secundaria_escuro': '#388E3C',  # Verde escuro para hover
    'alerta': '#F44336',  # Vermelho para alertas/cancelar
    'alerta_escuro': '#D32F2F',  # Vermelho escuro para hover
    'fundo': '#F5F5F5',  # Cinza claro para fundo
    'texto': '#212121',  # Quase preto para texto
    'texto_secundario': '#757575',  # Cinza médio para texto secundário
    'borda': '#E0E0E0',  # Cinza claro para bordas
    'destaque': '#FFD54F',  # Amarelo para destaques
}

altura = 900
largura = 800


class RedirectText:
    """Classe para redirecionar a saída do console para o widget Text."""
    
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.updating = True
        threading.Thread(target=self._update_widget, daemon=True).start()

    def write(self, string: str):
        self.queue.put(string)
    
    def flush(self):
        pass

    def _update_widget(self):
        """Atualiza o widget Text com as mensagens da fila."""
        while self.updating:
            try:
                while True:  # Processa todas as mensagens disponíveis
                    string = self.queue.get_nowait()
                    self.text_widget.insert(tk.END, string)
                    self.text_widget.see(tk.END)
                    self.text_widget.update_idletasks()
            except queue.Empty:
                time.sleep(0.1)
                continue

class SeletorUnidades(tk.Tk):
    # Definir tamanho padrão da janela
    tamanho = f"{largura}x{altura}"
    
    def __init__(self):
        super().__init__()
        
        # Configuração da janela
        self.title("Sistema de Extração de Dados Prisionais")
        self.geometry(self.tamanho)
        self.configure(bg=CORES['fundo'])
        
        # Definir tamanho mínimo para a janela
        self.minsize(800, 600)
        
        # Definir ícone (se disponível)
        try:
            self.iconbitmap('assets/icon.ico')
        except:
            pass
        
        # Centralizar a janela na tela
        self.centralizar_janela()
        
        # Variáveis de controle
        self.processando = False
        self.cancelar = False
        self.thread_processamento = None
        
        # Configurar estilos
        self.configurar_estilos()
        
        # Criar layout principal
        self.criar_layout()
        
        # Callback para processar seleção
        self.callback_processar = None

    def criar_layout(self):
        """Cria o layout principal da aplicação."""
        # Frame principal com padding
        main_frame = ttk.Frame(self, padding="20", style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho com logo e título
        self.criar_cabecalho(main_frame)
        
        # Área de conteúdo principal
        content_frame = ttk.Frame(main_frame, style='Content.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 20))
        
        # Painel esquerdo: seleção de unidades
        self.criar_painel_selecao(content_frame)
        
        # Painel direito: opções e controles
        self.criar_painel_controles(content_frame)
        
        # Área de progresso e status
        self.criar_area_progresso(main_frame)
        
        # Área de log
        self.criar_area_log(main_frame)
    
    def criar_cabecalho(self, parent):
        """Cria o cabeçalho da aplicação."""
        header_frame = ttk.Frame(parent, style='Header.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Título principal
        ttk.Label(
            header_frame, 
            text="Extrator de Informações Prisionais",
            font=('Segoe UI', 16, 'bold'),
            foreground=CORES['primaria'],
            style='Header.TLabel'
        ).pack(pady=(0, 5))
        
        # Subtítulo
        ttk.Label(
            header_frame, 
            text="Selecione as unidades e configure opções para iniciar a extração de dados",
            font=('Segoe UI', 10),
            foreground=CORES['texto_secundario'],
            style='Subtitle.TLabel'
        ).pack()
        
        # Separador decorativo
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))
    
    def criar_painel_selecao(self, parent):
        """Cria o painel de seleção de unidades."""
        # Frame para seleção de unidades (ocupa metade esquerda)
        selection_frame = ttk.LabelFrame(
            parent, 
            text="  Unidades Prisionais  ",
            padding=15,
            style='Card.TLabelframe'
        )
        selection_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Botões de ação no topo
        action_frame = ttk.Frame(selection_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            action_frame,
            text="Selecionar Todos",
            command=self.selecionar_todos,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="Limpar Seleção",
            command=self.limpar_selecao,
            style='Action.TButton'
        ).pack(side=tk.LEFT)

        # Debugging - mostrar unidades disponíveis
        print("Unidades prisionais disponíveis:")
        for unidade in config.UNIDADES_PRISIONAIS:
            print(f" - {unidade}: {config.DESCRICOES_UNIDADES.get(unidade, '')}")

        # Frame para as checkboxes com scrollbar
        checkbox_container = ttk.Frame(selection_frame)
        checkbox_container.pack(fill=tk.BOTH, expand=True)
        
        # Criar o frame para as checkboxes
        self.checkbox_frame = ttk.Frame(checkbox_container)
        self.checkbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Variáveis para os checkboxes
        self.checkbox_vars = {}
        self.criar_checkboxes()
    
    def criar_painel_controles(self, parent):
        """Cria o painel de controles e opções."""
        # Frame para controles (ocupa metade direita)
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Opções de teste
        options_frame = ttk.LabelFrame(
            control_frame, 
            text="  Opções de Execução  ",
            padding=15,
            style='Card.TLabelframe'
        )
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Variáveis para as opções
        self.modo_teste_var = tk.BooleanVar(value=False)
        self.limite_teste_var = tk.IntVar(value=5)
        self.mostrar_navegador_var = tk.BooleanVar(value=False)
        
        # Modo de teste com descrição
        modo_frame = ttk.Frame(options_frame)
        modo_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.cb_modo_teste = ttk.Checkbutton(
            modo_frame, 
            text="Ativar modo de teste", 
            variable=self.modo_teste_var,
            command=self.atualizar_opcoes_teste,
            style='Bold.TCheckbutton'
        )
        self.cb_modo_teste.pack(anchor=tk.W)
        
        ttk.Label(
            modo_frame,
            text="Limita a quantidade de registros processados\npara testar o funcionamento do sistema",
            foreground=CORES['texto_secundario'],
            style='Detail.TLabel'
        ).pack(anchor=tk.W, padx=(17, 0))
        
        # Opções de limite
        limite_frame = ttk.Frame(options_frame)
        limite_frame.pack(fill=tk.X, pady=(0, 15), padx=(17, 0))
        
        self.rb_limite_5 = ttk.Radiobutton(
            limite_frame, 
            text="5 cadastros por unidade", 
            variable=self.limite_teste_var, 
            value=5
        )
        self.rb_limite_5.pack(anchor=tk.W, pady=(0, 5))
        
        self.rb_limite_10 = ttk.Radiobutton(
            limite_frame, 
            text="10 cadastros por unidade", 
            variable=self.limite_teste_var, 
            value=10
        )
        self.rb_limite_10.pack(anchor=tk.W)
        
        # Opção para mostrar navegador
        navegador_frame = ttk.Frame(options_frame)
        navegador_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.cb_mostrar_navegador = ttk.Checkbutton(
            navegador_frame,
            text="Mostrar navegador durante execução",
            variable=self.mostrar_navegador_var
        )
        self.cb_mostrar_navegador.pack(anchor=tk.W)
        
        ttk.Label(
            navegador_frame,
            text="Útil para acompanhar o processo de extração\nno navegador e resolver problemas",
            foreground=CORES['texto_secundario'],
            style='Detail.TLabel'
        ).pack(anchor=tk.W, padx=(17, 0))
        
        # Inicialmente desabilitar as opções de limite
        self.atualizar_opcoes_teste()
        
        # Botões de ação
        action_frame = ttk.LabelFrame(
            control_frame, 
            text="  Ações  ",
            padding=15,
            style='Card.TLabelframe'
        )
        action_frame.pack(fill=tk.BOTH, pady=(0, 0))
        
        # Botão grande de processar
        self.btn_processar = ttk.Button(
            action_frame,
            text="Iniciar Extração",
            command=self.iniciar_processamento,
            style='Primary.TButton'
        )
        self.btn_processar.pack(fill=tk.X, ipady=8, pady=(0, 10))
        
        # Botão de cancelar (inicialmente desabilitado)
        self.btn_cancelar = ttk.Button(
            action_frame,
            text="Cancelar Processamento",
            command=self.cancelar_processamento,
            state=tk.DISABLED,
            style='Danger.TButton'
        )
        self.btn_cancelar.pack(fill=tk.X, ipady=8)
    
    def criar_area_progresso(self, parent):
        """Cria a área de progresso e status."""
        progress_frame = ttk.Frame(parent, style='Progress.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Label para mensagem de progresso
        self.progresso_label = ttk.Label(
            progress_frame,
            text="Aguardando início do processamento...",
            style='Status.TLabel'
        )
        self.progresso_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Frame para barra de progresso
        bar_frame = ttk.Frame(progress_frame)
        bar_frame.pack(fill=tk.X)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            bar_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style='Accent.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Label para percentual
        self.percentual_label = ttk.Label(
            bar_frame,
            text="0%",
            width=5,
            anchor=tk.E,
            style='Percent.TLabel'
        )
        self.percentual_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def criar_area_log(self, parent):
        """Cria a área de log de execução."""
        log_frame = ttk.LabelFrame(
            parent, 
            text="  Log de Execução  ",
            padding=10,
            style='Card.TLabelframe'
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para a área de texto com scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Área de texto
        self.log_text = tk.Text(
            text_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#FFFFFF',
            fg=CORES['texto'],
            borderwidth=1,
            relief=tk.SOLID,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Botões de controle do log
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            log_control_frame,
            text="Limpar Log",
            command=self.limpar_log,
            style='Small.TButton'
        ).pack(side=tk.RIGHT)
        
        # Redirecionar stdout para a área de texto
        self.redirect = RedirectText(self.log_text)
        sys.stdout = self.redirect
    
    def criar_checkboxes(self):
        """Cria os checkboxes para cada unidade prisional."""
        # Limpar checkboxes existentes
        for child in self.checkbox_frame.winfo_children():
            child.destroy()
            
        # Verificar se há unidades configuradas
        unidades = getattr(config, 'UNIDADES_PRISIONAIS', [])
        
        if not unidades:
            ttk.Label(
                self.checkbox_frame,
                text="Nenhuma unidade prisional configurada.\nVerifique o arquivo de configuração.",
                foreground='red',
                font=('Segoe UI', 10, 'bold')
            ).pack(padx=10, pady=10)
            print("ERRO: Nenhuma unidade prisional configurada!")
            return
            
        print(f"Criando {len(unidades)} checkboxes para unidades prisionais...")
            
        # Exibir todas as unidades na mesma ordem que estão definidas no config
        for i, unidade in enumerate(unidades):
            # Frame para cada unidade
            item_frame = ttk.Frame(self.checkbox_frame)
            item_frame.pack(fill=tk.X, pady=5)
            
            # Criar variável para o checkbox
            var = tk.BooleanVar()
            self.checkbox_vars[unidade] = var
            
            # Checkbox
            cb = ttk.Checkbutton(
                item_frame,
                text=unidade,
                variable=var,
                style='Unit.TCheckbutton'
            )
            cb.pack(side=tk.LEFT)
            
            # Label com descrição completa
            desc = self.obter_descricao_unidade(unidade)
            ttk.Label(
                item_frame,
                text=f"- {desc}",
                foreground=CORES['texto_secundario'],
                style='UnitDesc.TLabel'
            ).pack(side=tk.LEFT, padx=(5, 0))
        
        print(f"Criados {len(self.checkbox_vars)} checkboxes para unidades prisionais")
    
    def obter_descricao_unidade(self, sigla: str) -> str:
        """Retorna a descrição completa da unidade baseada no dicionário de config.py."""
        return config.DESCRICOES_UNIDADES.get(sigla, sigla)
    
    def selecionar_todos(self):
        """Seleciona todos os checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(True)
    
    def limpar_selecao(self):
        """Limpa a seleção de todos os checkboxes."""
        for var in self.checkbox_vars.values():
            var.set(False)
    
    def obter_unidades_selecionadas(self) -> List[str]:
        """Retorna lista com as unidades selecionadas."""
        return [
            unidade for unidade, var in self.checkbox_vars.items()
            if var.get()
        ]
    
    def atualizar_estado_botoes(self, processando=False):
        """Atualiza o estado dos componentes baseado no estado de processamento."""
        self.processando = processando
        
        if processando:
            # Desabilitar botões de seleção e processamento
            for widget in self.winfo_children():
                self.desabilitar_widgets_recursivo(widget, ['TButton', 'TCheckbutton', 'TRadiobutton'])
            
            # Habilitar apenas o botão de cancelar
            self.btn_cancelar.config(state=tk.NORMAL)
            self.btn_processar.config(state=tk.DISABLED)
            
            # Mostrar barra de progresso
            self.percentual_label.config(text="0%")
        else:
            # Habilitar todos os widgets desabilitados
            for widget in self.winfo_children():
                self.habilitar_widgets_recursivo(widget, ['TButton', 'TCheckbutton', 'TRadiobutton'])
            
            # Desabilitar botão de cancelar
            self.btn_cancelar.config(state=tk.DISABLED)
            
            # Atualizar estado das opções de teste conforme o checkbox principal
            self.atualizar_opcoes_teste()
    
    def desabilitar_widgets_recursivo(self, widget, tipos):
        """Desabilita recursivamente widgets de determinados tipos."""
        widget_type = widget.winfo_class()
        if any(tipo in widget_type for tipo in tipos):
            try:
                widget.config(state=tk.DISABLED)
            except:
                pass
        
        for child in widget.winfo_children():
            self.desabilitar_widgets_recursivo(child, tipos)
    
    def habilitar_widgets_recursivo(self, widget, tipos):
        """Habilita recursivamente widgets de determinados tipos."""
        widget_type = widget.winfo_class()
        if any(tipo in widget_type for tipo in tipos):
            try:
                widget.config(state=tk.NORMAL)
            except:
                pass
        
        for child in widget.winfo_children():
            self.habilitar_widgets_recursivo(child, tipos)
    
    def iniciar_processamento(self):
        """Inicia o processamento em uma thread separada."""
        selecionadas = self.obter_unidades_selecionadas()
        if not selecionadas:
            messagebox.showwarning(
                "Aviso", 
                "Nenhuma unidade selecionada!\n\nSelecione pelo menos uma unidade para iniciar o processamento.",
                parent=self
            )
            return
        
        if self.processando:
            return
            
        # Resetar flag de cancelamento
        self.cancelar = False
        
        # Obter opções de teste
        opcoes_teste = self.obter_opcoes_teste()
        
        # Atualizar estado da interface
        self.processando = True
        self.atualizar_estado_botoes(True)
        
        # Limpar log antes de iniciar
        self.limpar_log()
        
        # Mostrar mensagem inicial no log
        hora_atual = datetime.now().strftime('%H:%M:%S')
        print(f"[{hora_atual}] Iniciando processamento de {len(selecionadas)} unidades:")
        for unidade in selecionadas:
            print(f"  - {unidade}: {self.obter_descricao_unidade(unidade)}")
        
        if opcoes_teste['modo_teste']:
            print(f"[MODO TESTE] Limitado a {opcoes_teste['limite_teste']} cadastros por unidade.")
        
        # Iniciar processamento em thread separada
        def executar_processamento():
            try:
                if self.callback_processar:
                    self.callback_processar(selecionadas, opcoes_teste)
            finally:
                # Garantir que a interface seja atualizada ao finalizar
                self.after(0, self.finalizar_processamento)
        
        self.thread_processamento = threading.Thread(
            target=executar_processamento,
            daemon=True
        )
        self.thread_processamento.start()
    
    def finalizar_processamento(self):
        """Finaliza o processamento e restaura a interface."""
        self.processando = False
        self.atualizar_estado_botoes(False)
        self.thread_processamento = None
        self.btn_cancelar.config(text="Cancelar Processamento")
        self.percentual_label.config(text="100%")
    
    def cancelar_processamento(self):
        """Cancela o processamento em andamento."""
        if self.processando:
            mensagem = "\nSolicitação de cancelamento enviada. Aguardando finalização do processamento..."
            print(mensagem)
            self.progresso_label.config(text="Cancelando processamento...")
            self.cancelar = True
            self.btn_cancelar.config(state=tk.DISABLED, text="Cancelando...")
    
    def verificar_cancelamento(self):
        """Verifica se o processamento foi cancelado."""
        return self.cancelar
    
    def definir_callback_processamento(self, callback: Callable[[List[str], dict], None]):
        """Define o callback a ser chamado quando clicar em processar.
        
        Args:
            callback: Função que recebe uma lista de unidades e um dicionário de opções
        """
        self.callback_processar = callback
    
    def limpar_log(self):
        """Limpa a área de log."""
        self.log_text.delete(1.0, tk.END)

    def centralizar_janela(self):
        """Centraliza a janela na tela e garante que esteja totalmente visível."""
        try:
            # Obtém as dimensões da tela
            largura_tela = self.winfo_screenwidth()
            altura_tela = self.winfo_screenheight()
            
            # Usa as variáveis globais de altura e largura
            global altura, largura
            
            # Ajusta para garantir que a janela não seja maior que a tela
            if largura > largura_tela:
                largura = int(largura_tela * 0.9)
            
            if altura > altura_tela:
                altura = int(altura_tela * 0.9)
                
            # Atualiza a variável tamanho para refletir as dimensões ajustadas
            self.tamanho = f"{largura}x{altura}"
            
            # Calcular a posição x,y para centralizar
            pos_x = (largura_tela // 2) - (largura // 2)
            
            # Ajustar a posição vertical para dar mais espaço na parte inferior
            # Usa 40% da altura na parte superior (em vez de 50%)
            pos_y = int((altura_tela * 0.4) - (altura * 0.4))
            
            # Garantir que os valores sejam positivos e a janela esteja na tela
            pos_x = max(0, min(pos_x, largura_tela - largura))
            pos_y = max(0, min(pos_y, altura_tela - altura))
            
            # Configurar a geometria
            self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        except Exception as e:
            print(f"Erro ao centralizar janela: {str(e)}")
            self.geometry(f"{largura}x{altura}+10+10")

    def atualizar_opcoes_teste(self):
        """Atualiza o estado das opções de teste com base no checkbox de modo de teste."""
        if self.modo_teste_var.get():
            # Ativar opções de teste e definir 5 como padrão
            self.rb_limite_5.configure(state=tk.NORMAL)
            self.rb_limite_10.configure(state=tk.NORMAL)
            # Definir 5 como valor padrão
            self.limite_teste_var.set(5)
        else:
            # Desativar opções de teste
            self.rb_limite_5.configure(state=tk.DISABLED)
            self.rb_limite_10.configure(state=tk.DISABLED)
    
    def obter_opcoes_teste(self):
        """Retorna as opções de teste selecionadas."""
        return {
            'modo_teste': self.modo_teste_var.get(),
            'limite_teste': self.limite_teste_var.get(),
            'mostrar_navegador': self.mostrar_navegador_var.get()
        }

    def atualizar_progresso(self, mensagem, percentual=None):
        """Atualiza a barra de progresso e a mensagem associada."""
        # Atualizar na thread principal (evitar conflitos de thread)
        def _update():
            # Atualizar mensagem
            self.progresso_label.config(text=mensagem)
            
            # Atualizar percentual se fornecido
            if percentual is not None:
                # Se for zero, resetar barra
                if percentual == 0:
                    self.progress_var.set(0)
                    self.percentual_label.config(text="0%")
                    self.progress_bar.config(mode='determinate')
                # Se for negativo, usar modo indeterminado
                elif percentual < 0:
                    self.progress_bar.config(mode='indeterminate')
                    self.progress_bar.start(50)
                    self.percentual_label.config(text="")
                else:
                    # Modo determinado com valor definido
                    self.progress_bar.config(mode='determinate')
                    self.progress_bar.stop()
                    self.progress_var.set(percentual)
                    self.percentual_label.config(text=f"{int(percentual)}%")
            
            # Atualizar UI
            self.update_idletasks()
        
        # Agendar atualização na thread principal
        self.after(0, _update)
        
        # Também adicionar mensagem ao log, se for informativa
        if percentual is not None and (percentual == 0 or percentual == 100 or 
                                  (isinstance(mensagem, str) and not mensagem.startswith("Extraindo dados:"))):
            print(mensagem)

    def configurar_estilos(self):
        """Configura os estilos personalizados para os widgets."""
        estilo = ttk.Style()
        estilo.theme_use('clam')  # Usar tema clam como base
        
        # Configurar cores gerais
        estilo.configure('.', 
                         background=CORES['fundo'],
                         foreground=CORES['texto'],
                         font=('Segoe UI', 10))
        
        # Frames
        estilo.configure('TFrame', background=CORES['fundo'])
        estilo.configure('Content.TFrame', background=CORES['fundo'])
        estilo.configure('Header.TFrame', background=CORES['fundo'])
        estilo.configure('Progress.TFrame', background=CORES['fundo'])
        estilo.configure('CheckboxArea.TFrame', background=CORES['fundo'])
        
        # Botões
        estilo.configure('TButton', 
                         background=CORES['primaria'],
                         foreground='white',
                         font=('Segoe UI', 10))
        
        estilo.configure('Primary.TButton', 
                         background=CORES['secundaria'],
                         foreground='white',
                         font=('Segoe UI', 12, 'bold'))
        
        estilo.configure('Danger.TButton', 
                         background=CORES['alerta'],
                         foreground='white',
                         font=('Segoe UI', 12, 'bold'))
        
        estilo.configure('Action.TButton', 
                         font=('Segoe UI', 9))
        
        estilo.configure('Small.TButton', 
                         font=('Segoe UI', 9))
        
        # Mapeamentos de estados do botão
        estilo.map('TButton',
                  background=[('active', CORES['primaria_escuro']), 
                              ('disabled', '#CCCCCC')],
                  foreground=[('disabled', '#999999')])
        
        estilo.map('Primary.TButton',
                  background=[('active', CORES['secundaria_escuro']), 
                              ('disabled', '#CCCCCC')],
                  foreground=[('disabled', '#999999')])
        
        estilo.map('Danger.TButton',
                  background=[('active', CORES['alerta_escuro']), 
                              ('disabled', '#CCCCCC')],
                  foreground=[('disabled', '#999999')])
        
        # Checkbuttons
        estilo.configure('TCheckbutton', 
                         background=CORES['fundo'],
                         font=('Segoe UI', 10))
        
        estilo.configure('Bold.TCheckbutton', 
                         font=('Segoe UI', 11, 'bold'))
        
        estilo.configure('Unit.TCheckbutton', 
                         font=('Segoe UI', 10, 'bold'))
        
        # Labels
        estilo.configure('TLabel', 
                         background=CORES['fundo'],
                         font=('Segoe UI', 10))
        
        estilo.configure('Header.TLabel', 
                         font=('Segoe UI', 16, 'bold'),
                         foreground=CORES['primaria'])
        
        estilo.configure('Subtitle.TLabel', 
                         font=('Segoe UI', 10),
                         foreground=CORES['texto_secundario'])
        
        estilo.configure('Status.TLabel', 
                         font=('Segoe UI', 10, 'bold'),
                         foreground=CORES['texto'])
        
        estilo.configure('Percent.TLabel', 
                         font=('Segoe UI', 9, 'bold'),
                         foreground=CORES['primaria'])
        
        estilo.configure('Detail.TLabel', 
                         font=('Segoe UI', 9),
                         foreground=CORES['texto_secundario'])
        
        estilo.configure('UnitDesc.TLabel', 
                         font=('Segoe UI', 9),
                         foreground=CORES['texto_secundario'])
        
        # LabelFrames
        estilo.configure('TLabelframe', 
                         background=CORES['fundo'],
                         foreground=CORES['texto'])
        
        estilo.configure('TLabelframe.Label', 
                         background=CORES['fundo'],
                         foreground=CORES['primaria'],
                         font=('Segoe UI', 11, 'bold'))
        
        estilo.configure('Card.TLabelframe', 
                         background=CORES['fundo'],
                         borderwidth=1,
                         relief=tk.SOLID)
        
        estilo.configure('Card.TLabelframe.Label', 
                         background=CORES['fundo'],
                         foreground=CORES['primaria'],
                         font=('Segoe UI', 11, 'bold'))
        
        # Progressbar
        estilo.configure('Horizontal.TProgressbar', 
                         troughcolor=CORES['borda'],
                         background=CORES['primaria'],
                         borderwidth=0,
                         thickness=15)
        
        estilo.configure('Accent.Horizontal.TProgressbar', 
                         troughcolor=CORES['borda'],
                         background=CORES['secundaria'],
                         borderwidth=0,
                         thickness=15)

def criar_interface() -> SeletorUnidades:
    """Cria e retorna a interface de seleção."""
    print("Inicializando interface de seleção...")
    try:
        interface = SeletorUnidades()
        print("Interface de seleção criada com sucesso!")
        return interface
    except Exception as e:
        print(f"ERRO ao criar interface: {str(e)}")
        traceback.print_exc()
        
        # Criar uma interface de emergência que seja compatível com a original
        class InterfaceEmergencia(tk.Tk):
            def __init__(self, erro):
                super().__init__()
                self.title("ERRO - Interface de Emergência")
                self.geometry("600x400")
                self.configure(bg="#F8F8F8")
                
                # Frame principal
                main_frame = tk.Frame(self, bg="#F8F8F8", padx=20, pady=20)
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Ícone de erro
                tk.Label(
                    main_frame, 
                    text="⚠️", 
                    font=("Arial", 48),
                    fg="#D32F2F",
                    bg="#F8F8F8"
                ).pack(pady=(20, 10))
                
                # Mensagem de erro
                tk.Label(
                    main_frame, 
                    text="Erro ao inicializar a interface", 
                    font=("Segoe UI", 16, "bold"),
                    fg="#212121",
                    bg="#F8F8F8"
                ).pack(pady=10)
                
                # Detalhes do erro
                error_frame = tk.Frame(main_frame, bg="#EEEEEE", bd=1, relief=tk.SOLID, padx=10, pady=10)
                error_frame.pack(fill=tk.X, pady=10)
                
                tk.Label(
                    error_frame, 
                    text=str(erro),
                    font=("Consolas", 10),
                    fg="#D32F2F",
                    bg="#EEEEEE",
                    justify=tk.LEFT,
                    wraplength=500
                ).pack(fill=tk.X)
                
                # Botão para tentar novamente
                tk.Button(
                    main_frame,
                    text="Fechar Aplicação",
                    command=self.destroy,
                    font=("Segoe UI", 11),
                    bg="#D32F2F",
                    fg="white",
                    padx=20,
                    pady=8,
                    relief=tk.FLAT
                ).pack(pady=20)
            
            # Métodos necessários para compatibilidade
            def definir_callback_processamento(self, callback):
                print("Interface em modo de emergência - processamento desativado")
                
            def atualizar_progresso(self, mensagem, percentual=None):
                print(f"Progresso (emergência): {mensagem}")
                
            def verificar_cancelamento(self):
                return False
                
        return InterfaceEmergencia(str(e))

if __name__ == "__main__":
    # Exemplo de uso
    app = criar_interface()
    
    def exemplo_processamento(unidades: List[str], opcoes_teste: dict):
        print(f"Opções de teste: {opcoes_teste}")
        for unidade in unidades:
            print(f"Processando {unidade}...")
            # Simular processamento
            time.sleep(1)
    
    app.definir_callback_processamento(exemplo_processamento)
    app.mainloop() 