# Modulo de logging estruturado

import logging
import sys
from datetime import datetime
from pathlib import Path


# --- Configuracao do Logger ---

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"


def configurar_logging(
    nivel: int = logging.INFO,
    arquivo: bool = True,
    console: bool = True
) -> logging.Logger:
    """
    Configura o sistema de logging da aplicacao.
    
    Args:
        nivel: Nivel minimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        arquivo: Se True, salva logs em arquivo.
        console: Se True, exibe logs no console.
    
    Returns:
        Logger raiz configurado.
    """
    # Criar diretorio de logs se necessario
    if arquivo:
        LOG_DIR.mkdir(exist_ok=True)
    
    # Configurar logger raiz
    logger = logging.getLogger("analise_sentimentos")
    logger.setLevel(nivel)
    
    # Limpar handlers existentes
    logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Handler de console
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(nivel)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler de arquivo
    if arquivo:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(nivel)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def obter_logger(nome: str) -> logging.Logger:
    """
    Obtem um logger filho do logger principal.
    
    Args:
        nome: Nome do modulo ou componente.
    
    Returns:
        Logger configurado.
    """
    return logging.getLogger(f"analise_sentimentos.{nome}")


# --- Logger padrao ---

# Configura logging na importacao do modulo
_logger_configurado = False

def _garantir_configuracao():
    global _logger_configurado
    if not _logger_configurado:
        configurar_logging()
        _logger_configurado = True


# --- Funcoes de conveniencia ---

def log_info(mensagem: str, modulo: str = "app"):
    """Log de nivel INFO."""
    _garantir_configuracao()
    obter_logger(modulo).info(mensagem)


def log_warning(mensagem: str, modulo: str = "app"):
    """Log de nivel WARNING."""
    _garantir_configuracao()
    obter_logger(modulo).warning(mensagem)


def log_error(mensagem: str, modulo: str = "app"):
    """Log de nivel ERROR."""
    _garantir_configuracao()
    obter_logger(modulo).error(mensagem)


def log_debug(mensagem: str, modulo: str = "app"):
    """Log de nivel DEBUG."""
    _garantir_configuracao()
    obter_logger(modulo).debug(mensagem)


def log_exception(mensagem: str, modulo: str = "app"):
    """Log de excecao com traceback."""
    _garantir_configuracao()
    obter_logger(modulo).exception(mensagem)
