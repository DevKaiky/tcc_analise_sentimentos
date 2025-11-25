# Modulo unificado de banco de dados
# Gerencia conexoes, estrutura e operacoes CRUD

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional
import pandas as pd

from config.settings import DatabaseConfig
from config.logging_config import obter_logger

# Logger do modulo
_log = obter_logger("database")

# --- Configuracao ---

DatabaseConfig.carregar()
DB_FILE = DatabaseConfig.ARQUIVO


# --- Gerenciamento de Conexao ---

@contextmanager
def get_db_connection():
    """
    Context manager para conexao com o banco de dados.
    Garante fechamento adequado da conexao.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()


# --- Estrutura do Banco ---

def ensure_table_exists() -> bool:
    """
    Verifica e cria a tabela principal se nao existir.
    
    Returns:
        True se a operacao foi bem sucedida, False caso contrario.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS sentimentos_analise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data TEXT NOT NULL,
            sentimento TEXT,
            emocao TEXT,
            topico TEXT,
            entidades TEXT,
            aspectos TEXT
        );
    """
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Criar indice para melhorar performance de filtros
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sentimento 
                ON sentimentos_analise(sentimento);
            """)
            
            conn.commit()
            _log.info("Tabela 'sentimentos_analise' verificada/criada com sucesso")
            return True
    except sqlite3.Error as err:
        _log.error(f"Erro ao verificar/criar tabela: {err}")
        return False


def apagar_base_de_dados() -> bool:
    """
    Remove o arquivo do banco de dados.
    
    Returns:
        True se removido com sucesso ou se nao existia, False em caso de erro.
    """
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            _log.info(f"Base de dados '{DB_FILE}' removida")
        return True
    except Exception as e:
        _log.error(f"Erro ao remover base de dados: {e}")
        return False


# --- Operacoes de Escrita ---

def salvar_dado(dado: dict) -> Optional[int]:
    """
    Salva um novo registro no banco de dados.
    
    Args:
        dado: Dicionario com 'texto' e 'data'.
    
    Returns:
        ID do registro inserido ou None em caso de erro.
    """
    sql = "INSERT INTO sentimentos_analise (texto, data) VALUES (?, ?)"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (dado['texto'], dado['data']))
            conn.commit()
            _log.debug(f"Registro salvo com ID {cursor.lastrowid}")
            return cursor.lastrowid
    except sqlite3.Error as err:
        _log.error(f"Erro ao salvar registro: {err}")
        return None


def atualizar_analise(dado_id: int, sentimento: str, emocao: str, 
                      topico: str, entidades: str, aspectos: str) -> bool:
    """
    Atualiza os campos de analise de um registro existente.
    
    Args:
        dado_id: ID do registro a atualizar.
        sentimento: Resultado da analise de sentimento.
        emocao: Resultado da analise de emocao.
        topico: Topico identificado.
        entidades: Entidades extraidas.
        aspectos: Aspectos identificados.
    
    Returns:
        True se atualizado com sucesso, False caso contrario.
    """
    sql = """
        UPDATE sentimentos_analise 
        SET sentimento = ?, emocao = ?, topico = ?, entidades = ?, aspectos = ?
        WHERE id = ?
    """
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (sentimento, emocao, topico, entidades, aspectos, dado_id))
            conn.commit()
            _log.debug(f"Registro {dado_id} atualizado com sentimento '{sentimento}'")
            return cursor.rowcount > 0
    except sqlite3.Error as err:
        _log.error(f"Erro ao atualizar registro {dado_id}: {err}")
        return False


# --- Operacoes de Leitura ---

def obter_nao_analisados() -> list[dict]:
    """
    Obtem todos os registros que ainda nao foram analisados.
    
    Returns:
        Lista de dicionarios com 'id' e 'texto'.
    """
    sql = "SELECT id, texto FROM sentimentos_analise WHERE sentimento IS NULL"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            dados = [dict(row) for row in cursor.fetchall()]
            _log.debug(f"Obtidos {len(dados)} registros não analisados")
            return dados
    except sqlite3.Error as err:
        _log.error(f"Erro ao obter registros não analisados: {err}")
        return []


def obter_todos() -> list[dict]:
    """
    Obtem todos os registros do banco de dados.
    
    Returns:
        Lista de dicionarios com todos os campos.
    """
    sql = "SELECT * FROM sentimentos_analise ORDER BY id DESC"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as err:
        _log.error(f"Erro ao obter registros: {err}")
        return []


def obter_analisados_como_dataframe() -> pd.DataFrame:
    """
    Obtem todos os registros analisados como DataFrame do pandas.
    
    Returns:
        DataFrame com os registros ou DataFrame vazio em caso de erro.
    """
    sql = "SELECT * FROM sentimentos_analise WHERE sentimento IS NOT NULL"
    
    try:
        with get_db_connection() as conn:
            return pd.read_sql_query(sql, conn)
    except Exception as e:
        _log.error(f"Erro ao obter DataFrame: {e}")
        return pd.DataFrame()


def contar_registros(apenas_analisados: bool = False) -> int:
    """
    Conta o numero de registros no banco.
    
    Args:
        apenas_analisados: Se True, conta apenas registros com analise completa.
    
    Returns:
        Numero de registros.
    """
    if apenas_analisados:
        sql = "SELECT COUNT(*) FROM sentimentos_analise WHERE sentimento IS NOT NULL"
    else:
        sql = "SELECT COUNT(*) FROM sentimentos_analise"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchone()[0]
    except sqlite3.Error as err:
        _log.error(f"Erro ao contar registros: {err}")
        return 0


# --- Funcoes de Utilidade ---

def exibir_todos():
    """Exibe todos os registros no terminal (para debug)."""
    _log.info("--- Dados salvos no banco ---")
    
    registros = obter_todos()
    if not registros:
        _log.info("Nenhum registro encontrado")
    else:
        for registro in registros:
            print(registro)
    
    _log.info("--- Fim ---")


# --- Aliases para compatibilidade ---

salvar_dado_no_banco = salvar_dado
obter_dados_nao_analisados = obter_nao_analisados
atualizar_dado_analisado = atualizar_analise
exibir_todos_os_dados = exibir_todos
obter_dados_analisados_como_dataframe = obter_analisados_como_dataframe
apagar_base_de_dados_antiga = apagar_base_de_dados
