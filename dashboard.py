import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime
import io


from config.settings import validar_configuracao_completa
from core.database import (
    ensure_table_exists, 
    apagar_base_de_dados, 
    obter_nao_analisados, 
    atualizar_analise, 
    obter_analisados_como_dataframe,
    contar_registros
)
from core.coletar_dados import coletar_dados_reddit
from core.analise_sentimento import analisar_textos_em_lote

# --- Configuracao da Pagina ---
st.set_page_config(page_title="Análise de Sentimentos", layout="wide", initial_sidebar_state="expanded")

# --- Validacao de Configuracoes ---
if not validar_configuracao_completa(silencioso=True):
    st.error("Configurações incompletas. Verifique o arquivo .env com as variáveis necessárias.")
    st.code("""
REDDIT_CLIENT_ID=seu_client_id
REDDIT_CLIENT_SECRET=seu_client_secret
REDDIT_USER_AGENT=seu_user_agent
GEMINI_API_KEY=sua_api_key
    """, language="bash")
    st.stop()


# --- Funcoes com Cache ---

@st.cache_data(ttl=60)
def carregar_dados_analisados():
    """Carrega dados do banco com cache de 60 segundos."""
    return obter_analisados_como_dataframe()


@st.cache_data
def gerar_nuvem_palavras(texto: str):
    """Gera nuvem de palavras com cache."""
    return WordCloud(
        width=800, 
        height=400, 
        background_color='white', 
        collocations=False
    ).generate(texto)


def limpar_cache():
    """Limpa o cache do Streamlit."""
    carregar_dados_analisados.clear()
    gerar_nuvem_palavras.clear()


