import tkinter as tk
from tkinter import ttk
from datetime import datetime
from db import get_totais_coletores # Importa a função do arquivo db_service.py

def abrir_ui_principal(usuario_logado):
    """
    Cria e exibe a interface de controle de coletores WMS.
    
    Args:
        usuario_logado (str): O nome de usuário logado na aplicação.
    """
    janela = tk.Toplevel()
    janela.title("Controle Coletores WMS")
    janela.geometry("1000x600")
    janela.resizable(False, False)

    # Variável para rastrear a ação
    acao_var = tk.StringVar(value="")

    # --- Funções de Lógica ---
    def carregar_totais():
        """Carrega os totais do módulo db_service e atualiza os labels."""
        totais = get_totais_coletores()
        lbl_em_operacao.config(text=str(totais.get('EM OPERACAO', 0)))
        lbl_disponiveis.config(text=str(totais.get('DISPONIVEL', 0)))
        lbl_conserto.config(text=str(totais.get('EM CONSERTO', 0)))

    def atualizar_ui(event=None):
        """Mostra/esconde frames com base na ação selecionada."""
        acao_selecionada = acao_var.get()
        
        frame_testes.pack_forget()
        frame_info.pack_forget()
        frame_datas.pack_forget()
        
        if acao_selecionada in ["Devolução término operação", "Envio Conserto"]:
            frame_testes.pack(fill="x", padx=10, pady=10)
        
        if acao_selecionada in ["Envio Conserto", "Retorno Conserto", "Coletor Extraviado", "Coletor Inativo"]:
            frame_info.pack(fill="x", padx=10, pady=10)
            
        if acao_selecionada in ["Envio Conserto", "Retorno Conserto"]:
            frame_datas.pack(fill="x", padx=10, pady=10)

    def salvar_dados():
        """Coleta os dados da interface para salvar no banco."""
        acao = acao_var.get()
        coletor = entry_coletor.get()
        responsavel = entry_responsavel.get()
        
        if not acao or not coletor or not responsavel:
            print("Por favor, preencha todos os campos obrigatórios.")
            return

        dados = {
            "acao": acao,
            "coletor": coletor,
            "responsavel": responsavel,
            "usuario_registro": usuario_logado,
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "teste_realizado": var_teste.get(),
            "defeito_detectado": var_defeito.get(),
            "sinaliza_conserto": var_conserto.get(),
            "defeitos_encontrados": txt_defeitos.get("1.0", tk.END).strip(),
            "consideracoes": txt_consideracoes.get("1.0", tk.END).strip(),
            "data_envio_conserto": entry_envio.get(),
            "numero_chamado": entry_chamado.get(),
            "data_retorno_conserto": entry_retorno.get()
        }

        print("Dados a serem salvos:", dados)
        # TODO: Chame aqui a função para inserir os dados no banco de dados
        # import db_service
        # db_service.salvar_registro(dados)


    # --- UI Layout ---
    tk.Label(janela, text="Controle Coletores WMS", font=("Arial", 16, "bold")).pack(pady=10)
    
    frame_top = tk.Frame(janela)
    frame_top.pack(fill="x", padx=10, pady=5)
    
    tk.Label(frame_top, text="Em operação", fg="blue").grid(row=0, column=0, padx=20)
    lbl_em_operacao = tk.Label(frame_top, text="0", font=("Arial", 14))
    lbl_em_operacao.grid(row=1, column=0)
    
    tk.Label(frame_top, text="Disponíveis", fg="green").grid(row=0, column=1, padx=20)
    lbl_disponiveis = tk.Label(frame_top, text="0", font=("Arial", 14))
    lbl_disponiveis.grid(row=1, column=1)
    
    tk.Label(frame_top, text="Enviado para Conserto", fg="red").grid(row=0, column=2, padx=20)
    lbl_conserto = tk.Label(frame_top, text="0", font=("Arial", 14))
    lbl_conserto.grid(row=1, column=2)

    ttk.Button(frame_top, text="Atualizar Totais", command=carregar_totais).grid(row=1, column=3, padx=20)
    
    # --- Seção de Ações ---
    frame_acoes = tk.LabelFrame(janela, text="Escolha uma ação")
    frame_acoes.pack(fill="x", padx=10, pady=10)
    
    acoes = [
        "Entrega Início operação", "Devolução término operação", "Envio Conserto",
        "Retorno Conserto", "Coletor Extraviado", "Coletor Inativo"
    ]
    
    for i, acao in enumerate(acoes):
        rb = tk.Radiobutton(frame_acoes, text=acao, variable=acao_var, value=acao)
        rb.grid(row=0, column=i, padx=10)
        rb.bind("<Button-1>", atualizar_ui)

    # --- Frames que serão controlados dinamicamente ---
    frame_dados = tk.Frame(janela)
    frame_dados.pack(fill="x", padx=10, pady=10)
    
    tk.Label(frame_dados, text="Coletor:").grid(row=0, column=0, sticky="e")
    entry_coletor = tk.Entry(frame_dados, width=20)
    entry_coletor.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_dados, text="Responsável:").grid(row=0, column=2, sticky="e")
    entry_responsavel = tk.Entry(frame_dados, width=30)
    entry_responsavel.grid(row=0, column=3, padx=5)
    
    frame_testes = tk.Frame(janela)
    frame_info = tk.Frame(janela)
    frame_datas = tk.Frame(janela)

    def add_radio(frame, texto, row):
        tk.Label(frame, text=texto).grid(row=row, column=0, sticky="w")
        var = tk.StringVar(value="NÃO")
        tk.Radiobutton(frame, text="SIM", variable=var, value="SIM").grid(row=row, column=1)
        tk.Radiobutton(frame, text="NÃO", variable=var, value="NÃO").grid(row=row, column=2)
        return var
    
    var_teste = add_radio(frame_testes, "Teste realizado?", 0)
    var_defeito = add_radio(frame_testes, "Detectado defeito?", 1)
    var_conserto = add_radio(frame_testes, "Sinaliza conserto?", 2)
    
    tk.Label(frame_info, text="Defeitos encontrados:").grid(row=0, column=0, sticky="w")
    txt_defeitos = tk.Text(frame_info, height=4, width=40)
    txt_defeitos.grid(row=1, column=0, padx=5)
    
    tk.Label(frame_info, text="Considerações:").grid(row=0, column=1, sticky="w")
    txt_consideracoes = tk.Text(frame_info, height=4, width=40)
    txt_consideracoes.grid(row=1, column=1, padx=5)

    tk.Label(frame_datas, text="Data Envio Conserto:").grid(row=0, column=0)
    entry_envio = tk.Entry(frame_datas, width=20)
    entry_envio.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_datas, text="Nº Chamado:").grid(row=0, column=2)
    entry_chamado = tk.Entry(frame_datas, width=20)
    entry_chamado.grid(row=0, column=3, padx=5)
    
    tk.Label(frame_datas, text="Data Retorno Conserto:").grid(row=0, column=4)
    entry_retorno = tk.Entry(frame_datas, width=20)
    entry_retorno.grid(row=0, column=5, padx=5)
    
    frame_botoes = tk.Frame(janela)
    frame_botoes.pack(pady=15)
    
    ttk.Button(frame_botoes, text="Salvar", command=salvar_dados).pack(side="left", padx=10)
    ttk.Button(frame_botoes, text="Cancelar", command=janela.destroy).pack(side="left", padx=10)
    
    carregar_totais()
    
    janela.mainloop()

if __name__ == "__main__":
    # Exemplo de como chamar a interface a partir de um arquivo principal
    root = tk.Tk()
    root.withdraw()
    abrir_ui_principal("admin")
    root.mainloop()