import praw
import datetime
import re
from config.settings import RedditConfig
from config.logging_config import obter_logger
from .database import salvar_dado

# Logger do modulo
_log = obter_logger("collector")

# Cliente Reddit sera inicializado sob demanda
_reddit = None

# Configurações de filtragem
TAMANHO_MINIMO_TEXTO = 10  # Caracteres mínimos para considerar o post válido
BOT_KEYWORDS = [
    'AutoModerator',
    'bot',
    '[bot]',
    'moderator',
    'automoderator',
    'ModeratorBot',
    'AutoModBot'
]


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


def _eh_post_de_bot(autor, titulo, texto):
    """
    Verifica se o post foi criado por um bot.

    Args:
        autor: Nome do autor do post.
        titulo: Título do post.
        texto: Conteúdo do post.

    Returns:
        True se for identificado como bot, False caso contrário.
    """
    if not autor:
        return False

    # Verifica o nome do autor
    autor_lower = str(autor).lower()
    for keyword in BOT_KEYWORDS:
        if keyword.lower() in autor_lower:
            return True

    # Verifica título e texto
    texto_completo = f"{titulo} {texto}".lower()
    for keyword in BOT_KEYWORDS:
        if keyword.lower() in texto_completo and len(keyword) > 3:
            return True

    return False


def _tamanho_valido(texto):
    """
    Verifica se o texto tem tamanho mínimo válido.

    Args:
        texto: Texto a ser validado.

    Returns:
        True se o texto tem tamanho válido, False caso contrário.
    """
    if not texto:
        return False

    # Remove espaços em branco extras e verifica tamanho
    texto_limpo = texto.strip()
    return len(texto_limpo) >= TAMANHO_MINIMO_TEXTO


def _eh_texto_valido(texto):
    """
    Verifica se o texto contém conteúdo significativo.
    Remove URLs, menções e caracteres especiais para validação.

    Args:
        texto: Texto a ser validado.

    Returns:
        True se o texto é válido, False caso contrário.
    """
    if not texto:
        return False

    # Remove URLs
    texto_sem_url = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', texto)

    # Remove menções (u/username, r/subreddit)
    texto_sem_mencoes = re.sub(r'[ur]/\w+', '', texto_sem_url)

    # Remove caracteres especiais repetidos (ex: "!!!", "???")
    texto_limpo = re.sub(r'([!?.])\1{2,}', r'\1', texto_sem_mencoes)

    # Verifica se ainda sobra conteúdo significativo
    return _tamanho_valido(texto_limpo)


def coletar_dados_reddit(palavra_chave, max_posts=5, subreddit=None):
    """
    Coleta posts do Reddit baseado em uma palavra-chave.

    Para garantir a qualidade dos dados, são aplicados filtros de pré-processamento:
    - Exclusão de postagens com menos de 10 caracteres (geralmente ruído ou erros de digitação)
    - Remoção automática de postagens geradas por bots moderadores (identificados por
      palavras-chave como 'AutoModerator')
    - Validação de conteúdo significativo (remove posts apenas com URLs ou caracteres especiais)

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

    dados_coletados = []
    posts_filtrados = 0
    posts_processados = 0

    try:
        for post in subreddit_alvo.search(palavra_chave, sort="new", limit=max_posts * 2):
            posts_processados += 1

            # Concatena titulo e texto apenas se selftext existir
            texto_completo = post.title
            if post.selftext and post.selftext.strip():
                texto_completo = f"{post.title}. {post.selftext}"

            # Aplicar filtros de qualidade
            # Filtro 1: Verificar se é post de bot
            if _eh_post_de_bot(post.author, post.title, post.selftext or ''):
                posts_filtrados += 1
                _log.debug(f"Post filtrado (bot): {post.title[:50]}...")
                continue

            # Filtro 2: Verificar tamanho mínimo
            if not _tamanho_valido(texto_completo):
                posts_filtrados += 1
                _log.debug(f"Post filtrado (tamanho): {post.title[:50]}...")
                continue

            # Filtro 3: Verificar se texto é válido (não apenas URLs/caracteres especiais)
            if not _eh_texto_valido(texto_completo):
                posts_filtrados += 1
                _log.debug(f"Post filtrado (conteúdo inválido): {post.title[:50]}...")
                continue

            # Post aprovado nos filtros
            post_data = {
                'texto': texto_completo,
                'data': datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S")
            }

            salvar_dado(post_data)
            dados_coletados.append(post_data)

            # Parar quando atingir o número desejado de posts válidos
            if len(dados_coletados) >= max_posts:
                break

        _log.info(f"Coleta concluída: {len(dados_coletados)} posts coletados, "
                  f"{posts_filtrados} posts filtrados de {posts_processados} processados")
        return dados_coletados

    except Exception as e:
        _log.error(f"Erro na coleta: {e}")
        return dados_coletados
