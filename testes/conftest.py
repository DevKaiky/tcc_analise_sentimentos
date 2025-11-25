# Configuracao global de testes pytest

import pytest
import sys
import os

# Adiciona diretorio raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def configurar_ambiente_testes():
    """Configura ambiente para testes."""
    # Define variaveis de ambiente minimas para evitar erros de importacao
    os.environ.setdefault('REDDIT_CLIENT_ID', 'test')
    os.environ.setdefault('REDDIT_CLIENT_SECRET', 'test')
    os.environ.setdefault('REDDIT_USER_AGENT', 'test')
    os.environ.setdefault('GEMINI_API_KEY', 'test')
    os.environ.setdefault('DATABASE_FILE', ':memory:')
    
    yield
    
    # Cleanup apos testes
    pass


@pytest.fixture
def sample_posts():
    """Fixture com posts de exemplo para testes."""
    return [
        {'id': 1, 'texto': 'Este produto e excelente, recomendo muito!'},
        {'id': 2, 'texto': 'Pessimo atendimento, nunca mais volto.'},
        {'id': 3, 'texto': 'O servico e ok, nada de especial.'},
    ]


@pytest.fixture
def sample_analise():
    """Fixture com resultado de analise de exemplo."""
    return {
        1: {
            'sentimento': 'muito positivo',
            'emocao': 'alegria',
            'topico': 'produto',
            'entidades': 'nenhuma',
            'aspectos': 'qualidade: positivo'
        },
        2: {
            'sentimento': 'muito negativo',
            'emocao': 'raiva',
            'topico': 'atendimento',
            'entidades': 'nenhuma',
            'aspectos': 'atendimento: negativo'
        },
        3: {
            'sentimento': 'neutro',
            'emocao': 'neutra',
            'topico': 'servico',
            'entidades': 'nenhuma',
            'aspectos': 'nenhum'
        }
    }
