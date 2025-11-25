import praw
import datetime
from config.settings import RedditConfig
from config.logging_config import obter_logger
from .database import salvar_dado

# Logger do modulo
_log = obter_logger("collector")

# Cliente Reddit sera inicializado sob demanda
_reddit = None


def _inicializar_reddit():
    """Inicializa o cliente Reddit sob demanda."""
    global _reddit
    if _reddit is not None:
        return _reddit
    
    try:
        RedditConfig.carregar()
        _reddit = praw.Reddit(
            client_id=RedditConfig.CLIENT_ID,
            client_secret=RedditConfig.CLIENT_SECRET,
            user_agent=RedditConfig.USER_AGENT,
        )
        _log.info("Cliente Reddit inicializado")
        return _reddit
    except Exception as e:
        _log.error(f"Erro ao inicializar cliente Reddit: {e}")
        return None


def coletar_dados_reddit(palavra_chave, max_posts=5, subreddit=None):
    """
    Coleta posts do Reddit baseado em uma palavra-chave.
    
    Args:
        palavra_chave: Termo de busca.
        max_posts: Numero maximo de posts a coletar.
        subreddit: Nome do subreddit (usa padrao da configuracao se nao informado).
    
    Returns:
        Lista de dicionarios com os dados coletados.
    """
    reddit = _inicializar_reddit()
    if not reddit:
        _log.error("Cliente Reddit não inicializado")
        return []
    
    nome_subreddit = subreddit or RedditConfig.SUBREDDIT_PADRAO
    subreddit_alvo = reddit.subreddit(nome_subreddit)
    _log.info(f"Coletando posts de r/{nome_subreddit} com termo '{palavra_chave}'")
    _log.info(f"Coletando posts de r/{nome_subreddit} com termo '{palavra_chave}'")
    
    dados_coletados = []
    
    try:
        for post in subreddit_alvo.search(palavra_chave, sort="new", limit=max_posts):
            # Concatena titulo e texto apenas se selftext existir
            texto_completo = post.title
            if post.selftext and post.selftext.strip():
                texto_completo = f"{post.title}. {post.selftext}"
            
            post_data = {
                'texto': texto_completo,
                'data': datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            salvar_dado(post_data) 
            dados_coletados.append(post_data)

        _log.info(f"Coleta concluída: {len(dados_coletados)} posts")
        return dados_coletados

    except Exception as e:
        _log.error(f"Erro na coleta: {e}")
        return dados_coletados
