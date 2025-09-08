import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import db  # conexão com banco


# Função para gerar IDUsuario automaticamente
def gerar_id_usuario(nome_completo):
    nome_completo = nome_completo.upper().strip()
    partes = nome_completo.split()
    if len(partes) < 2:
        return None
    primeiro = partes[0].lower()
    ultimo = partes[-1].lower()
    return f"{primeiro}.{ultimo}"


# --- Ações ---
def login():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()

    if not usuario or not senha:
        messagebox.showerror("Erro", "Preencha todos os campos!")
        return

    if db.verificar_login(usuario, senha):
        root.withdraw()  # esconde a janela de login
        import ui_principal
        ui_principal.abrir_ui_principal(usuario)

    else:
        messagebox.showerror("Erro", "Usuário ou senha inválidos!")


def esqueci_senha():
    messagebox.showinfo("Esqueci minha senha", 
                        "Procure o administrador de sistemas para resetar sua senha.")


def cadastrar_usuario():
    nome = entry_nome.get().strip()
    email = entry_email.get().strip()
    senha = entry_senha_cadastro.get().strip()

    if not nome or not email or not senha:
        messagebox.showerror("Erro", "Preencha todos os campos!")
        return

    # Validação do e-mail corporativo
    # Validação do e-mail corporativo
    dominios_corporativos = (
        "@gruposoma.com.br",
        "@farmrio.com.br",
        "@somagrupo.com.br",
        "@azzas2154.com.br",
        "@animale.com.br"
    )
    if not email.endswith(dominios_corporativos):
        messagebox.showerror("Erro", f"O e-mail deve ser corporativo ({dominios_corporativos})")
        return

    id_usuario = gerar_id_usuario(nome)
    if not id_usuario:
        messagebox.showerror("Erro", "Digite nome e sobrenome!")
        return

    try:
        if db.usuario_existe(id_usuario, email):
            messagebox.showerror("Erro", "Usuário ou e-mail já cadastrados!")
            return

        db.inserir_usuario(id_usuario, nome.upper(), email, senha)
        messagebox.showinfo("Sucesso", f"Usuário cadastrado!\nID: {id_usuario}")
        entry_nome.delete(0, tk.END)
        entry_email.delete(0, tk.END)
        entry_senha_cadastro.delete(0, tk.END)
        mostrar_login()  # volta para tela de login
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao cadastrar: {e}")


# --- Alternar telas ---
def mostrar_login():
    frame_cadastro.pack_forget()
    frame_login.pack(pady=10)


def mostrar_cadastro():
    frame_login.pack_forget()
    frame_cadastro.pack(pady=10)


# --- Janela principal ---
root = tk.Tk()
root.title("Sistema de Cadastro e Login")
root.geometry("400x550")

# --- Logo ---
logo_path = r"C:\Users\adriano.soares\Desktop\python\Cadastro_coletores\assets\Logo Minimalista AZZAS.png"
logo_img = Image.open(logo_path)
logo_img = logo_img.resize((120, 120))
logo_tk = ImageTk.PhotoImage(logo_img)
tk.Label(root, image=logo_tk).pack(pady=10)

# --- Frame Login ---
frame_login = tk.Frame(root)

tk.Label(frame_login, text="Usuário:").pack(pady=5)
entry_usuario = tk.Entry(frame_login, width=30)
entry_usuario.pack(pady=5)

tk.Label(frame_login, text="Senha:").pack(pady=5)
entry_senha = tk.Entry(frame_login, show="*", width=30)
entry_senha.pack(pady=5)

tk.Button(frame_login, text="Login", command=login).pack(pady=10)
tk.Button(frame_login, text="Esqueci minha senha", command=esqueci_senha).pack(pady=5)
tk.Button(frame_login, text="Cadastrar novo usuário", command=mostrar_cadastro).pack(pady=5)

frame_login.pack(pady=10)


# --- Frame Cadastro ---
frame_cadastro = tk.Frame(root)

tk.Label(frame_cadastro, text="Nome completo:").pack(pady=5)
entry_nome = tk.Entry(frame_cadastro, width=30)
entry_nome.pack(pady=5)

tk.Label(frame_cadastro, text="E-mail corporativo:").pack(pady=5)
entry_email = tk.Entry(frame_cadastro, width=30)
entry_email.pack(pady=5)

tk.Label(frame_cadastro, text="Senha:").pack(pady=5)
entry_senha_cadastro = tk.Entry(frame_cadastro, show="*", width=30)
entry_senha_cadastro.pack(pady=5)

tk.Button(frame_cadastro, text="Cadastrar", command=cadastrar_usuario).pack(pady=10)
tk.Button(frame_cadastro, text="Voltar ao Login", command=mostrar_login).pack(pady=5)

# Inicialmente mostra login
frame_login.pack(pady=10)

root.mainloop()
