import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import time

from core.db import ensure_table_exists
from core.database import apagar_base_de_dados_antiga, obter_dados_nao_analisados, atualizar_dado_analisado, obter_dados_analisados_como_dataframe
from core.coletar_dados import coletar_dados_reddit
from core.analise_sentimento import analisar_textos_em_lote

# --- Configuração da Página ---
st.set_page_config(page_title="Análise de Sentimentos", layout="wide", initial_sidebar_state="expanded")

def executar_pipeline_completo(palavra_chave, max_posts):
    apagar_base_de_dados_antiga()
    ensure_table_exists()
    st.toast("Base de dados recriada para a nova análise!")

    with st.spinner(f"Coletando {max_posts} posts sobre '{palavra_chave}'..."):
        coletar_dados_reddit(palavra_chave, max_posts=max_posts)
    st.toast("Coleta de dados concluída!", icon="✅")

    posts_para_analisar = obter_dados_nao_analisados()
    if not posts_para_analisar:
        st.warning("Nenhum post encontrado para a palavra-chave. Tente outro termo.")
        return False

    with st.spinner("Analisando todos os posts com IA"):
        resultados_analise = analisar_textos_em_lote(posts_para_analisar)
    
    if resultados_analise:
        for post_id, analise in resultados_analise.items():
            atualizar_dado_analisado(post_id, analise['sentimento'], analise['emocao'], analise['topico'], analise['entidades'], analise['aspectos'])
        st.toast("Análise com IA concluída!", icon="✅")
        return True
    else:
        st.error("Falha ao analisar os posts. Verifique o terminal para mais detalhes.")
        return False

# --- Barra Lateral ---
with st.sidebar:
    st.title("Painel de Controle")
    palavra_chave_input = st.text_input("Digite a palavra-chave:", value="Nubank")
    st.info(
        """
        **Dicas de Busca Avançada:**
        * Use `palavra1 palavra2` para buscar por ambas as palavras.
        * Use `palavra1 OR palavra2` para buscar por uma ou outra.
        * Use `-palavra` para excluir uma palavra da busca.
        """
    ) 
    max_posts_slider = st.slider("Número máximo de posts:", min_value=5, max_value=50, value=10)
    
    if st.button("Executar Análise", type="primary", use_container_width=True):
        st.session_state.analise_executada = True
        st.session_state.palavra_chave = palavra_chave_input
        st.session_state.sucesso_analise = executar_pipeline_completo(palavra_chave_input, max_posts_slider)
    
    st.markdown("---")
    st.markdown("Desenvolvido para o TCC de Análise de Sentimentos.")

# --- Área Principal do Dashboard ---
st.title("Dashboard Interativo de Análise de Sentimentos")

if 'analise_executada' in st.session_state and st.session_state.sucesso_analise:
    st.header(f"Resultados da Análise para: '{st.session_state.palavra_chave}'", divider='rainbow')

    df = obter_dados_analisados_como_dataframe()

    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Posts Analisados", len(df))
        try:
            col2.metric("Sentimento Predominante", df['sentimento'].mode()[0].capitalize())
            col3.metric("Tópico Principal", df['topico'].mode()[0].capitalize())
        except IndexError:
            col2.metric("Sentimento Predominante", "N/A")
            col3.metric("Tópico Principal", "N/A")

        st.markdown("---")

        tab_graficos, tab_dados, tab_insights = st.tabs(["📊 Resumo Gráfico", "📄 Dados Detalhados", "💡 Insights Adicionais"])

        with tab_graficos:
            for col in ['sentimento', 'emocao', 'topico']:
                if col in df.columns:
                    df[col] = df[col].str.strip().str.lower()

            cores_sentimento = {
                'muito positivo': '#1A5D1A', 
                'positivo': '#4CAF50', 
                'neutro': '#BDBDBD', 
                'negativo': '#F44336',
                'muito negativo': '#A60000'
            }

            c1, c2 = st.columns(2)
            with c1:
                fig_sentimento = px.pie(df, names='sentimento', title='Distribuição de Sentimentos (5 Níveis)', hole=.4, color='sentimento', color_discrete_map=cores_sentimento)
                st.plotly_chart(fig_sentimento, use_container_width=True)
                
                contagem_topicos = df['topico'].value_counts().reset_index().head(10) # Mostra os 10 tópicos mais comuns
                fig_topicos = px.bar(contagem_topicos, x='topico', y='count', title='Tópicos Mais Comentados (Gerados por IA)', color='topico')
                st.plotly_chart(fig_topicos, use_container_width=True)
            with c2:
                contagem_emocoes = df['emocao'].value_counts().reset_index()
                fig_emocao = px.bar(contagem_emocoes, x='emocao', y='count', title='Distribuição de Emoções', color='emocao')
                st.plotly_chart(fig_emocao, use_container_width=True)

        with tab_dados:
            st.header("Explore os Dados Analisados")
            sentimento_filtro = st.selectbox("Filtrar por Sentimento:", options=['Todos'] + sorted(df['sentimento'].unique().tolist()))
            df_filtrado = df if sentimento_filtro == 'Todos' else df[df['sentimento'] == sentimento_filtro]
            st.dataframe(df_filtrado)

        with tab_insights:
            st.header("Insights Adicionais")
            col_insights1, col_insights2 = st.columns(2)
            with col_insights1:
                st.subheader("Nuvem de Entidades")
                entidades_flat = [ent.strip().lower() for sublist in df['entidades'].str.split(',') for ent in sublist if ent.strip().lower() not in ['nenhuma', '']]
                if entidades_flat:
                    texto_nuvem = " ".join(entidades_flat)
                    wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(texto_nuvem)
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)
                else:
                    st.write("Nenhuma entidade significativa encontrada.")
            with col_insights2:
                st.subheader("Exemplos de Posts")
                df_positivos = df[df['sentimento'] == 'muito positivo']
                if not df_positivos.empty:
                    st.success("**Exemplo de Post Muito Positivo:**")
                    st.info(f"_{df_positivos.iloc[0]['texto']}_")

                df_negativos = df[df['sentimento'] == 'muito negativo']
                if not df_negativos.empty:
                    st.error("**Exemplo de Post Muito Negativo:**")
                    st.warning(f"_{df_negativos.iloc[0]['texto']}_")
else:
    st.info("Clique em 'Executar Análise' na barra lateral para começar.")