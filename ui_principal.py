import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import get_totais_coletores
from mov_validacoes import (
    processar_movimentacao,
    nome_coletor_ou_usuario,
    status_do_coletor,
)


def abrir_ui_principal(usuario_logado: str):
    """
    Interface principal de controle de coletores WMS.
    """
    janela = tk.Toplevel()
    janela.title("Controle Coletores WMS")
    janela.geometry("1000x600")
    janela.resizable(False, False)

    # -------------------------
    # Estado
    # -------------------------
    acao_var = tk.StringVar(value="")  # ação escolhida

    # -------------------------
    # Funções
    # -------------------------
    def carregar_totais():
        totais = get_totais_coletores()
        lbl_em_operacao.config(text=str(totais.get("EM OPERACAO", 0)))
        lbl_disponiveis.config(text=str(totais.get("DISPONIVEL", 0)))
        lbl_conserto.config(text=str(totais.get("EM CONSERTO", 0)))

    def atualizar_ui(*_):
        acao = acao_var.get()
        # esconde tudo
        frame_testes.pack_forget()
        frame_info.pack_forget()
        frame_datas.pack_forget()

        # mostra conforme regras
        if acao in ["Devolução término operação", "Envio Conserto"]:
            frame_testes.pack(fill="x", padx=10, pady=10)

        if acao in ["Envio Conserto", "Retorno Conserto", "Coletor Extraviado", "Coletor Inativo"]:
            frame_info.pack(fill="x", padx=10, pady=10)

        if acao in ["Envio Conserto", "Retorno Conserto"]:
            frame_datas.pack(fill="x", padx=10, pady=10)

    def on_enter_coletor(event=None):
        _id = entry_coletor.get().strip()
        if not _id:
            return
        try:
            serial = nome_coletor_ou_usuario(_id, modo="COLETOR")
            st, last_colab = status_do_coletor(_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao consultar coletor: {e}")
            return

        if serial:
            texto = f"{serial} | Status: {st}"
            if last_colab:
                texto += f" (colab: {last_colab})"
            lbl_info_coletor.config(text=texto, fg="gray")
        else:
            lbl_info_coletor.config(text="Não encontrado", fg="red")

        entry_responsavel.focus_set()
        entry_responsavel.selection_range(0, tk.END)

    def on_enter_resp(event=None):
        _id = entry_responsavel.get().strip()
        if not _id:
            return
        try:
            nome = nome_coletor_ou_usuario(_id, modo="USUARIO")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao consultar usuário: {e}")
            return

        if nome:
            lbl_info_resp.config(text=nome, fg="gray")
        else:
            lbl_info_resp.config(text="Não encontrado", fg="red")

    def limpar_form():
        # campos principais
        entry_coletor.delete(0, tk.END)
        entry_responsavel.delete(0, tk.END)

        # textos/observações
        txt_defeitos.delete("1.0", tk.END)
        txt_consideracoes.delete("1.0", tk.END)

        # datas e chamado
        entry_envio.delete(0, tk.END)
        entry_chamado.delete(0, tk.END)
        entry_retorno.delete(0, tk.END)

        # reset de ação e rádios
        acao_var.set("")
        var_teste.set("NÃO")
        var_defeito.set("NÃO")
        var_conserto.set("NÃO")

        # esconde frames condicionais
        frame_testes.pack_forget()
        frame_info.pack_forget()
        frame_datas.pack_forget()

        # limpa labels auxiliares
        lbl_info_coletor.config(text="")
        lbl_info_resp.config(text="")

        # foco de volta
        entry_coletor.focus_set()

    def salvar_dados():
        acao_ui = acao_var.get()
        id_coletor = entry_coletor.get().strip()
        id_resp = entry_responsavel.get().strip()

        # lista de defeitos (se tiver listbox específica, monte aqui)
        lista_defeitos = []

        ok, msg = processar_movimentacao(
            acao_ui=acao_ui,
            id_coletor=id_coletor,
            id_resp=id_resp,
            realizado_teste=(var_teste.get() == "SIM"),
            detectado_defeito=(var_defeito.get() == "SIM"),
            sinaliza_conserto=(var_conserto.get() == "SIM"),
            observacao=(txt_defeitos.get("1.0", "end").strip()
                        or txt_consideracoes.get("1.0", "end").strip()
                        or None),
            resp_processo=usuario_logado,
            data_envio_conserto=(entry_envio.get().strip() or None),   # 'YYYY-MM-DD'
            chamado=(entry_chamado.get().strip() or None),
            data_retorno_conserto=(entry_retorno.get().strip() or None),
            lista_defeitos_escolhidos=lista_defeitos
        )

        if ok:
            messagebox.showinfo("Sucesso", msg)
            carregar_totais()
            limpar_form()
        else:
            messagebox.showerror("Validação", msg)

    # -------------------------
    # Layout
    # -------------------------
    tk.Label(janela, text="Controle Coletores WMS", font=("Arial", 18, "bold")).pack(pady=12)

    frame_top = tk.Frame(janela)
    frame_top.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_top, text="Em operação", fg="blue", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=20)
    lbl_em_operacao = tk.Label(frame_top, text="0", font=("Arial", 16))
    lbl_em_operacao.grid(row=1, column=0)

    tk.Label(frame_top, text="Disponíveis", fg="green", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=20)
    lbl_disponiveis = tk.Label(frame_top, text="0", font=("Arial", 16))
    lbl_disponiveis.grid(row=1, column=1)

    tk.Label(frame_top, text="Enviado para Conserto", fg="red", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=20)
    lbl_conserto = tk.Label(frame_top, text="0", font=("Arial", 16))
    lbl_conserto.grid(row=1, column=2)

    ttk.Button(frame_top, text="Atualizar Totais", command=carregar_totais).grid(row=1, column=3, padx=20)

    # Ações
    frame_acoes = tk.LabelFrame(janela, text="Escolha uma ação")
    frame_acoes.pack(fill="x", padx=10, pady=10)

    acoes = [
        "Entrega Início operação",
        "Devolução término operação",
        "Envio Conserto",
        "Retorno Conserto",
        "Coletor Extraviado",
        "Coletor Inativo",
    ]
    for i, ac in enumerate(acoes):
        rb = tk.Radiobutton(frame_acoes, text=ac, variable=acao_var, value=ac)
        rb.grid(row=0, column=i, padx=10)
    acao_var.trace_add("write", atualizar_ui)

    # Dados principais
    frame_dados = tk.Frame(janela)
    frame_dados.pack(fill="x", padx=10, pady=10)

    tk.Label(frame_dados, text="Coletor:").grid(row=0, column=0, sticky="e")
    entry_coletor = tk.Entry(frame_dados, width=25)
    entry_coletor.grid(row=0, column=1, padx=5)
    entry_coletor.bind("<Return>", on_enter_coletor)

    tk.Label(frame_dados, text="Responsável:").grid(row=0, column=2, sticky="e")
    entry_responsavel = tk.Entry(frame_dados, width=35)
    entry_responsavel.grid(row=0, column=3, padx=5)
    entry_responsavel.bind("<Return>", on_enter_resp)

    # labels de informações abaixo dos campos
    lbl_info_coletor = tk.Label(frame_dados, text="", fg="gray")
    lbl_info_coletor.grid(row=1, column=1, sticky="w", pady=(3, 0))
    lbl_info_resp = tk.Label(frame_dados, text="", fg="gray")
    lbl_info_resp.grid(row=1, column=3, sticky="w", pady=(3, 0))

    # Frames variáveis
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
    txt_defeitos = tk.Text(frame_info, height=4, width=48)
    txt_defeitos.grid(row=1, column=0, padx=5)

    tk.Label(frame_info, text="Considerações:").grid(row=0, column=1, sticky="w")
    txt_consideracoes = tk.Text(frame_info, height=4, width=48)
    txt_consideracoes.grid(row=1, column=1, padx=5)

    tk.Label(frame_datas, text="Data Envio Conserto (YYYY-MM-DD):").grid(row=0, column=0, sticky="e")
    entry_envio = tk.Entry(frame_datas, width=20)
    entry_envio.grid(row=0, column=1, padx=5)

    tk.Label(frame_datas, text="Nº Chamado:").grid(row=0, column=2, sticky="e")
    entry_chamado = tk.Entry(frame_datas, width=20)
    entry_chamado.grid(row=0, column=3, padx=5)

    tk.Label(frame_datas, text="Data Retorno Conserto (YYYY-MM-DD):").grid(row=0, column=4, sticky="e")
    entry_retorno = tk.Entry(frame_datas, width=20)
    entry_retorno.grid(row=0, column=5, padx=5)

    # Botões
    frame_botoes = tk.Frame(janela)
    frame_botoes.pack(pady=15)
    ttk.Button(frame_botoes, text="Salvar", command=salvar_dados).pack(side="left", padx=10)
    ttk.Button(frame_botoes, text="Cancelar", command=limpar_form).pack(side="left", padx=10)

    # Inicializa
    carregar_totais()
    entry_coletor.focus_set()

    # Importante: não chame mainloop aqui, pois a janela é Toplevel.


if __name__ == "__main__":
    # Execução direta para testes locais
    root = tk.Tk()
    root.withdraw()  # esconde a raiz
    abrir_ui_principal("admin")
    root.mainloop()
