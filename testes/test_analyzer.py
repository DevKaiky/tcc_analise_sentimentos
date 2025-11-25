# Testes unitarios para o modulo de analise de sentimentos

import pytest
from unittest.mock import patch, MagicMock


class TestNormalizacaoSentimento:
    """Testes para normalizacao de sentimentos."""
    
    def test_sentimentos_validos(self):
        """Verifica se sentimentos validos sao mantidos."""
        from core.analise_sentimento import _normalizar_sentimento
        
        assert _normalizar_sentimento('muito positivo') == 'muito positivo'
        assert _normalizar_sentimento('positivo') == 'positivo'
        assert _normalizar_sentimento('neutro') == 'neutro'
        assert _normalizar_sentimento('negativo') == 'negativo'
        assert _normalizar_sentimento('muito negativo') == 'muito negativo'
    
    def test_sentimentos_com_espacos(self):
        """Verifica se espacos sao removidos."""
        from core.analise_sentimento import _normalizar_sentimento
        
        assert _normalizar_sentimento('  positivo  ') == 'positivo'
        assert _normalizar_sentimento('muito positivo ') == 'muito positivo'
    
    def test_sentimentos_maiusculos(self):
        """Verifica se maiusculas sao convertidas."""
        from core.analise_sentimento import _normalizar_sentimento
        
        assert _normalizar_sentimento('POSITIVO') == 'positivo'
        assert _normalizar_sentimento('Muito Negativo') == 'muito negativo'
    
    def test_sentimentos_aproximados(self):
        """Verifica se variantes sao corrigidas."""
        from core.analise_sentimento import _normalizar_sentimento
        
        assert _normalizar_sentimento('muito positiva') == 'muito positivo'
        assert _normalizar_sentimento('negativa') == 'negativo'
        assert _normalizar_sentimento('neutra') == 'neutro'
    
    def test_sentimento_invalido_retorna_neutro(self):
        """Verifica se valores invalidos retornam neutro."""
        from core.analise_sentimento import _normalizar_sentimento
        
        assert _normalizar_sentimento('invalido') == 'neutro'
        assert _normalizar_sentimento('xyz') == 'neutro'
        assert _normalizar_sentimento('') == 'neutro'


class TestNormalizacaoEmocao:
    """Testes para normalizacao de emocoes."""
    
    def test_emocoes_validas(self):
        """Verifica se emocoes validas sao mantidas."""
        from core.analise_sentimento import _normalizar_emocao
        
        assert _normalizar_emocao('alegria') == 'alegria'
        assert _normalizar_emocao('raiva') == 'raiva'
        assert _normalizar_emocao('tristeza') == 'tristeza'
        assert _normalizar_emocao('surpresa') == 'surpresa'
        assert _normalizar_emocao('neutra') == 'neutra'
    
    def test_emocoes_aproximadas(self):
        """Verifica se variantes sao corrigidas."""
        from core.analise_sentimento import _normalizar_emocao
        
        assert _normalizar_emocao('antecipação') == 'antecipacao'
        assert _normalizar_emocao('neutral') == 'neutra'
        assert _normalizar_emocao('neutro') == 'neutra'
    
    def test_emocao_invalida_retorna_neutra(self):
        """Verifica se valores invalidos retornam neutra."""
        from core.analise_sentimento import _normalizar_emocao
        
        assert _normalizar_emocao('invalido') == 'neutra'
        assert _normalizar_emocao('') == 'neutra'


class TestParseLinhaResposta:
    """Testes para parsing de linhas da resposta da IA."""
    
    def test_parse_formato_correto(self):
        """Verifica parsing de linha no formato correto."""
        from core.analise_sentimento import _parse_linha_resposta
        
        linha = "ID:1; Sentimento:positivo; Emoção:alegria; Tópico:teste; Entidades:nenhuma; Aspectos:nenhum"
        resultado = _parse_linha_resposta(linha)
        
        assert resultado is not None
        assert resultado['id'] == 1
        assert resultado['sentimento'] == 'positivo'
        assert resultado['emocao'] == 'alegria'
        assert resultado['topico'] == 'teste'
    
    def test_parse_linha_vazia(self):
        """Verifica que linha vazia retorna None."""
        from core.analise_sentimento import _parse_linha_resposta
        
        assert _parse_linha_resposta('') is None
        assert _parse_linha_resposta('   ') is None
    
    def test_parse_linha_incompleta(self):
        """Verifica que linha incompleta retorna None."""
        from core.analise_sentimento import _parse_linha_resposta
        
        linha = "ID:1; Sentimento:positivo"
        resultado = _parse_linha_resposta(linha)
        
        assert resultado is None


class TestAnalisarTextosEmLote:
    """Testes para funcao de analise em lote."""
    
    def test_lista_vazia_retorna_dict_vazio(self):
        """Verifica que lista vazia retorna dicionario vazio."""
        from core.analise_sentimento import analisar_textos_em_lote
        
        with patch('core.analise_sentimento._inicializar_modelo') as mock_modelo:
            mock_modelo.return_value = MagicMock()
            
            resultado = analisar_textos_em_lote([])
            
            assert resultado == {}
    
    def test_modelo_nao_inicializado(self):
        """Verifica comportamento quando modelo falha."""
        from core.analise_sentimento import analisar_textos_em_lote
        
        with patch('core.analise_sentimento._inicializar_modelo') as mock_modelo:
            mock_modelo.return_value = None
            
            posts = [{'id': 1, 'texto': 'Teste'}]
            resultado = analisar_textos_em_lote(posts)
            
            assert resultado is None
