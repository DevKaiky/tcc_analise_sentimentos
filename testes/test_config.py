# Testes unitarios para o modulo de configuracao

import pytest
import os
from unittest.mock import patch


class TestValidacaoConfiguracao:
    """Testes para validacao de configuracoes."""
    
    def test_configuracao_incompleta_reddit(self):
        """Verifica que falta de config do Reddit e detectada."""
        from config import RedditConfig
        
        with patch.dict(os.environ, {}, clear=True):
            assert RedditConfig.validar() is False
    
    def test_configuracao_incompleta_gemini(self):
        """Verifica que falta de config do Gemini e detectada."""
        from config import GeminiConfig
        
        with patch.dict(os.environ, {}, clear=True):
            assert GeminiConfig.validar() is False
    
    def test_configuracao_completa_reddit(self):
        """Verifica validacao com config completa do Reddit."""
        from config import RedditConfig
        
        env_vars = {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret',
            'REDDIT_USER_AGENT': 'test_agent'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            assert RedditConfig.validar() is True
    
    def test_configuracao_completa_gemini(self):
        """Verifica validacao com config completa do Gemini."""
        from config import GeminiConfig
        
        env_vars = {
            'GEMINI_API_KEY': 'test_key'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            assert GeminiConfig.validar() is True


class TestConstantesSentimentosEmocoes:
    """Testes para constantes de sentimentos e emocoes."""
    
    def test_sentimentos_validos_existem(self):
        """Verifica que todos os sentimentos esperados existem."""
        from config import SENTIMENTOS_VALIDOS
        
        esperados = {
            'muito positivo', 'positivo', 'neutro', 
            'negativo', 'muito negativo'
        }
        
        assert SENTIMENTOS_VALIDOS == esperados
    
    def test_emocoes_validas_existem(self):
        """Verifica que todas as emocoes esperadas existem."""
        from config import EMOCOES_VALIDAS
        
        esperados = {
            'alegria', 'raiva', 'tristeza', 
            'surpresa', 'antecipacao', 'neutra'
        }
        
        assert EMOCOES_VALIDAS == esperados
    
    def test_constantes_sao_imutaveis(self):
        """Verifica que constantes sao frozensets."""
        from config import SENTIMENTOS_VALIDOS, EMOCOES_VALIDAS
        
        assert isinstance(SENTIMENTOS_VALIDOS, frozenset)
        assert isinstance(EMOCOES_VALIDAS, frozenset)


class TestValidacaoGlobal:
    """Testes para validacao global de configuracao."""
    
    def test_validacao_completa_falha_sem_variaveis(self):
        """Verifica que validacao completa falha sem variaveis."""
        from config import validar_configuracao_completa
        
        with patch.dict(os.environ, {}, clear=True):
            resultado = validar_configuracao_completa(silencioso=True)
            assert resultado is False
    
    def test_validacao_completa_sucesso(self):
        """Verifica que validacao completa passa com tudo configurado."""
        from config import validar_configuracao_completa
        
        env_vars = {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret',
            'REDDIT_USER_AGENT': 'test_agent',
            'GEMINI_API_KEY': 'test_key'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            resultado = validar_configuracao_completa(silencioso=True)
            assert resultado is True
