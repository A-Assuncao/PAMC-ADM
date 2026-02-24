import os
import sys
import traceback
import time
from playwright.sync_api import sync_playwright
from src.ui.interface_selecao import criar_interface
from src.core.listar_presos_up import listar_presos_up
from login_canaime import Login
from src.utils.updater import check_and_update

def fazer_login_alternativo(headless=False, timeout_navegacao=30000):
    """
    Faz login no sistema Canaimé de forma alternativa, sem depender de networkidle.
    
    Esta função resolve o problema onde obter_pagina() trava esperando networkidle
    que nunca é alcançado devido a requisições contínuas na página.
    
    Args:
        headless: Se True, o navegador não será exibido
        timeout_navegacao: Timeout para operações de navegação em ms
        
    Returns:
        page: Objeto page do Playwright logado, ou None se falhar
    """
    print("[LOG] ===== INICIANDO LOGIN ALTERNATIVO =====")
    
    try:
        # Usa a biblioteca login-canaime apenas para obter credenciais
        with Login() as login_obj:
            # Obtém credenciais
            if not hasattr(login_obj, 'usuario') or not login_obj.usuario:
                print("[LOG] Obtendo credenciais...")
                login_obj.obter_credenciais()
            
            if not login_obj.usuario or not login_obj.senha:
                print("[LOG] ERRO: Não foi possível obter credenciais")
                return None
            
            print(f"[LOG] Credenciais obtidas para usuário: {login_obj.usuario}")
            
            # Inicia Playwright manualmente
            print("[LOG] Iniciando Playwright...")
            playwright = sync_playwright().start()
            
            # Configura argumentos do navegador
            browser_args = [
                "--disable-web-security",
                "--disable-site-isolation-trials",
                "--no-sandbox",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
            
            # Lança o navegador
            print("[LOG] Lançando navegador Chromium...")
            browser = playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )
            
            # Cria contexto
            print("[LOG] Criando contexto do navegador...")
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                bypass_csp=True,
                permissions=["geolocation"]
            )
            context.set_default_navigation_timeout(timeout_navegacao)
            
            # Cria página
            print("[LOG] Criando página...")
            page = context.new_page()
            page.set_default_timeout(timeout_navegacao)
            
            # Obtém URL de login da biblioteca
            try:
                from login_canaime.auth import URL_LOGIN_CANAIME
                url_login = URL_LOGIN_CANAIME
            except ImportError:
                try:
                    from login_canaime import URL_LOGIN_CANAIME
                    url_login = URL_LOGIN_CANAIME
                except:
                    # URL padrão do sistema Canaimé
                    url_login = "https://canaime.com.br/sgp2rr/login/login_principal.php"
            
            print(f"[LOG] Navegando para página de login: {url_login}")
            page.goto(url_login, wait_until="domcontentloaded")
            print(f"[LOG] Página de login carregada. URL atual: {page.url}")
            
            # Aguarda um pouco para garantir que a página carregou
            time.sleep(2)
            
            # Preenche formulário de login
            print("[LOG] Preenchendo formulário de login...")
            try:
                page.fill("input[name='usuario']", login_obj.usuario)
                print("[LOG] Usuário preenchido")
                page.fill("input[name='senha']", login_obj.senha)
                print("[LOG] Senha preenchida")
                
                # Pressiona Enter para submeter
                print("[LOG] Submetendo formulário...")
                page.press("input[name='senha']", "Enter")
                
                # Aguarda navegação (não espera networkidle, apenas domcontentloaded)
                print("[LOG] Aguardando resposta do login...")
                try:
                    # Aguarda até 15 segundos para a navegação acontecer
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    print("[LOG] Navegação detectada após login")
                except Exception as nav_e:
                    print(f"[LOG] AVISO: Timeout aguardando navegação: {str(nav_e)}")
                    # Continua mesmo assim
                
                # Aguarda um pouco mais para garantir que a página carregou
                time.sleep(3)
                
                # Verifica se o login foi bem-sucedido
                current_url = page.url
                print(f"[LOG] URL após login: {current_url}")
                
                # Verifica se ainda está na página de login
                if 'login' in current_url.lower() or 'index.php' in current_url.lower():
                    # Verifica se há algum elemento que indique falha no login
                    try:
                        # Tenta encontrar algum elemento que indique erro
                        erro_element = page.locator("text=/erro|inválido|incorreto/i").first
                        if erro_element.count() > 0:
                            erro_texto = erro_element.text_content()
                            print(f"[LOG] ERRO: Possível falha no login - {erro_texto}")
                            return None
                    except:
                        pass
                    
                    # Se ainda está na página de login após alguns segundos, pode ter falhado
                    print("[LOG] AVISO: Ainda na página de login. Verificando novamente...")
                    time.sleep(2)
                    current_url = page.url
                    if 'login' in current_url.lower():
                        print("[LOG] ERRO: Login falhou - ainda na página de login")
                        return None
                
                # Verifica se há imagens na página (indicador de sucesso do login)
                try:
                    imagens = page.locator('img').count()
                    print(f"[LOG] Número de imagens na página: {imagens}")
                    if imagens < 4:
                        print("[LOG] AVISO: Poucas imagens na página, pode indicar falha no login")
                        # Mas continua mesmo assim, pois pode ser que a página esteja correta
                except Exception as img_e:
                    print(f"[LOG] AVISO: Não foi possível contar imagens: {str(img_e)}")
                
                print("[LOG] Login alternativo concluído com sucesso!")
                # Armazena referências para poder fechar depois
                page._browser = browser
                page._context = context
                page._playwright = playwright
                return page
                
            except Exception as login_e:
                print(f"[LOG] ERRO durante o login: {str(login_e)}")
                print(f"[LOG] Traceback: {traceback.format_exc()}")
                page.close()
                browser.close()
                playwright.stop()
                return None
                
    except Exception as e:
        print(f"[LOG] ERRO CRÍTICO no login alternativo: {str(e)}")
        print(f"[LOG] Traceback: {traceback.format_exc()}")
        return None

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
    
    # Registra o início do processamento
    if modo_teste:
        interface.atualizar_progresso(f"MODO TESTE ativado - máximo de {limite_teste} presos por unidade", 2)
    
    try:
        # Tenta primeiro o método alternativo de login que não depende de networkidle
        interface.atualizar_progresso("Realizando login no sistema...", 3)
        print("[LOG] Tentando login alternativo (não depende de networkidle)...")
        
        page = fazer_login_alternativo(headless=True, timeout_navegacao=30000)
        login = None  # Inicializa variável para controle de fechamento
        
        # Se o método alternativo falhar, tenta o método original como fallback
        if page is None:
            print("[LOG] Login alternativo falhou. Tentando método original como fallback...")
            interface.atualizar_progresso("Tentando método de login alternativo...", 5)
            
            login_obj = Login()
            login = login_obj.__enter__()  # Entra no context manager manualmente
            # Tenta com timeout menor primeiro
            page = login.obter_pagina(headless=True, timeout=30000)
        
        # Verifica se a página foi obtida com sucesso
        if page is None:
            erro_msg = (
                "Erro ao obter página logada: Timeout excedido.\n\n"
                "Possíveis causas:\n"
                "- Problemas de conexão com a internet\n"
                "- Sistema Canaimé temporariamente indisponível\n"
                "- Credenciais inválidas ou expiradas\n"
                "- Timeout muito curto para a operação\n"
                "- A página pode ter requisições contínuas que impedem o estado 'networkidle'\n\n"
                "Tente novamente ou verifique sua conexão."
            )
            interface.atualizar_progresso(erro_msg, 0)
            print(erro_msg)
            return None
        
        # Verificar se a página está realmente logada antes de continuar
        try:
            # Tenta verificar se estamos em uma página logada verificando a URL ou algum elemento
            # Se a página ainda estiver na tela de login, isso indicará problema
            current_url = page.url
            print(f"URL atual após login: {current_url}")
            
            # Se ainda estiver na página de login, pode indicar falha no login
            if 'login' in current_url.lower():
                print("AVISO: A página pode ainda estar na tela de login. Verificando...")
                # Aguardar um pouco mais e verificar novamente
                time.sleep(2)
                current_url = page.url
                if 'login' in current_url.lower():
                    erro_msg = "Falha no login: A página ainda está na tela de login."
                    interface.atualizar_progresso(erro_msg, 0)
                    print(erro_msg)
                    return None
        except Exception as e:
            print(f"AVISO: Não foi possível verificar o estado da página: {str(e)}")
            # Continua mesmo assim, pois pode ser que a página esteja correta
        
        # Configurar a página para não baixar imagens (otimização)
        # IMPORTANTE: Isso deve ser feito ANTES de qualquer navegação adicional
        print("[LOG] Configurando bloqueio de imagens...")
        sys.stdout.flush()
        try:
            print("[LOG] Executando page.route()...")
            sys.stdout.flush()
            page.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
            print("[LOG] page.route() executado com sucesso")
            sys.stdout.flush()
            print("[LOG] Bloqueio de imagens configurado com sucesso")
            sys.stdout.flush()
        except Exception as e:
            print(f"[LOG] ERRO ao configurar bloqueio de imagens: {str(e)}")
            print(f"[LOG] Traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            # Continua mesmo assim
        
        print("[LOG] ===== PONTO DE VERIFICAÇÃO 1: Após bloqueio de imagens =====")
        sys.stdout.flush()
        print("[LOG] Preparando para iniciar extração...")
        sys.stdout.flush()
        
        # Login já foi realizado pelo obter_pagina()
        print("[LOG] Atualizando interface com mensagem de login realizado...")
        try:
            interface.atualizar_progresso("Login realizado com sucesso! Iniciando extração...", 10)
            print("[LOG] Interface atualizada com sucesso")
        except Exception as e:
            print(f"[LOG] ERRO ao atualizar interface: {str(e)}")
            print(f"[LOG] Traceback: {traceback.format_exc()}")
        
        print("[LOG] Login confirmado. Preparando para iniciar extração...")
        print(f"[LOG] Unidades selecionadas: {unidades_selecionadas}")
        print(f"[LOG] Modo teste: {modo_teste}, Limite: {limite_teste}")
        
        # Verificar se a página ainda está acessível
        print("[LOG] Verificando se a página ainda está acessível...")
        try:
            current_url = page.url
            print(f"[LOG] URL atual antes de iniciar extração: {current_url}")
            print(f"[LOG] Título da página: {page.title()}")
        except Exception as e:
            print(f"[LOG] AVISO: Não foi possível obter informações da página: {str(e)}")
            print(f"[LOG] Traceback: {traceback.format_exc()}")
        
        # Chama a função principal com a interface para mostrar progresso
        print("[LOG] ===== INICIANDO CHAMADA PARA listar_presos_up() =====")
        print(f"[LOG] Parâmetros: page={type(page)}, interface={type(interface)}, unidades={unidades_selecionadas}")
        
        try:
            resultado = listar_presos_up(
                page, 
                interface=interface,
                unidades_selecionadas=unidades_selecionadas,
                modo_teste=modo_teste,
                limite_teste=limite_teste
            )
            print("[LOG] ===== RETORNO DE listar_presos_up() =====")
            print(f"[LOG] Resultado recebido: {resultado is not None}")
        except Exception as e:
            print(f"[LOG] ERRO ao chamar listar_presos_up(): {str(e)}")
            print(f"[LOG] Traceback completo: {traceback.format_exc()}")
            resultado = None
            print("[LOG] ===== RETORNO DE listar_presos_up() =====")
        finally:
            # Sempre fecha o navegador/Playwright ao terminar (evita EPIPE ao fechar o app)
            try:
                if page is not None and hasattr(page, '_browser') and hasattr(page, '_playwright'):
                    print("[LOG] Fechando browser do login alternativo...")
                    try:
                        page._browser.close()
                    except Exception:
                        pass
                    try:
                        page._playwright.stop()
                    except Exception:
                        pass
                elif login is not None and hasattr(login, 'fechar'):
                    try:
                        login.fechar()
                    except Exception:
                        pass
            except Exception:
                pass

        # Verifica o resultado
        if resultado:
            caminho_excel = resultado['caminho_excel']
            interface.atualizar_progresso(f"Processamento concluído com sucesso! Arquivo salvo em:\n{caminho_excel}", 100)
        else:
            interface.atualizar_progresso("Operação cancelada ou finalizada com erro.", 0)
                
    except TimeoutError as e:
        # Erro específico de timeout
        erro_msg = (
            f"Timeout ao processar operação: {str(e)}\n\n"
            "O sistema pode estar lento ou indisponível.\n"
            "Tente novamente em alguns instantes."
        )
        print(erro_msg)
        print(traceback.format_exc())
        interface.atualizar_progresso(erro_msg, 0)
    except AttributeError as e:
        # Erro específico quando page é None
        if "'NoneType' object has no attribute" in str(e):
            erro_msg = (
                "Erro ao obter página logada: Timeout excedido.\n\n"
                "Possíveis causas:\n"
                "- Problemas de conexão com a internet\n"
                "- Sistema Canaimé temporariamente indisponível\n"
                "- Credenciais inválidas ou expiradas\n"
                "- Timeout muito curto para a operação\n\n"
                "Tente novamente ou verifique sua conexão."
            )
            print(erro_msg)
            print(traceback.format_exc())
            interface.atualizar_progresso(erro_msg, 0)
        else:
            raise
    except Exception as e:
        # Em caso de erro genérico, exibe na interface
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
