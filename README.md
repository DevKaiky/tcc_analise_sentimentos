# Sistema de Análise de Sentimentos

Sistema desenvolvido como Trabalho de Conclusão de Curso (TCC) para análise automatizada de sentimentos em postagens do Reddit utilizando Inteligência Artificial.

## Sobre o Projeto

Este projeto implementa um pipeline completo de análise de sentimentos que:
1. Coleta postagens do Reddit com base em palavras-chave
2. Analisa o conteúdo utilizando a API do Google Gemini
3. Classifica sentimentos, emoções, tópicos e entidades
4. Apresenta os resultados em um dashboard interativo

### Funcionalidades Principais

- **Coleta automatizada**: Busca postagens em subreddits específicos
- **Análise multidimensional**: Sentimento (5 níveis), emoção, tópico e entidades
- **Dashboard interativo**: Visualização com gráficos e métricas
- **Análise temporal**: Evolução do sentimento ao longo do tempo
- **Exportação de relatórios**: CSV e TXT para documentação

## Tecnologias Utilizadas

| Tecnologia | Finalidade |
|------------|-----------|
| Python 3.10+ | Linguagem principal |
| Streamlit | Interface do dashboard |
| Google Gemini | Análise de sentimentos via IA |
| PRAW | Integração com API do Reddit |
| SQLite | Armazenamento de dados |
| Plotly | Visualizações interativas |
| Pandas | Manipulação de dados |

## Estrutura do Projeto

```
projeto/
├── config/                  # Configurações
│   ├── __init__.py
│   ├── settings.py         # Variáveis de ambiente
│   └── logging_config.py   # Sistema de logs
├── core/                    # Módulos principais
│   ├── __init__.py
│   ├── database.py         # Operações de banco de dados
│   ├── coletar_dados.py    # Coleta do Reddit
│   └── analise_sentimento.py  # Análise com IA
├── tests/                   # Testes unitários
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_analyzer.py
│   └── test_config.py
├── logs/                    # Arquivos de log (gerado)
├── dashboard.py             # Interface Streamlit
├── main.py                  # Script de teste
├── requirements.txt         # Dependências
├── .env.example            # Template de configuração
└── README.md               # Este arquivo
```

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Conta no Reddit com credenciais de API
- Chave de API do Google Gemini

### Passo a Passo

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd projeto
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas credenciais.

### Obtendo Credenciais

#### Reddit API
1. Acesse https://www.reddit.com/prefs/apps
2. Clique em "Create App" ou "Create Another App"
3. Selecione "script" como tipo
4. Copie o `client_id` e `client_secret`

#### Google Gemini API
1. Acesse https://makersuite.google.com/app/apikey
2. Crie uma nova chave de API
3. Copie a chave gerada

## Uso

### Dashboard Interativo

```bash
streamlit run dashboard.py
```

Acesse `http://localhost:8501` no navegador.

### Script de Teste

```bash
python main.py
```

## Configuração

### Variáveis de Ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `REDDIT_CLIENT_ID` | Sim | ID do aplicativo Reddit |
| `REDDIT_CLIENT_SECRET` | Sim | Segredo do aplicativo Reddit |
| `REDDIT_USER_AGENT` | Sim | Identificador do agente |
| `GEMINI_API_KEY` | Sim | Chave da API do Gemini |
| `REDDIT_SUBREDDIT` | Não | Subreddit padrão (default: brasil) |
| `GEMINI_MODELO` | Não | Modelo do Gemini |
| `DATABASE_FILE` | Não | Nome do arquivo SQLite |

## Testes

Execute os testes com:

```bash
pytest tests/ -v
```

Para ver cobertura:

```bash
pytest tests/ -v --cov=core --cov=config
```

## Arquitetura

### Fluxo de Dados

```
[Reddit API] → [Coletor] → [SQLite] → [Analisador] → [Dashboard]
                               ↑                          ↓
                               └── [Gemini API] ←─────────┘
```

### Análise de Sentimentos

O sistema classifica cada texto em:

- **Sentimento**: muito positivo, positivo, neutro, negativo, muito negativo
- **Emoção**: alegria, raiva, tristeza, surpresa, antecipação, neutra
- **Tópico**: categoria gerada pela IA (2-3 palavras)
- **Entidades**: nomes próprios identificados
- **Aspectos**: elementos específicos mencionados

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Limitações Conhecidas

- Taxa de requisições limitada pela API do Reddit
- Análise depende da disponibilidade do Gemini
- Subreddit fixo por configuração (não dinâmico)
- Banco de dados local (não distribuído)

## Trabalhos Futuros

- [ ] Suporte a múltiplas redes sociais (Twitter/X, YouTube)
- [ ] Análise de sentimento em tempo real
- [ ] Modelo de IA local como alternativa
- [ ] API REST para integração
- [ ] Containerização com Docker

## Licença

Este projeto foi desenvolvido para fins acadêmicos como parte de um Trabalho de Conclusão de Curso.

## Autor

Desenvolvido para TCC de Análise de Sentimentos.

---

*Última atualização: 2024*
