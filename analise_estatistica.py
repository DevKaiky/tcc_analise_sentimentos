import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from collections import Counter
import matplotlib.pyplot as plt

# Adiciona o diretório atual ao path para conseguir importar 'core' e 'config'
sys.path.append(os.getcwd())

# Configuração para visualização limpa no terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

class GeradorEstatisticas:
    def __init__(self, dataframe_ia):
        """
        Inicializa com o DataFrame contendo os resultados da IA.
        """
        self.df = dataframe_ia.copy()
        
        # Garantir conversão de data se a coluna existir
        if 'data' in self.df.columns:
            self.df['data'] = pd.to_datetime(self.df['data'])

    def gerar_dados_gerais(self):
        """Gera estatísticas descritivas gerais (N, janela temporal)."""
        n_total = len(self.df)
        data_min = self.df['data'].min() if 'data' in self.df.columns else None
        data_max = self.df['data'].max() if 'data' in self.df.columns else None
        
        stats = {
            'n_total': n_total,
            'inicio_coleta': data_min,
            'fim_coleta': data_max,
            'dias_cobertos': (data_max - data_min).days if data_max and data_min else 0
        }
        
        print("-" * 50)
        print("ESTATÍSTICAS GERAIS")
        print("-" * 50)
        for k, v in stats.items():
            print(f"{k}: {v}")
        
        return stats

    def gerar_distribuicoes(self):
        """Calcula distribuições percentuais de sentimentos e emoções."""
        print("\n" + "-" * 50)
        print("DISTRIBUIÇÃO DE SENTIMENTOS (IA)")
        print("-" * 50)
        dist_sent = self.df['sentimento'].value_counts(normalize=True) * 100
        print(dist_sent.round(2).to_string())
        
        print("\n" + "-" * 50)
        print("TOP 5 EMOÇÕES")
        print("-" * 50)
        top_emo = self.df['emocao'].value_counts().head(5)
        dist_emo = (self.df['emocao'].value_counts(normalize=True) * 100).head(5)
        
        df_emo = pd.DataFrame({'Qtd': top_emo, '%': dist_emo.round(2)})
        print(df_emo)

    def gerar_topicos_entidades(self):
        """Identifica tópicos e entidades mais frequentes."""
        print("\n" + "-" * 50)
        print("TOP 5 TÓPICOS")
        print("-" * 50)
        print(self.df['topico'].value_counts().head(5).to_string())
        
        print("\n" + "-" * 50)
        print("TOP 10 ENTIDADES")
        print("-" * 50)
        
        todas_entidades = []
        for ent_str in self.df['entidades'].dropna():
            if isinstance(ent_str, str):
                partes = [e.strip() for e in ent_str.split(',') if e.strip().lower() not in ['nenhuma', '']]
                todas_entidades.extend(partes)
        
        counts = Counter(todas_entidades)
        for ent, qtd in counts.most_common(10):
            print(f"{ent}: {qtd}")

    def validar_contra_humano(self, caminho_csv_manual, agrupar_3_classes=True):
        """
        Calcula acurácia comparando IA vs Humano com leitura robusta de CSV.
        """
        try:
            # TENTA LER COM VÍRGULA
            df_manual = pd.read_csv(caminho_csv_manual, sep=',')
            
            # SE FICOU TUDO EM UMA COLUNA SÓ OU NÃO ACHOU A COLUNA, TENTA PONTO E VÍRGULA
            if len(df_manual.columns) < 2 or 'sentimento_humano' not in df_manual.columns:
                df_manual = pd.read_csv(caminho_csv_manual, sep=';')
            
            # LIMPEZA DOS CABEÇALHOS (Remove espaços extras e deixa minúsculo)
            # Ex: " sentimento_humano " vira "sentimento_humano"
            df_manual.columns = df_manual.columns.str.strip().str.lower()
            
            # VERIFICAÇÃO DE SEGURANÇA
            if 'sentimento_humano' not in df_manual.columns:
                print("\nERRO CRÍTICO DE COLUNAS:")
                print(f"O script esperava a coluna: 'sentimento_humano'")
                print(f"Mas encontrou as colunas: {list(df_manual.columns)}")
                print("DICA: Verifique se digitou o cabeçalho corretamente na primeira linha do CSV.")
                return

            # Normalização básica do conteúdo (Maiúscula/Minúscula)
            df_manual['sentimento_humano'] = df_manual['sentimento_humano'].astype(str).str.lower().str.strip()
            
            # CRUZAMENTO DE DADOS (JOIN)
            if 'id' in df_manual.columns and 'id' in self.df.columns:
                df_validacao = pd.merge(self.df, df_manual[['id', 'sentimento_humano']], on='id', how='inner')
            else:
                print("AVISO: Coluna 'id' não encontrada no CSV manual. Tentando cruzar pelo texto...")
                # Tenta achar uma coluna que pareça texto
                col_texto_manual = 'texto' if 'texto' in df_manual.columns else df_manual.columns[0]
                col_texto_ia = 'texto'
                df_validacao = pd.merge(self.df, df_manual[[col_texto_manual, 'sentimento_humano']], 
                                      left_on=col_texto_ia, right_on=col_texto_manual, how='inner')
            
            if df_validacao.empty:
                print("\nERRO: O arquivo foi lido, mas nenhum ID ou Texto coincidiu entre o Banco de Dados e o CSV Manual.")
                print("Verifique se os IDs no seu CSV correspondem aos IDs que aparecem no painel/banco.")
                return

            y_true = df_validacao['sentimento_humano']
            y_pred = df_validacao['sentimento']

            # --- LÓGICA DE AGRUPAMENTO (3 CLASSES) ---
            if agrupar_3_classes:
                print("\n[INFO] Modo ativado: Agrupando sentimentos em 3 classes (Positivo / Negativo / Neutro)...")
                
                def simplificar(val):
                    # Se tiver 'positivo' (seja 'muito positivo' ou 'positivo'), vira 'positivo'
                    if 'positivo' in str(val): return 'positivo'
                    # Se tiver 'negativo' (seja 'muito negativo' ou 'negativo'), vira 'negativo'
                    if 'negativo' in str(val): return 'negativo'
                    # O resto é neutro
                    return 'neutro'
                
                y_true = y_true.apply(simplificar)
                y_pred = y_pred.apply(simplificar)
            # -----------------------------------------
            
            # Cálculo das Métricas
            acuracia = accuracy_score(y_true, y_pred)
            
            print("\n" + "=" * 60)
            print(f"RELATÓRIO DE VALIDAÇÃO ({'3 Classes' if agrupar_3_classes else '5 Classes'})")
            print("=" * 60)
            print(f"Total de itens validados manualmente: {len(df_validacao)}")
            print(f"ACURÁCIA (Concordância Humano x IA): {acuracia:.2%}")
            
            print("\nDetalhamento por Classe:")
            print(classification_report(y_true, y_pred, zero_division=0))
            
            print("\nMatriz de Confusão (Linhas=Real, Colunas=IA):")
            labels = sorted(list(set(y_true) | set(y_pred)))
            cm = confusion_matrix(y_true, y_pred, labels=labels)
            df_cm = pd.DataFrame(cm, index=labels, columns=labels)
            print(df_cm)
            
        except FileNotFoundError:
            print(f"\nERRO CRÍTICO: O arquivo '{caminho_csv_manual}' não foi encontrado.")
        except Exception as e:
            print(f"\nERRO INESPERADO: {str(e)}")

# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    try:
        # Importa as configurações do seu projeto original
        from config.settings import inicializar_configuracao
        from core.database import obter_analisados_como_dataframe
        
        # Carrega configurações (API Key, Banco, etc)
        inicializar_configuracao()
        
        print("Carregando dados analisados do banco de dados...")
        df_projeto = obter_analisados_como_dataframe()
        
        if not df_projeto.empty:
            stats = GeradorEstatisticas(df_projeto)
            
            # 1. Gera os "Dados Duros" para a Seção de Resultados
            stats.gerar_dados_gerais()
            stats.gerar_distribuicoes()
            stats.gerar_topicos_entidades()
            
            # 2. Executa a Validação Cruzada (Acurácia)
            # O script vai procurar o arquivo 'validacao_manual.csv'
            print("\n" + "#" * 30)
            print("INICIANDO VALIDAÇÃO MANUAL")
            print("#" * 30)
            stats.validar_contra_humano('validacao_manual.csv', agrupar_3_classes=True)
            
        else:
            print("\nAVISO: O banco de dados está vazio. Rode o dashboard e colete dados primeiro.")
            
    except ImportError as e:
        print(f"Erro de importação: {e}")
        print("Certifique-se de estar rodando este script na raiz do projeto (mesma pasta do dashboard.py)")