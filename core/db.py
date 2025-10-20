import sqlite3


DB_FILE = "sentimentos.db" 

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_table_exists():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
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
            """)
            conn.commit()
            print("Tabela 'sentimentos_analise' verificada/criada com sucesso no SQLite!")
    except sqlite3.Error as err:
        print(f"Erro ao verificar/criar tabela no SQLite: {err}")