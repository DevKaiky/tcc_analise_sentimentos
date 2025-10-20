import sqlite3
from .db import get_db_connection, DB_FILE
import pandas as pd
import os

def salvar_dado_no_banco(dado):
    sql = "INSERT INTO sentimentos_analise (texto, data) VALUES (?, ?)"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (dado['texto'], dado['data']))
            conn.commit()
    except sqlite3.Error as err:
        print(f"Erro ao salvar no SQLite: {err}")

def obter_dados_nao_analisados():
    sql = "SELECT id, texto FROM sentimentos_analise WHERE sentimento IS NULL"
    dados = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            dados = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as err:
        print(f"Erro ao obter dados não analisados do SQLite: {err}")
    return dados

def atualizar_dado_analisado(dado_id, sentimento, emocao, topico, entidades, aspectos):
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
    except sqlite3.Error as err:
        print(f"Erro ao atualizar dado no SQLite: {err}")

def exibir_todos_os_dados():
    print("\n--- Exibindo todos os dados salvos no banco ---")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sentimentos_analise ORDER BY id DESC")
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhum dado encontrado no banco de dados.")
                return

            for dado in resultados:
                print(dict(dado))

    except sqlite3.Error as err:
        print(f"Erro ao consultar dados no SQLite: {err}")
    finally:
        print("--- Fim da exibição ---\n")

def obter_dados_analisados_como_dataframe():
    sql = "SELECT * FROM sentimentos_analise WHERE sentimento IS NOT NULL"
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(sql, conn)
            return df
    except Exception as e:
        print(f"Erro ao obter dados como DataFrame: {e}")
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro
    
def apagar_base_de_dados_antiga():
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"Ficheiro de base de dados antigo '{DB_FILE}' apagado com sucesso.")
    except Exception as e:
        print(f"Erro ao tentar apagar o ficheiro da base de dados: {e}")       