def calcular_metricas(df: pd.DataFrame) -> dict:
    """Calcula metricas do DataFrame."""
    if df.empty:
        return {'total': 0, 'sentimento': 'N/A', 'topico': 'N/A'}
    
    sentimento = df['sentimento'].mode()
    topico = df['topico'].mode()
    
    return {
        'total': len(df),
        'sentimento': sentimento.iloc[0].capitalize() if not sentimento.empty else 'N/A',
        'topico': topico.iloc[0].capitalize() if not topico.empty else 'N/A'
    }


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza colunas do DataFrame."""
    df = df.copy()
    for col in ['sentimento', 'emocao', 'topico']:
        if col in df.columns:
            df[col] = df[col].str.strip().str.lower()
    return df


# --- Funcoes de Exportacao ---

def gerar_relatorio_csv(df: pd.DataFrame) -> bytes:
    """Gera arquivo CSV para download."""
    return df.to_csv(index=False).encode('utf-8')


def gerar_relatorio_excel(df: pd.DataFrame, metricas: dict, palavra_chave: str) -> bytes:
    """Gera arquivo Excel com multiplas abas."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba de dados
        df.to_excel(writer, sheet_name='Dados', index=False)
        
        # Aba de resumo
        resumo = pd.DataFrame([
            {'Métrica': 'Palavra-chave', 'Valor': palavra_chave},
            {'Métrica': 'Total de Posts', 'Valor': metricas['total']},
            {'Métrica': 'Sentimento Predominante', 'Valor': metricas['sentimento']},
            {'Métrica': 'Tópico Principal', 'Valor': metricas['topico']},
            {'Métrica': 'Data da Análise', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Aba de distribuicao de sentimentos
        dist_sentimento = df['sentimento'].value_counts().reset_index()
        dist_sentimento.columns = ['Sentimento', 'Quantidade']
        dist_sentimento.to_excel(writer, sheet_name='Sentimentos', index=False)
        
        # Aba de distribuicao de emocoes
        dist_emocao = df['emocao'].value_counts().reset_index()
        dist_emocao.columns = ['Emoção', 'Quantidade']
        dist_emocao.to_excel(writer, sheet_name='Emoções', index=False)
    
    return output.getvalue()


def gerar_relatorio_texto(df: pd.DataFrame, metricas: dict, palavra_chave: str) -> str:
    """Gera relatorio em formato texto."""
    linhas = [
        "=" * 60,
        "RELATÓRIO DE ANÁLISE DE SENTIMENTOS",
        "=" * 60,
        "",
        f"Data do Relatório: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Palavra-chave Analisada: {palavra_chave}",
        "",
        "-" * 40,
        "RESUMO GERAL",
        "-" * 40,
        f"Total de Posts Analisados: {metricas['total']}",
        f"Sentimento Predominante: {metricas['sentimento']}",
        f"Tópico Principal: {metricas['topico']}",
        "",
        "-" * 40,
        "DISTRIBUIÇÃO DE SENTIMENTOS",
        "-" * 40,
    ]
    
    for sentimento, count in df['sentimento'].value_counts().items():
        percentual = count / len(df) * 100
        linhas.append(f"  {sentimento.capitalize()}: {count} ({percentual:.1f}%)")
    
    linhas.extend([
        "",
        "-" * 40,
        "DISTRIBUIÇÃO DE EMOÇÕES",
        "-" * 40,
    ])
    
    for emocao, count in df['emocao'].value_counts().items():
        percentual = count / len(df) * 100
        linhas.append(f"  {emocao.capitalize()}: {count} ({percentual:.1f}%)")
    
    linhas.extend([
        "",
        "-" * 40,
        "TÓPICOS IDENTIFICADOS",
        "-" * 40,
    ])
    
    for topico, count in df['topico'].value_counts().head(10).items():
        linhas.append(f"  {topico.capitalize()}: {count}")
    
    linhas.extend([
        "",
        "=" * 60,
        "FIM DO RELATÓRIO",
        "=" * 60,
    ])
    
    return "\n".join(linhas)


# --- Pipeline Principal ---

def executar_pipeline_completo(palavra_chave, max_posts):
    """Executa o pipeline completo de coleta e analise."""
    # Limpa cache antes de nova analise
    limpar_cache()
    
    apagar_base_de_dados()
    ensure_table_exists()
    st.toast("Base de dados recriada para a nova análise!")

    with st.spinner(f"Coletando {max_posts} posts sobre '{palavra_chave}'..."):
        coletar_dados_reddit(palavra_chave, max_posts=max_posts)
    st.toast("Coleta de dados concluída!", icon="✅")

    posts_para_analisar = obter_nao_analisados()
    if not posts_para_analisar:
        st.warning("Nenhum post encontrado para a palavra-chave. Tente outro termo.")
        return False

    with st.spinner("Analisando todos os posts com IA..."):
        resultados_analise = analisar_textos_em_lote(posts_para_analisar)
    
    if resultados_analise:
        for post_id, analise in resultados_analise.items():
            atualizar_analise(
                post_id, 
                analise['sentimento'], 
                analise['emocao'], 
                analise['topico'], 
                analise['entidades'], 
                analise['aspectos']
            )
        st.toast("Análise com IA concluída!", icon="✅")
        return True
    else:
        st.error("Falha ao analisar os posts. Verifique os logs para mais detalhes.")
        return False


# --- Constantes de Visualizacao ---

CORES_SENTIMENTO = {
    'muito positivo': '#1A5D1A', 
    'positivo': '#4CAF50', 
    'neutro': '#BDBDBD', 
    'negativo': '#F44336',
    'muito negativo': '#A60000'
}


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
    
    max_posts_slider = st.slider(
        "Número máximo de posts:", 
        min_value=5, 
        max_value=50, 
        value=10
    )
    
    if st.button("Executar Análise", type="primary", use_container_width=True):
        st.session_state.analise_executada = True
        st.session_state.palavra_chave = palavra_chave_input
        st.session_state.sucesso_analise = executar_pipeline_completo(
            palavra_chave_input, 
            max_posts_slider
        )
    
    # Secao de exportacao
    if 'analise_executada' in st.session_state and st.session_state.get('sucesso_analise'):
        st.markdown("---")
        st.subheader("Exportar Resultados")
        
        df_export = carregar_dados_analisados()
        if not df_export.empty:
            df_export = preparar_dataframe(df_export)
            metricas_export = calcular_metricas(df_export)
            palavra = st.session_state.get('palavra_chave', 'analise')
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                # Download CSV
                csv_data = gerar_relatorio_csv(df_export)
                st.download_button(
                    label="CSV",
                    data=csv_data,
                    file_name=f"analise_{palavra}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                # Download Texto
                txt_data = gerar_relatorio_texto(df_export, metricas_export, palavra)
                st.download_button(
                    label="TXT",
                    data=txt_data,
                    file_name=f"relatorio_{palavra}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    st.markdown("---")
    st.markdown("Desenvolvido para o TCC de Análise de Sentimentos.")


# --- Area Principal do Dashboard ---

st.title("Dashboard Interativo de Análise de Sentimentos")

if 'analise_executada' in st.session_state and st.session_state.sucesso_analise:
    st.header(
        f"Resultados da Análise para: '{st.session_state.palavra_chave}'", 
        divider='rainbow'
    )

    # Carrega dados com cache
    df = carregar_dados_analisados()

    if not df.empty:
        # Prepara dados
        df = preparar_dataframe(df)
        metricas = calcular_metricas(df)
        
        # Metricas principais
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Posts Analisados", metricas['total'])
        col2.metric("Sentimento Predominante", metricas['sentimento'])
        col3.metric("Tópico Principal", metricas['topico'])

        st.markdown("---")

        # Tabs de conteudo
        tab_graficos, tab_temporal, tab_dados, tab_insights = st.tabs([
            "📊 Resumo Gráfico", 
            "📈 Análise Temporal",
            "📄 Dados Detalhados", 
            "💡 Insights Adicionais"
        ])

        with tab_graficos:
            c1, c2 = st.columns(2)
            
            with c1:
                # Grafico de sentimentos
                fig_sentimento = px.pie(
                    df, 
                    names='sentimento', 
                    title='Distribuição de Sentimentos (5 Níveis)', 
                    hole=.4, 
                    color='sentimento', 
                    color_discrete_map=CORES_SENTIMENTO
                )
                st.plotly_chart(fig_sentimento, use_container_width=True)
                
                # Grafico de topicos
                contagem_topicos = df['topico'].value_counts().reset_index().head(10)
                fig_topicos = px.bar(
                    contagem_topicos, 
                    x='topico', 
                    y='count', 
                    title='Tópicos Mais Comentados (Gerados por IA)', 
                    color='topico'
                )
                st.plotly_chart(fig_topicos, use_container_width=True)
            
            with c2:
                # Grafico de emocoes
                contagem_emocoes = df['emocao'].value_counts().reset_index()
                fig_emocao = px.bar(
                    contagem_emocoes, 
                    x='emocao', 
                    y='count', 
                    title='Distribuição de Emoções', 
                    color='emocao'
                )
                st.plotly_chart(fig_emocao, use_container_width=True)

        with tab_temporal:
            st.header("Análise Temporal dos Sentimentos")
            
            # Converte coluna data para datetime
            df_temporal = df.copy()
            df_temporal['data'] = pd.to_datetime(df_temporal['data'])
            df_temporal['data_apenas'] = df_temporal['data'].dt.date
            
            # Mapeamento de sentimentos para valores numericos
            mapa_sentimento_valor = {
                'muito negativo': -2,
                'negativo': -1,
                'neutro': 0,
                'positivo': 1,
                'muito positivo': 2
            }
            df_temporal['sentimento_valor'] = df_temporal['sentimento'].map(mapa_sentimento_valor)
            
            # Grafico de linha temporal
            if len(df_temporal['data_apenas'].unique()) > 1:
                # Agrupa por data
                df_por_data = df_temporal.groupby('data_apenas').agg({
                    'sentimento_valor': 'mean',
                    'id': 'count'
                }).reset_index()
                df_por_data.columns = ['Data', 'Sentimento Médio', 'Quantidade']
                
                fig_temporal = px.line(
                    df_por_data,
                    x='Data',
                    y='Sentimento Médio',
                    title='Evolução do Sentimento ao Longo do Tempo',
                    markers=True
                )
                fig_temporal.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_temporal.update_yaxes(
                    ticktext=['Muito Negativo', 'Negativo', 'Neutro', 'Positivo', 'Muito Positivo'],
                    tickvals=[-2, -1, 0, 1, 2]
                )
                st.plotly_chart(fig_temporal, use_container_width=True)

                
                # Grafico de barras empilhadas por data
                df_sentimento_data = df_temporal.groupby(
                    ['data_apenas', 'sentimento']
                ).size().reset_index(name='count')
                
                fig_barras = px.bar(
                    df_sentimento_data,
                    x='data_apenas',
                    y='count',
                    color='sentimento',
                    title='Distribuição de Sentimentos por Data',
                    color_discrete_map=CORES_SENTIMENTO,
                    barmode='stack'
                )
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("Análise temporal requer posts de múltiplas datas.")
                
            # Metricas temporais
            st.subheader("Estatísticas Temporais")
            col_t1, col_t2, col_t3 = st.columns(3)
            
            sentimento_medio = df_temporal['sentimento_valor'].mean()
            sentimento_texto = 'Neutro'
            if sentimento_medio > 0.5:
                sentimento_texto = 'Positivo'
            elif sentimento_medio > 1.5:
                sentimento_texto = 'Muito Positivo'
            elif sentimento_medio < -0.5:
                sentimento_texto = 'Negativo'
            elif sentimento_medio < -1.5:
                sentimento_texto = 'Muito Negativo'
            
            col_t1.metric("Sentimento Médio", sentimento_texto, f"{sentimento_medio:.2f}")
            col_t2.metric("Desvio Padrão", f"{df_temporal['sentimento_valor'].std():.2f}")
            col_t3.metric("Período Analisado", f"{len(df_temporal['data_apenas'].unique())} dia(s)")

        with tab_dados:
            st.header("Explore os Dados Analisados")
            
            opcoes_sentimento = ['Todos'] + sorted(df['sentimento'].unique().tolist())
            sentimento_filtro = st.selectbox(
                "Filtrar por Sentimento:", 
                options=opcoes_sentimento
            )
            
            if sentimento_filtro == 'Todos':
                df_filtrado = df
            else:
                df_filtrado = df[df['sentimento'] == sentimento_filtro]
            
            st.dataframe(df_filtrado, use_container_width=True)

        with tab_insights:
            st.header("Insights Adicionais")
            col_insights1, col_insights2 = st.columns(2)
            
            with col_insights1:
                st.subheader("Nuvem de Entidades")
                
                # Extrai entidades
                entidades_flat = [
                    ent.strip().lower() 
                    for sublist in df['entidades'].str.split(',') 
                    for ent in sublist 
                    if ent.strip().lower() not in ['nenhuma', '']
                ]
                
                if entidades_flat:
                    texto_nuvem = " ".join(entidades_flat)
                    wordcloud = gerar_nuvem_palavras(texto_nuvem)
                    
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)
                    plt.close(fig)
                else:
                    st.write("Nenhuma entidade significativa encontrada.")
            
            with col_insights2:
                st.subheader("Exemplos de Posts")
                
                # Post muito positivo
                df_positivos = df[df['sentimento'] == 'muito positivo']
                if not df_positivos.empty:
                    st.success("**Exemplo de Post Muito Positivo:**")
                    st.info(f"_{df_positivos.iloc[0]['texto']}_")

                # Post muito negativo
                df_negativos = df[df['sentimento'] == 'muito negativo']
                if not df_negativos.empty:
                    st.error("**Exemplo de Post Muito Negativo:**")
                    st.warning(f"_{df_negativos.iloc[0]['texto']}_")
                
                # Se nao houver extremos, mostra neutro
                if df_positivos.empty and df_negativos.empty:
                    df_neutros = df[df['sentimento'] == 'neutro']
                    if not df_neutros.empty:
                        st.info("**Exemplo de Post Neutro:**")
                        st.write(f"_{df_neutros.iloc[0]['texto']}_")
        
        # Secao de Exportacao
        st.markdown("---")
        st.subheader("Exportar Relatório")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        palavra_chave = st.session_state.palavra_chave
        
        with col_exp1:
            csv_data = gerar_relatorio_csv(df)
            st.download_button(
                label="📄 Baixar CSV",
                data=csv_data,
                file_name=f"analise_{palavra_chave}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            try:
                excel_data = gerar_relatorio_excel(df, metricas, palavra_chave)
                st.download_button(
                    label="📊 Baixar Excel",
                    data=excel_data,
                    file_name=f"analise_{palavra_chave}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.warning("Instale openpyxl para exportar Excel")
        
        with col_exp3:
            texto_relatorio = gerar_relatorio_texto(df, metricas, palavra_chave)
            st.download_button(
                label="📝 Baixar Relatório TXT",
                data=texto_relatorio,
                file_name=f"relatorio_{palavra_chave}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

else:
    st.info("Clique em 'Executar Análise' na barra lateral para começar.")
