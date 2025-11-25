# Modulo de configuracao centralizada e validacao de ambiente

import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


# --- Variaveis de Ambiente ---

class ConfiguracaoIncompleta(Exception):
    """Excecao levantada quando variaveis de ambiente obrigatorias estao ausentes."""
    pass


def _obter_variavel_obrigatoria(nome: str) -> str:
    """Obtem uma variavel de ambiente obrigatoria ou levanta excecao."""
    valor = os.getenv(nome)
    if not valor or valor.strip() == "":
        raise ConfiguracaoIncompleta(
            f"Variavel de ambiente obrigatoria '{nome}' nao definida. "
            f"Verifique o arquivo .env"
        )
    return valor.strip()


def _obter_variavel_opcional(nome: str, padrao: str = "") -> str:
    """Obtem uma variavel de ambiente opcional com valor padrao."""
    valor = os.getenv(nome, padrao)
    return valor.strip() if valor else padrao


# --- Configuracoes do Reddit ---

class RedditConfig:
    """Configuracoes para a API do Reddit."""
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    USER_AGENT: str = ""
    SUBREDDIT_PADRAO: str = "brasil"
    
    @classmethod
    def carregar(cls) -> None:
        cls.CLIENT_ID = _obter_variavel_obrigatoria("REDDIT_CLIENT_ID")
        cls.CLIENT_SECRET = _obter_variavel_obrigatoria("REDDIT_CLIENT_SECRET")
        cls.USER_AGENT = _obter_variavel_obrigatoria("REDDIT_USER_AGENT")
        cls.SUBREDDIT_PADRAO = _obter_variavel_opcional("REDDIT_SUBREDDIT", "brasil")
    
    @classmethod
    def validar(cls) -> bool:
        try:
            cls.carregar()
            return True
        except ConfiguracaoIncompleta:
            return False


# --- Configuracoes do Gemini ---

class GeminiConfig:
    """Configuracoes para a API do Google Gemini."""
    API_KEY = genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    MODELO = genai.GenerativeModel("models/gemini-flash-latest")
    TENTATIVAS_MAX: int = 5
    DELAY_ENTRE_TENTATIVAS: int = 5
    
    @classmethod
    def carregar(cls) -> None:
        cls.API_KEY = _obter_variavel_obrigatoria("GEMINI_API_KEY")
        cls.MODELO = _obter_variavel_opcional("GEMINI_MODELO", "models/gemini-flash-latest")
        
        tentativas = _obter_variavel_opcional("GEMINI_TENTATIVAS_MAX", "5")
        cls.TENTATIVAS_MAX = int(tentativas) if tentativas.isdigit() else 5
    
    @classmethod
    def validar(cls) -> bool:
        try:
            cls.carregar()
            return True
        except ConfiguracaoIncompleta:
            return False


# --- Configuracoes do Banco de Dados ---

class DatabaseConfig:
    """Configuracoes do banco de dados SQLite."""
    ARQUIVO: str = "sentimentos.db"
    
    @classmethod
    def carregar(cls) -> None:
        cls.ARQUIVO = _obter_variavel_opcional("DATABASE_FILE", "sentimentos.db")


# --- Valores Validos para Analise ---

SENTIMENTOS_VALIDOS = frozenset({
    'muito positivo',
    'positivo',
    'neutro',
    'negativo',
    'muito negativo'
})

EMOCOES_VALIDAS = frozenset({
    'alegria',
    'raiva',
    'tristeza',
    'surpresa',
    'antecipacao',
    'neutra'
})


# --- Funcao de Validacao Global ---

def validar_configuracao_completa(silencioso: bool = False) -> bool:
    """
    Valida todas as configuracoes necessarias para o funcionamento do sistema.
    
    Args:
        silencioso: Se True, nao imprime mensagens de erro.
    
    Returns:
        True se todas as configuracoes estao validas, False caso contrario.
    """
    erros = []
    
    # Validar Reddit
    try:
        RedditConfig.carregar()
    except ConfiguracaoIncompleta as e:
        erros.append(str(e))
    
    # Validar Gemini
    try:
        GeminiConfig.carregar()
    except ConfiguracaoIncompleta as e:
        erros.append(str(e))
    
    # Carregar Database (nao tem variaveis obrigatorias)
    DatabaseConfig.carregar()
    
    if erros:
        if not silencioso:
            print("=" * 60)
            print("ERRO DE CONFIGURACAO")
            print("=" * 60)
            for erro in erros:
                print(f"  - {erro}")
            print("=" * 60)
            print("Crie um arquivo .env na raiz do projeto com as variaveis:")
            print("  REDDIT_CLIENT_ID=seu_client_id")
            print("  REDDIT_CLIENT_SECRET=seu_client_secret")
            print("  REDDIT_USER_AGENT=seu_user_agent")
            print("  GEMINI_API_KEY=sua_api_key")
            print("=" * 60)
        return False
    
    return True


def inicializar_configuracao() -> None:
    """
    Inicializa e valida todas as configuracoes.
    Encerra o programa se houver erros criticos.
    """
    if not validar_configuracao_completa():
        sys.exit(1)
    
    # Carregar todas as configuracoes
    RedditConfig.carregar()
    GeminiConfig.carregar()
    DatabaseConfig.carregar()
