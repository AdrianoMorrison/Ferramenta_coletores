# DB.py
import os
import pyodbc
from typing import Dict, Tuple

# ---------------------------
# Configuração (use .env/ambiente)
# ---------------------------
CONFIG = {
    "SERVER": os.getenv("DB_SERVER", "192.168.9.200"),
    "DATABASE": os.getenv("DB_NAME", "DbLogistica"),
    "UID": os.getenv("DB_USER", "Logistica_OPCD"),
    "PWD": os.getenv("DB_PASS", "Log1_Op@CD123"),
    # Lista de drivers aceitos em ordem de preferência
    "PREFERRED_DRIVERS": [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
    ],
    # Outras opções úteis
    "CONNECT_TIMEOUT": os.getenv("DB_CONNECT_TIMEOUT", "5"),  # segundos
    "ENCRYPT": os.getenv("DB_ENCRYPT", "yes"),                # Driver 18 exige encrypt
    "TRUST_CERT": os.getenv("DB_TRUST_CERT", "yes"),          # ok se não usar CA corporativa
}

def _pick_driver() -> str:
    """Escolhe o primeiro driver disponível da lista de preferência."""
    installed = set(pyodbc.drivers())
    for drv in CONFIG["PREFERRED_DRIVERS"]:
        if drv in installed:
            return drv
    raise RuntimeError(
        "Nenhum driver ODBC do SQL Server compatível foi encontrado.\n"
        f"Instalados: {sorted(installed)}\n"
        "Instale, por exemplo: 'ODBC Driver 18 for SQL Server' (x64) "
        "ou ajuste o nome do driver na connection string."
    )

def _make_cnxn_string(driver: str) -> str:
    # Para Driver 18: Encrypt=YES é padrão; se não tiver CA, use TrustServerCertificate=YES.
    # Para Driver 17/13, esses parâmetros são ignorados se não suportados.
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={CONFIG['SERVER']};"
        f"DATABASE={CONFIG['DATABASE']};"
        f"UID={CONFIG['UID']};"
        f"PWD={CONFIG['PWD']};"
        f"Encrypt={CONFIG['ENCRYPT']};"
        f"TrustServerCertificate={CONFIG['TRUST_CERT']};"
        f"Connection Timeout={CONFIG['CONNECT_TIMEOUT']};"
    )

def conectar() -> pyodbc.Connection:
    """
    Cria e retorna uma conexão com o SQL Server tentando drivers compatíveis.
    Levanta uma exceção com mensagem amigável se não houver driver.
    """
    driver = _pick_driver()
    conn_str = _make_cnxn_string(driver)
    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as ex:
        # Mensagem melhor para IM002 (fonte de dados/driver)
        if ex.args and isinstance(ex.args[0], str) and ex.args[0].startswith("IM002"):
            raise RuntimeError(
                "Falha ao abrir conexão ODBC (IM002). "
                "Verifique se o driver está instalado e corresponde à arquitetura (x64/x86). "
                f"Tentado: {driver}"
            ) from ex
        raise

def verificar_login(usuario: str, senha: str) -> bool:
    """Verifica as credenciais de login no banco de dados."""
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Usuario WHERE IDUsuario=? AND Senha=? AND Ativo=1",
            (usuario, senha),
        )
        return cur.fetchone()[0] > 0

def usuario_existe(id_usuario: str, email: str) -> bool:
    """Verifica se um usuário já existe pelo ID ou email."""
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Usuario WHERE IDUsuario=? OR Email=?",
            (id_usuario, email),
        )
        return cur.fetchone()[0] > 0

def inserir_usuario(id_usuario: str, nome_usuario: str, email: str, senha: str) -> None:
    """Insere um novo usuário no banco de dados."""
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Usuario (IDUsuario, NomeUsuario, Email, Senha, Ativo)
            VALUES (?, ?, ?, ?, 1)
            """,
            (id_usuario, nome_usuario, email, senha),
        )
        conn.commit()

def get_totais_coletores() -> Dict[str, int]:
    """
    Executa a consulta de totais dos coletores.
    Retorna um dicionário com 'EM OPERACAO', 'DISPONIVEL', 'EM CONSERTO'.
    """
    totais = {"EM OPERACAO": 0, "DISPONIVEL": 0, "EM CONSERTO": 0}
    sql_query = """
        SELECT
            COUNT(DISTINCT LTRIM(RTRIM(A.IDcoletores))) AS QTColetores,
            CASE
                WHEN B.IDRegistro = 4 THEN 'DISPONIVEL'
                WHEN B.IDRegistro = 1 THEN 'EM OPERACAO'
                WHEN B.IDRegistro = 3 THEN 'EM CONSERTO'
                WHEN B.IDRegistro = 5 THEN 'EXTRAVIADO'
                WHEN B.IDRegistro = 6 THEN 'INATIVO'
                WHEN B.IDRegistro IS NULL OR B.IDRegistro = 2 THEN 'DISPONIVEL'
            END AS STATUS_COLETOR
        FROM COLETORES_CADASTRO A WITH (NOLOCK)
        LEFT JOIN (
            SELECT A.IDColetor, B.IDRegistro
            FROM (
                SELECT MAX(DataRegistro) AS DataRegistro, IDColetor
                FROM LG_ControleColetores
                GROUP BY IDColetor
            ) A
            LEFT JOIN LG_ControleColetores B
              ON A.IDColetor = B.IDColetor AND A.DataRegistro = B.DataRegistro
        ) B ON LTRIM(RTRIM(A.IDcoletores)) = B.IDColetor
        GROUP BY
            CASE
                WHEN B.IDRegistro = 4 THEN 'DISPONIVEL'
                WHEN B.IDRegistro = 1 THEN 'EM OPERACAO'
                WHEN B.IDRegistro = 3 THEN 'EM CONSERTO'
                WHEN B.IDRegistro = 5 THEN 'EXTRAVIADO'
                WHEN B.IDRegistro = 6 THEN 'INATIVO'
                WHEN B.IDRegistro IS NULL OR B.IDRegistro = 2 THEN 'DISPONIVEL'
            END;
    """
    try:
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute(sql_query)
            for qtd, status in cur.fetchall():
                if status in totais:
                    totais[status] = qtd
    except pyodbc.Error as ex:
        print(f"Erro ao conectar/consultar o banco: {ex}")
    return totais

# Atalho opcional:
get_conn = conectar

if __name__ == "__main__":
    print("Drivers instalados:", pyodbc.drivers())
    print("Totais de Coletores:", get_totais_coletores())
