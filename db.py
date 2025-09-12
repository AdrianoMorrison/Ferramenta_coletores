import pyodbc

def conectar():
    """Cria e retorna uma conexão com o banco de dados."""
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=192.168.9.200;"
        "DATABASE=DbLogistica;"
        "UID=Logistica_OPCD;"
        "PWD=Log1_Op@CD123;"
    )

def verificar_login(usuario, senha):
    """Verifica as credenciais de login no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuario WHERE IDUsuario=? AND Senha=? AND Ativo=1", 
                    (usuario, senha))
    resultado = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return resultado > 0

def usuario_existe(id_usuario, email):
    """Verifica se um usuário já existe pelo ID ou email."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuario WHERE IDUsuario=? OR Email=?", 
                    (id_usuario, email))
    existe = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return existe > 0

def inserir_usuario(id_usuario, nome_usuario, email, senha):
    """Insere um novo usuário no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    sql = """
    INSERT INTO Usuario (IDUsuario, NomeUsuario, Email, Senha, Ativo)
    VALUES (?, ?, ?, ?, 1)
    """
    cursor.execute(sql, (id_usuario, nome_usuario, email, senha))
    conn.commit()
    cursor.close()
    conn.close()

def get_totais_coletores():
    """
    Conecta ao SQL Server, executa a consulta de totais e retorna os resultados.
    
    Retorna:
        dict: Um dicionário com os totais por status (Em Operação, Disponível, Conserto).
              Retorna um dicionário vazio em caso de erro.
    """
    totais = {
        'EM OPERACAO': 0,
        'DISPONIVEL': 0,
        'EM CONSERTO': 0
    }
    
    try:
        conn = conectar()
        cursor = conn.cursor()

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
            FROM
                COLETORES_CADASTRO A WITH (NOLOCK)
            LEFT JOIN
                (
                    SELECT
                        A.IDColetor,
                        B.IDRegistro
                    FROM
                        (
                            SELECT
                                MAX(DataRegistro) AS DataRegistro,
                                IDColetor
                            FROM
                                LG_ControleColetores
                            GROUP BY
                                IDColetor
                        ) A
                    LEFT JOIN
                        LG_ControleColetores B ON A.IDColetor = B.IDColetor AND A.DataRegistro = B.DataRegistro
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
        cursor.execute(sql_query)
        resultados = cursor.fetchall()
        conn.close()
        
        for qtd, status in resultados:
            if status in totais:
                totais[status] = qtd
                
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Erro ao conectar ou consultar o banco de dados: {sqlstate}")
        
    return totais

# Exemplo de como usar a função:
if __name__ == "__main__":
    totais_coletores = get_totais_coletores()
    print("Totais de Coletores:", totais_coletores)


# atalho opcional para compatibilidade
get_conn = conectar
