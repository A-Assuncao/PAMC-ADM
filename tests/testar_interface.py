#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar a interface gráfica isoladamente.
"""

import os
import sys
import time
import random
import traceback
import threading
import tkinter as tk
from typing import List, Dict

# Adicionar diretório raiz ao path para permitir importações relativas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Importar a interface
    from src.ui.interface_selecao import criar_interface, SeletorUnidades
    
    def simular_processamento(unidades: List[str], opcoes_teste: Dict = None):
        """
        Simula o processamento de unidades para testar a interface.
        
        Args:
            unidades: Lista de unidades selecionadas
            opcoes_teste: Dicionário com as opções de teste (opcional)
        """
        if opcoes_teste is None:
            opcoes_teste = {}
            
        print(f"Processando unidades: {', '.join(unidades)}")
        print(f"Opções de teste: {opcoes_teste}")
        
        # Obter a instância atual da interface
        interface = None
        for widget in tk._default_root.winfo_children():
            if isinstance(widget, SeletorUnidades):
                interface = widget
                break
        
        if not interface:
            print("Não foi possível encontrar a instância da interface!")
            return
        
        # Iniciar processamento
        interface.atualizar_progresso("Iniciando processamento...", 0)
        time.sleep(1)
        
        # Simular login
        interface.atualizar_progresso("Realizando login...", 5)
        time.sleep(2)
        interface.atualizar_progresso("Login realizado com sucesso!", 10)
        time.sleep(0.5)
        
        # Processar unidades
        for i, unidade in enumerate(unidades):
            # Verificar cancelamento
            if interface.verificar_cancelamento():
                interface.atualizar_progresso("Processamento cancelado pelo usuário", 0)
                return
            
            # Progresso da unidade atual
            progresso_base = 10 + (i / len(unidades)) * 80
            interface.atualizar_progresso(f"Processando unidade {unidade} ({i+1}/{len(unidades)})...", progresso_base)
            
            # Simular extração de presos
            total_presos = 5 if opcoes_teste.get('modo_teste', False) else 15
            for j in range(total_presos):
                # Verificar cancelamento
                if interface.verificar_cancelamento():
                    interface.atualizar_progresso("Processamento cancelado pelo usuário", 0)
                    return
                
                # Simular processamento
                time.sleep(random.uniform(0.1, 0.3))
                
                # Atualizar progresso
                percentual = progresso_base + (j / total_presos) * (80 / len(unidades))
                interface.atualizar_progresso(f"Extraindo dados: {j+1}/{total_presos}", percentual)
            
            print(f"Concluído processamento da unidade {unidade}: {total_presos} presos")
        
        # Finalizar
        interface.atualizar_progresso("Salvando resultados...", 90)
        time.sleep(1)
        interface.atualizar_progresso("Processamento finalizado com sucesso!", 100)
        print("Processamento finalizado!")
    
    def main():
        print("Iniciando teste da interface gráfica...")
        
        try:
            # Criar interface
            app = criar_interface()
            
            # Configurar callback de processamento
            app.definir_callback_processamento(simular_processamento)
            
            # Iniciar loop principal
            print("Interface pronta. Use os botões para testar.")
            app.mainloop()
            
        except Exception as e:
            print(f"Erro na interface: {str(e)}")
            traceback.print_exc()
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"Erro ao inicializar: {str(e)}")
    traceback.print_exc() 