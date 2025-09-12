# mov_validacoes.py
# ------------------------------------------------------------
# Validações e inserts de coletores (SQL Server), alinhado ao db.py
# - junções com LTRIM/RTRIM (sem RIGHT/zero-pad)
# - usa exatamente db.conectar()
# - "último movimento" via ROW_NUMBER (determinístico)
# ------------------------------------------------------------
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
from datetime import datetime
import pyodbc

import db as _db
def get_conn():
    return _db.conectar()

ID_REGISTRO = {
    "ENTREGA":   1,
    "DEVOLUCAO": 2,
    "ENVIO":     3,
    "RETORNO":   4,
    "EXTRAVIO":  5,
    "INATIVO":   6,
}

STATUS_BY_IDREG = {
    1: "EM OPERACAO",
    2: "DISPONIVEL",
    3: "EM CONSERTO",
    4: "DISPONIVEL",
    5: "EXTRAVIADO",
    6: "INATIVO",
    None: "DISPONIVEL",
}

@dataclass
class MovDados:
    id_registro: int
    id_coletor: str
    id_colaborador: Optional[str]
    realizado_teste: bool
    detectado_defeito: bool
    sinaliza_conserto: bool
    observacao: Optional[str]
    resp_processo: str
    data_envio_conserto: Optional[str]   # YYYY-MM-DD
    chamado: Optional[str]
    data_retorno_conserto: Optional[str] # YYYY-MM-DD

@dataclass
class DefeitoItem:
    id_registro: int
    id_coletor: str
    id_defeito: str
    resp_processo: str

def yyyymmdd(date_iso: Optional[str]) -> Optional[str]:
    if not date_iso:
        return None
    dt = datetime.strptime(date_iso, "%Y-%m-%d")
    return dt.strftime("%Y%m%d")

# =========================
# LOOKUPS AUXILIARES
# =========================

def fetch_defeitos_list() -> List[str]:
    sql = (
        "SELECT CASE WHEN LEN(IdDefeito)<2 THEN '0'+CONVERT(VARCHAR,IdDefeito) "
        "            ELSE CONVERT(VARCHAR,IdDefeito) END + ' - ' + DescricaoDefeito "
        "FROM LG_ColetoresDefeito WITH (NOLOCK) ORDER BY IdDefeito"
    )
    with get_conn() as cn, cn.cursor() as cur:
        cur.execute(sql)
        return [r[0] for r in cur.fetchall()]

# =========================
# ÚLTIMO MOVIMENTO (determinístico)
# =========================

def _get_ultimo_mov_do_coletor(id_coletor: str):
    """
    Retorna (IDRegistro:int, IDColaborador) do ÚLTIMO movimento do coletor,
    unificando variações como '73' e '000073' na mesma partição.
    """
    sql = """
    WITH Base AS (
      SELECT
          LTRIM(RTRIM(IDColetor))                         AS IDColetorTrim,
          LTRIM(RTRIM(IDColaborador))                     AS IDColaborador,
          CAST(IDRegistro AS INT)                         AS IDRegistro,   -- <<<<<< AQUI
          DataRegistro,
          /* Normaliza: se for número => '73'; senão => texto trimado */
          COALESCE(CONVERT(VARCHAR(50),
                   TRY_CONVERT(BIGINT, LTRIM(RTRIM(IDColetor)))),
                   LTRIM(RTRIM(IDColetor)))               AS IDColetorNorm
      FROM LG_ControleColetores
    ),
    Movs AS (
      SELECT *,
             ROW_NUMBER() OVER (
               PARTITION BY IDColetorNorm
               ORDER BY DataRegistro DESC, IDRegistro DESC
             ) AS rn
      FROM Base
    )
    SELECT TOP 1 IDRegistro, IDColaborador
    FROM Movs
    WHERE rn = 1
      AND IDColetorNorm = COALESCE(
            CONVERT(VARCHAR(50), TRY_CONVERT(BIGINT, LTRIM(RTRIM(?)))),
            LTRIM(RTRIM(?))
          );
    """
    with get_conn() as cn, cn.cursor() as cur:
        p = id_coletor.strip()
        cur.execute(sql, (p, p))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)


def _status_atual(id_coletor: str) -> Tuple[str, Optional[str]]:
    """
    Mapeia o último IDRegistro para o texto de status e retorna também o colaborador.
    """
    last_idreg, last_colab = _get_ultimo_mov_do_coletor(id_coletor)
    return STATUS_BY_IDREG.get(last_idreg, "DISPONIVEL"), last_colab

# =========================
# VALIDAÇÕES
# =========================

