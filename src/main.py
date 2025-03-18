import os
import sys
import traceback
from src.ui.interface_selecao import criar_interface
from src.core.listar_presos_up import listar_presos_up
from login_canaime import Login
from src.utils.updater import check_and_update

def iniciar_extracao(unidades_selecionadas, opcoes, interface):
    """
    Função principal que inicia a extração de dados usando Playwright.
    
    Args:
        unidades_selecionadas: Lista de códigos das unidades selecionadas
        opcoes: Dicionário com opções de configuração
        interface: Objeto da interface gráfica para atualização do progresso
    """
    # Atualiza interface
    interface.atualizar_progresso("Iniciando navegador...", 0)
    
    # Obtém as opções de modo de teste
    modo_teste = opcoes.get('modo_teste', False)
    limite_teste = opcoes.get('limite_teste', 10)
    mostrar_navegador = opcoes.get('mostrar_navegador', False)
    
    # Registra o início do processamento
    if modo_teste:
        interface.atualizar_progresso(f"MODO TESTE ativado - máximo de {limite_teste} presos por unidade", 2)
    
    try:
        with Login() as login:
            
            # Cria uma página
            page = login.obter_pagina(headless= not mostrar_navegador)
            
            # Configurar a página para não baixar imagens (otimização)
            page.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
            
            # Login no sistema (implementar conforme necessário)
            interface.atualizar_progresso("Realizando login no sistema...", 5)

            
            # Chama a função principal com a interface para mostrar progresso
            resultado = listar_presos_up(
                page, 
                interface=interface,
                unidades_selecionadas=unidades_selecionadas,
                modo_teste=modo_teste,
                limite_teste=limite_teste
            )
            
            # Fecha o navegador
            login.fechar()
            
            # Verifica o resultado
            if resultado:
                caminho_excel = resultado['caminho_excel']
                interface.atualizar_progresso(f"Processamento concluído com sucesso! Arquivo salvo em:\n{caminho_excel}", 100)
            else:
                interface.atualizar_progresso("Operação cancelada ou finalizada com erro.", 0)
                
    except Exception as e:
        # Em caso de erro, exibe na interface
        erro = f"Erro: {str(e)}\n{traceback.format_exc()}"
        print(erro)
        interface.atualizar_progresso(f"Erro durante o processamento: {str(e)}", 0)

def main():
    """Função principal do programa."""
    try:
        # Verificar por atualizações
        print("Verificando atualizações...")
        check_and_update()
        
        # Cria e configura a interface
        interface = criar_interface()
        
        # Define o callback de processamento
        interface.definir_callback_processamento(
            lambda unidades, opcoes: iniciar_extracao(unidades, opcoes, interface)
        )
        
        # Inicia o loop da interface
        interface.mainloop()
        
    except Exception as e:
        print(f"Erro fatal: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
