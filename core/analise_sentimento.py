import re
import time
import google.generativeai as genai
from config.settings import GeminiConfig, SENTIMENTOS_VALIDOS, EMOCOES_VALIDAS
from config.logging_config import obter_logger

# Logger do modulo
_log = obter_logger("analyzer")

# Modelo sera inicializado sob demanda
_model = None

# Regex para parsing robusto da resposta
_REGEX_LINHA = re.compile(
    r'ID[:\s]*(\d+)[;\s]*'
    r'Sentimento[:\s]*([^;]+)[;\s]*'
    r'Emo[çc][aã]o[:\s]*([^;]+)[;\s]*'
    r'T[oó]pico[:\s]*([^;]+)[;\s]*'
    r'Entidades[:\s]*([^;]+)[;\s]*'
    r'Aspectos[:\s]*(.*)',
    re.IGNORECASE
)


def _inicializar_modelo():
    """Inicializa o modelo Gemini sob demanda."""
    global _model
    if _model is not None:
        return _model
    
    try:
        GeminiConfig.carregar()
        genai.configure(api_key=GeminiConfig.API_KEY)
        _model = genai.GenerativeModel(GeminiConfig.MODELO)
        _log.info(f"API do Gemini configurada com modelo '{GeminiConfig.MODELO}'")
        return _model
    except Exception as e:
        _log.error(f"Erro ao configurar API do Gemini: {e}")
        return None


def _normalizar_sentimento(valor: str) -> str:
    """Normaliza e valida o valor de sentimento."""
    if not valor:
        return 'neutro'
    
    valor_normalizado = valor.strip().lower()
    if valor_normalizado in SENTIMENTOS_VALIDOS:
        return valor_normalizado
    
    # Tentativa de correcao para valores aproximados
    mapeamento_aproximado = {
        'muito positiva': 'muito positivo',
        'muito negativa': 'muito negativo',
        'positiva': 'positivo',
        'negativa': 'negativo',
        'neutra': 'neutro',
        'neutral': 'neutro',
    }
    
    for chave, valor_correto in mapeamento_aproximado.items():
        if chave in valor_normalizado:
            return valor_correto
    
    return 'neutro'


def _normalizar_emocao(valor: str) -> str:
    """Normaliza e valida o valor de emocao."""
    if not valor:
        return 'neutra'
    
    valor_normalizado = valor.strip().lower()
    if valor_normalizado in EMOCOES_VALIDAS:
        return valor_normalizado
    
    # Mapeamento para variantes comuns
    mapeamento_aproximado = {
        'antecipação': 'antecipacao',
        'anticipation': 'antecipacao',
        'neutral': 'neutra',
        'neutro': 'neutra',
        'joy': 'alegria',
        'anger': 'raiva',
        'sadness': 'tristeza',
        'surprise': 'surpresa',
    }
    
    for chave, valor_correto in mapeamento_aproximado.items():
        if chave in valor_normalizado:
            return valor_correto
    
    return 'neutra'


def _parse_linha_resposta(linha: str) -> dict | None:
    """
    Faz o parsing de uma linha da resposta da IA usando regex.
    
    Args:
        linha: Linha de texto da resposta.
    
    Returns:
        Dicionario com os dados extraidos ou None se falhar.
    """
    # Tenta com regex primeiro
    match = _REGEX_LINHA.match(linha.strip())
    if match:
        return {
            'id': int(match.group(1)),
            'sentimento': _normalizar_sentimento(match.group(2)),
            'emocao': _normalizar_emocao(match.group(3)),
            'topico': match.group(4).strip(),
            'entidades': match.group(5).strip(),
            'aspectos': match.group(6).strip()
        }
    
    # Fallback: parsing por split
    try:
        parts = linha.split(';')
        if len(parts) < 6:
            return None
        
        # Extrai ID
        id_part = parts[0]
        id_match = re.search(r'(\d+)', id_part)
        if not id_match:
            return None
        
        post_id = int(id_match.group(1))
        
        return {
            'id': post_id,
            'sentimento': _normalizar_sentimento(parts[1].split(':', 1)[-1] if ':' in parts[1] else parts[1]),
            'emocao': _normalizar_emocao(parts[2].split(':', 1)[-1] if ':' in parts[2] else parts[2]),
            'topico': (parts[3].split(':', 1)[-1] if ':' in parts[3] else parts[3]).strip(),
            'entidades': (parts[4].split(':', 1)[-1] if ':' in parts[4] else parts[4]).strip(),
            'aspectos': (parts[5].split(':', 1)[-1] if ':' in parts[5] else parts[5]).strip()
        }
    except (IndexError, ValueError):
        return None


