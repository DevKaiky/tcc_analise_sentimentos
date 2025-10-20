from core.coletar_dados import coletar_dados_reddit
from core.analise_sentimento import analisar_textos_em_lote
from core.database import (
    apagar_base_de_dados_antiga,
    obter_dados_nao_analisados,
    atualizar_dado_analisado,
    exibir_todos_os_dados,
)
from core.db import ensure_table_exists



def executar_pipeline_de_teste(palavra_chave, max_posts):
    print("--- INICIANDO PIPELINE DE TESTE ---")
    
    # 1. Limpa e recria a base de dados
    apagar_base_de_dados_antiga()
    ensure_table_exists()
    print("\n[PASSO 1] Base de dados limpa e pronta.")

    # 2. Coleta de dados
    print(f"\n[PASSO 2] A coletar {max_posts} posts sobre '{palavra_chave}'...")
    coletar_dados_reddit(palavra_chave, max_posts=max_posts)

    # 3. Análise com IA
    print("\n[PASSO 3] A analisar posts com IA...")
    posts_para_analisar = obter_dados_nao_analisados()
    if posts_para_analisar:
        resultados_analise = analisar_textos_em_lote(posts_para_analisar)
        if resultados_analise:
            for post_id, analise in resultados_analise.items():
                atualizar_dado_analisado(
                    post_id,
                    analise['sentimento'],
                    analise['emocao'],
                    analise['topico'],
                    analise['entidades'],
                    analise['aspectos']
                )
            print("Análise concluída com sucesso.")
        else:
            print("Falha na análise dos posts.")
    else:
        print("Nenhum post encontrado para analisar.")

    print("\n[PASSO 4] Resultados guardados na base de dados:")
    exibir_todos_os_dados() 

    print("\n--- PIPELINE DE TESTE CONCLUÍDO ---")


if __name__ == "__main__":
    # Parâmetros para o seu teste
    PALAVRA_CHAVE_TESTE = "Apple"
    MAXIMO_POSTS_TESTE = 5
    
    executar_pipeline_de_teste(PALAVRA_CHAVE_TESTE, MAXIMO_POSTS_TESTE)