def validar_bipagem(acao: str, id_coletor: Optional[str], id_resp: Optional[str]) -> Tuple[bool, str]:
    id_coletor = (id_coletor or "").strip()
    id_resp    = (id_resp or "").strip()
    if id_coletor == "" and id_resp != "":
        return False, "É necessário bipar o endereço do coletor para processar os dados."
    if id_coletor != "" and id_resp == "" and acao.upper() in ("DEVOLUCAO","ENTREGA","ENVIO","RETORNO"):
        return False, "É necessário bipar o crachá do colaborador para processar os dados."
    return True, ""

def _colaborador_tem_coletor_em_operacao(id_resp: str) -> Optional[str]:
    """
    Retorna o IDColetor *textual* (trimado) se o colaborador estiver, no estado atual,
    com algum coletor EM OPERACAO. Usa a mesma normalização de partição.
    """
    sql = """
    WITH Base AS (
      SELECT
          LTRIM(RTRIM(IDColetor))                         AS IDColetorTrim,
          LTRIM(RTRIM(IDColaborador))                     AS IDColaborador,
          IDRegistro,
          DataRegistro,
          COALESCE(CONVERT(VARCHAR(50),
                   TRY_CONVERT(BIGINT, LTRIM(RTRIM(IDColetor)))),
                   LTRIM(RTRIM(IDColetor)))               AS IDColetorNorm
      FROM LG_ControleColetores
    ),
    Movs AS (
      SELECT *,
             ROW_NUMBER() OVER (
               PARTITION BY IDColetorNorm
               ORDER BY DataRegistro DESC, IDRegistro DESC
             ) AS rn
      FROM Base
    )
    SELECT TOP 1 IDColetorTrim
    FROM Movs
    WHERE rn = 1
      AND IDRegistro = 1
      AND IDColaborador = LTRIM(RTRIM(?));
    """
    with get_conn() as cn, cn.cursor() as cur:
        cur.execute(sql, (id_resp.strip(),))
        row = cur.fetchone()
        return row[0] if row else None


def validar_regras_de_status(acao: str, id_coletor: str, id_resp: Optional[str]) -> Tuple[bool, str]:
    ac = acao.upper()
    status, last_colab = _status_atual(id_coletor)

    # ENTREGA
    if ac == "ENTREGA" and (id_resp or "").strip():
        atual = _colaborador_tem_coletor_em_operacao(id_resp)
        if atual:
            return False, f"{id_resp} já está com o coletor {atual}. EFETUE A DEVOLUÇÃO para prosseguir."

    # DEVOLUÇÃO
    if ac == "DEVOLUCAO":
        if status == "DISPONIVEL":
            return False, f"{id_coletor} não está em operação para ser devolvido. EFETUE ENTREGA para prosseguir."
        if status in ("EXTRAVIADO", "INATIVO") and id_resp:
            return False, f"Retorno de coletor que estava {status}."
        if status == "EM OPERACAO" and id_resp and last_colab and id_resp.strip() != last_colab.strip():
            return False, f"{last_colab} que estava com esse coletor. Verifique o USUÁRIO CORRETO para prosseguir."

    # ENVIO (conserto)
    if ac == "ENVIO":
        if status == "EM OPERACAO":
            return False, f"{id_coletor} está em operação. EFETUE DEVOLUÇÃO para prosseguir."
        if status == "EM CONSERTO":
            return False, f"{id_coletor} já está em conserto. EFETUE RETORNO para prosseguir."

    # RETORNO (conserto)
    if ac == "RETORNO" and status != "EM CONSERTO":
        return False, f"{id_coletor} não foi enviado para conserto. EFETUE O ENVIO para prosseguir."

    return True, ""

# =========================
# INSERTS
# =========================

