import os
import praw
from dotenv import load_dotenv
from .database import salvar_dado_no_banco 
import datetime

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

def coletar_dados_reddit(palavra_chave, max_posts=5):
   
    subreddit_alvo = reddit.subreddit("brasil") # Exemplo: buscando no r/brasil
    print(f"Coletando posts do subreddit 'r/{subreddit_alvo.display_name}' contendo '{palavra_chave}'...")
    
    dados_coletados = []
    
    try:
        # Busca por novos posts no subreddit
        for post in subreddit_alvo.search(palavra_chave, sort="new", limit=max_posts):
            post_data = {
                'texto': f"{post.title}. {post.selftext}",
                'data': datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            salvar_dado_no_banco(post_data) 
            dados_coletados.append(post_data)

        print(f"Coleta de dados do Reddit concluída. Total coletado: {len(dados_coletados)}")
        return dados_coletados

    except Exception as e:
        print(f"[Erro inesperado na coleta de dados do Reddit] {e}")
        return dados_coletados