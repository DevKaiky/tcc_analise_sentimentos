import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

NOME_DO_MODELO = "models/gemini-flash-latest" 

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(NOME_DO_MODELO)
    print(f"API do Gemini configurada com sucesso usando o modelo '{NOME_DO_MODELO}'.")
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    model = None

def analisar_textos_em_lote(posts_para_analisar, tentativas_max=5):
    if not model:
        print("Modelo Gemini não inicializado.")
        return None

    # --- PROMPT ---
    prompt_header = (
        "Faça uma análise completa para cada um dos textos a seguir, numerados por ID. Siga estritamente as instruções:\n"
        "1.  **Sentimento**: Classifique numa escala de 5 pontos: 'muito positivo', 'positivo', 'neutro', 'negativo', 'muito negativo'.\n"
        "2.  **Emoção**: Classifique como 'alegria', 'raiva', 'tristeza', 'surpresa', 'antecipação' ou 'neutra'.\n"
        "3.  **Tópico**: Gere uma etiqueta de tópico curta e concisa (2-3 palavras) que resuma o assunto principal. Não use a palavra 'Outro'.\n"
        "4.  **Entidades**: Extraia entidades nomeadas. Se não houver, retorne 'nenhuma'.\n"
        "5.  **Aspectos**: Extraia aspectos e seus sentimentos associados. Se não houver, retorne 'nenhum'.\n\n"
        "Responda para cada texto no seguinte formato, um por linha:\n"
        "ID:<id_do_post>; Sentimento:<resultado>; Emoção:<resultado>; Tópico:<resultado>; Entidades:<resultado>; Aspectos:<resultado>\n\n"
        "--- INÍCIO DOS TEXTOS ---\n"
    )
    
    prompt_body = "\n".join([f"ID:{post['id']}; Texto:\"{post['texto']}\"" for post in posts_para_analisar])
    prompt_completo = prompt_header + prompt_body

    for tentativa in range(tentativas_max):
        try:
            response = model.generate_content(prompt_completo)
            
            resultados = {}
            for linha in response.text.strip().split('\n'):
                try:
                    parts = linha.split(';')
                    post_id = int(parts[0].split(':')[1])
                    resultados[post_id] = {
                        "sentimento": parts[1].split(':', 1)[1].strip(),
                        "emocao": parts[2].split(':', 1)[1].strip(),
                        "topico": parts[3].split(':', 1)[1].strip(),
                        "entidades": parts[4].split(':', 1)[1].strip(),
                        "aspectos": parts[5].split(':', 1)[1].strip()
                    }
                except (IndexError, ValueError) as e:
                    print(f"Aviso: Falha ao processar a linha da resposta da IA: '{linha}'. Erro: {e}")
                    continue 

            return resultados
        except Exception as e:
            print(f"[Erro na análise em lote] Tentativa {tentativa + 1}: {e}")
            time.sleep(5 * (tentativa + 1))

    print("[Falha] Não foi possível analisar os dados em lote.")
    return None