def inserir_mov_principal(d: MovDados) -> None:
    sql = """
    INSERT INTO LG_ControleColetores
    (DataRegistro, IDRegistro, IDColetor, IDColaborador,
     RealizadoTeste, DetectadoDefeito, SinalizaConserto,
     Observacao, RespProcesso, DataEnvioConserto, Chamado, DataRetornoConserto)
    VALUES
    (GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        d.id_registro,
        d.id_coletor.strip(),
        (d.id_colaborador or "").strip() or None,
        1 if d.realizado_teste else 0,
        1 if d.detectado_defeito else 0,
        1 if d.sinaliza_conserto else 0,
        (d.observacao or "").strip() or None,
        d.resp_processo.strip(),
        yyyymmdd(d.data_envio_conserto),
        (d.chamado or "").strip() or None,
        yyyymmdd(d.data_retorno_conserto),
    )
    with get_conn() as cn, cn.cursor() as cur:
        cur.execute(sql, params)
        cn.commit()  # <<<<<< AQUI


def inserir_defeitos(defeitos: List[DefeitoItem]) -> None:
    if not defeitos:
        return
    sql = """
    INSERT INTO LG_ControleColetoresDefeito
    (DataRegistro, IDRegistro, IDColetor, IDDefeito, RespProcesso)
    VALUES (GETDATE(), ?, ?, ?, ?)
    """
    with get_conn() as cn, cn.cursor() as cur:
        for it in defeitos:
            cur.execute(sql, (it.id_registro, it.id_coletor.strip(), it.id_defeito.strip(), it.resp_processo.strip()))
        cn.commit()  # <<<<<< AQUI

# =========================
# ORQUESTRAÇÃO
# =========================

def processar_movimentacao(
    acao_ui: str,
    id_coletor: str,
    id_resp: Optional[str],
    realizado_teste: bool,
    detectado_defeito: bool,
    sinaliza_conserto: bool,
    observacao: Optional[str],
    resp_processo: str,
    data_envio_conserto: Optional[str],
    chamado: Optional[str],
    data_retorno_conserto: Optional[str],
    lista_defeitos_escolhidos: Optional[List[str]] = None,
) -> Tuple[bool, str]:

    acao_norm = acao_ui.strip().upper()
    if acao_norm.startswith("ENTREGA"):
        ac = "ENTREGA"
    elif acao_norm.startswith("DEVOLU"):
        ac = "DEVOLUCAO"
    elif acao_norm.startswith("ENVIO"):
        ac = "ENVIO"
    elif acao_norm.startswith("RETORNO"):
        ac = "RETORNO"
    elif "EXTRAVI" in acao_norm:
        ac = "EXTRAVIO"
    elif "INATIV" in acao_norm:
        ac = "INATIVO"
    else:
        return False, f"Ação não reconhecida: {acao_ui}"

    id_reg = ID_REGISTRO[ac]
    id_coletor = (id_coletor or "").strip()
    id_resp = (id_resp or "").strip()

    ok, msg = validar_bipagem(ac, id_coletor, id_resp)
    if not ok:
        return False, msg

    ok, msg = validar_regras_de_status(ac, id_coletor, id_resp)
    if not ok:
        return False, msg

    mov = MovDados(
        id_registro=id_reg,
        id_coletor=id_coletor,
        id_colaborador=id_resp,
        realizado_teste=realizado_teste,
        detectado_defeito=detectado_defeito,
        sinaliza_conserto=sinaliza_conserto,
        observacao=observacao,
        resp_processo=resp_processo,
        data_envio_conserto=data_envio_conserto,
        chamado=chamado,
        data_retorno_conserto=data_retorno_conserto,
    )

    try:
        inserir_mov_principal(mov)

        if detectado_defeito and lista_defeitos_escolhidos:
            itens: List[DefeitoItem] = []
            for s in lista_defeitos_escolhidos:
                id_def = s.split(" - ")[0].strip()
                itens.append(DefeitoItem(
                    id_registro=id_reg,
                    id_coletor=id_coletor,
                    id_defeito=id_def,
                    resp_processo=resp_processo
                ))
            inserir_defeitos(itens)

        return True, "Movimentação registrada com sucesso."
    except pyodbc.Error as e:
        return False, f"Erro de banco: {e}"
    except Exception as e:
        return False, f"Falha ao processar movimentação: {e}"

# =========================
# HELPERS DE UI
# =========================

def nome_coletor_ou_usuario(id_busca: str, modo: str) -> Optional[str]:
    if modo.upper() == "COLETOR":
        sql = """
        SELECT TOP 1 LTRIM(RTRIM(NumSerie))
        FROM COLETORES_CADASTRO WITH (NOLOCK)
        WHERE LTRIM(RTRIM(IDColetores)) = LTRIM(RTRIM(?))
          AND LTRIM(RTRIM(NumSerie)) NOT LIKE '%COLETOR%'
        ORDER BY IDColetores
        """
    else:
        sql = """
        SELECT TOP 1 NOME_COMPLETO
        FROM [DB_VIEWS].[dbo].[SS_USUARIOS_COLETOR] WITH (NOLOCK)
        WHERE INATIVO = 0
          AND LTRIM(RTRIM(ID_USUARIO)) = LTRIM(RTRIM(?))
          --AND NOME_COMPLETO NOT LIKE '%G21%'
        """
    with get_conn() as cn, cn.cursor() as cur:
        cur.execute(sql, (id_busca.strip(),))
        row = cur.fetchone()
        return row[0] if row else None

def status_do_coletor(id_coletor: str) -> Tuple[str, Optional[str]]:
    return _status_atual(id_coletor)