def analisar_textos_em_lote(posts_para_analisar, tentativas_max=None):
    """
    Analisa uma lista de posts usando a API do Gemini.
    
    Args:
        posts_para_analisar: Lista de dicionarios com 'id' e 'texto'.
        tentativas_max: Numero maximo de tentativas em caso de erro.
    
    Returns:
        Dicionario com resultados da analise ou None em caso de falha.
    """
    model = _inicializar_modelo()
    if not model:
        _log.error("Modelo Gemini não inicializado")
        return None
    
    if not posts_para_analisar:
        _log.warning("Nenhum post para analisar")
        return {}
    
    if tentativas_max is None:
        tentativas_max = GeminiConfig.TENTATIVAS_MAX
    
    _log.info(f"Iniciando análise de {len(posts_para_analisar)} posts")

    prompt_header = (
        "Faça uma análise completa para cada um dos textos a seguir, numerados por ID. Siga estritamente as instruções:\n"
        "1.  **Sentimento**: Classifique numa escala de 5 pontos: 'muito positivo', 'positivo', 'neutro', 'negativo', 'muito negativo'.\n"
        "2.  **Emoção**: Classifique como 'alegria', 'raiva', 'tristeza', 'surpresa', 'antecipação' ou 'neutra'.\n"
        "3.  **Tópico**: Gere uma etiqueta de tópico curta e concisa (2-3 palavras) que resuma o assunto principal. Não use a palavra 'Outro'.\n"
        "4.  **Entidades**: Extraia entidades nomeadas. Se não houver, retorne 'nenhuma'.\n"
        "5.  **Aspectos**: Extraia aspectos e seus sentimentos associados. Se não houver, retorne 'nenhum'.\n\n"
        "Responda para cada texto no seguinte formato, um por linha:\n"
        "ID:<id_do_post>; Sentimento:<resultado>; Emoção:<resultado>; Tópico:<resultado>; Entidades:<resultado>; Aspectos:<resultado>\n\n"
        "--- INÍCIO DOS TEXTOS ---\n"
    )
    
    prompt_body = "\n".join([f"ID:{post['id']}; Texto:\"{post['texto']}\"" for post in posts_para_analisar])
    prompt_completo = prompt_header + prompt_body
    
    ids_esperados = {post['id'] for post in posts_para_analisar}

    for tentativa in range(tentativas_max):
        try:
            response = model.generate_content(prompt_completo)
            
            resultados = {}
            linhas_processadas = 0
            
            for linha in response.text.strip().split('\n'):
                if not linha.strip():
                    continue
                
                dados = _parse_linha_resposta(linha)
                if dados and dados['id'] in ids_esperados:
                    post_id = dados.pop('id')
                    resultados[post_id] = dados
                    linhas_processadas += 1
            
            # Verifica se conseguiu processar pelo menos alguns posts
            if resultados:
                taxa_sucesso = len(resultados) / len(posts_para_analisar) * 100
                _log.info(f"Parsing: {len(resultados)}/{len(posts_para_analisar)} posts ({taxa_sucesso:.1f}%)")
                
                # Preenche posts que falharam com valores padrao
                for post in posts_para_analisar:
                    if post['id'] not in resultados:
                        _log.warning(f"Post ID {post['id']} sem análise, usando padrões")
                        resultados[post['id']] = {
                            'sentimento': 'neutro',
                            'emocao': 'neutra',
                            'topico': 'indefinido',
                            'entidades': 'nenhuma',
                            'aspectos': 'nenhum'
                        }
                
                return resultados
            
            _log.warning(f"Tentativa {tentativa + 1}: nenhum resultado parseado")
            
        except Exception as e:
            _log.error(f"Tentativa {tentativa + 1} falhou: {e}")
        
        time.sleep(GeminiConfig.DELAY_ENTRE_TENTATIVAS * (tentativa + 1))

    _log.error("Falha total na análise em lote")
    return None
