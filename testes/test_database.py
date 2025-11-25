# Testes unitarios para o modulo de banco de dados

import pytest
import os
import tempfile
from unittest.mock import patch

# Configura banco de dados temporario para testes
@pytest.fixture(autouse=True)
def banco_temporario():
    """Fixture que cria um banco de dados temporario para cada teste."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    # Patch da configuracao do banco
    with patch('config.DatabaseConfig.ARQUIVO', temp_db):
        with patch('core.database.DB_FILE', temp_db):
            yield temp_db
    
    # Limpa arquivo temporario
    if os.path.exists(temp_db):
        os.remove(temp_db)


class TestEstruturaTabela:
    """Testes para criacao e estrutura da tabela."""
    
    def test_criar_tabela(self, banco_temporario):
        """Verifica se a tabela e criada corretamente."""
        from core.database import ensure_table_exists, get_db_connection
        
        resultado = ensure_table_exists()
        assert resultado is True
        
        # Verifica se tabela existe
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sentimentos_analise'"
            )
            assert cursor.fetchone() is not None
    
    def test_criar_tabela_multiplas_vezes(self, banco_temporario):
        """Verifica se criar tabela multiplas vezes nao causa erro."""
        from core.database import ensure_table_exists
        
        # Primeira chamada
        resultado1 = ensure_table_exists()
        # Segunda chamada
        resultado2 = ensure_table_exists()
        
        assert resultado1 is True
        assert resultado2 is True


class TestOperacoesEscrita:
    """Testes para operacoes de escrita no banco."""
    
    def test_salvar_dado(self, banco_temporario):
        """Verifica se um dado e salvo corretamente."""
        from core.database import ensure_table_exists, salvar_dado, obter_todos
        
        ensure_table_exists()
        
        dado = {
            'texto': 'Texto de teste para analise',
            'data': '2024-01-15 10:30:00'
        }
        
        resultado_id = salvar_dado(dado)
        
        assert resultado_id is not None
        assert resultado_id > 0
        
        # Verifica se foi salvo
        todos = obter_todos()
        assert len(todos) == 1
        assert todos[0]['texto'] == dado['texto']
    
    def test_atualizar_analise(self, banco_temporario):
        """Verifica se a analise e atualizada corretamente."""
        from core.database import (
            ensure_table_exists, salvar_dado, 
            atualizar_analise, obter_todos
        )
        
        ensure_table_exists()
        
        # Salva dado inicial
        dado = {'texto': 'Texto para analise', 'data': '2024-01-15 10:30:00'}
        dado_id = salvar_dado(dado)
        
        # Atualiza com analise
        resultado = atualizar_analise(
            dado_id,
            sentimento='positivo',
            emocao='alegria',
            topico='teste',
            entidades='nenhuma',
            aspectos='nenhum'
        )
        
        assert resultado is True
        
        # Verifica atualizacao
        todos = obter_todos()
        assert todos[0]['sentimento'] == 'positivo'
        assert todos[0]['emocao'] == 'alegria'


class TestOperacoesLeitura:
    """Testes para operacoes de leitura no banco."""
    
    def test_obter_nao_analisados(self, banco_temporario):
        """Verifica se retorna apenas registros sem analise."""
        from core.database import (
            ensure_table_exists, salvar_dado, 
            atualizar_analise, obter_nao_analisados
        )
        
        ensure_table_exists()
        
        # Salva dois registros
        id1 = salvar_dado({'texto': 'Texto 1', 'data': '2024-01-15'})
        id2 = salvar_dado({'texto': 'Texto 2', 'data': '2024-01-16'})
        
        # Analisa apenas o primeiro
        atualizar_analise(id1, 'neutro', 'neutra', 'teste', 'nenhuma', 'nenhum')
        
        # Deve retornar apenas o segundo
        nao_analisados = obter_nao_analisados()
        
        assert len(nao_analisados) == 1
        assert nao_analisados[0]['id'] == id2
    
    def test_contar_registros(self, banco_temporario):
        """Verifica contagem de registros."""
        from core.database import (
            ensure_table_exists, salvar_dado,
            atualizar_analise, contar_registros
        )
        
        ensure_table_exists()
        
        # Salva registros
        id1 = salvar_dado({'texto': 'Texto 1', 'data': '2024-01-15'})
        salvar_dado({'texto': 'Texto 2', 'data': '2024-01-16'})
        
        # Analisa um
        atualizar_analise(id1, 'neutro', 'neutra', 'teste', 'nenhuma', 'nenhum')
        
        assert contar_registros() == 2
        assert contar_registros(apenas_analisados=True) == 1


class TestRemocaoBaseDados:
    """Testes para remocao do banco de dados."""
    
    def test_apagar_base_de_dados(self, banco_temporario):
        """Verifica se a base de dados e removida."""
        from core.database import ensure_table_exists, apagar_base_de_dados
        
        ensure_table_exists()
        
        # Arquivo deve existir
        assert os.path.exists(banco_temporario)
        
        # Remove
        with patch('core.database.DB_FILE', banco_temporario):
            resultado = apagar_base_de_dados()
        
        assert resultado is True
