import streamlit as st
import pymupdf as fitz
import pandas as pd
import tempfile
import re
from openai import OpenAI
from datetime import datetime
import os
import json

st.set_page_config(
    page_title="EQP - Elaborador de Questões de Prova",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Função para extrair texto diretamente do PDF
def extrair_texto_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texto_total = ""
    for pagina in doc:
        texto_total += pagina.get_text() + "\n"
    return texto_total


    

 

# Interface Streamlit
st.title("Gerador de questões de prova com IA")

st.write("Carregue um arquivo PDF com conteúdo para gerar questões para uma criança.")

# Inicializa o session_state se não existir
if 'texto_extraido' not in st.session_state:
    st.session_state.texto_extraido = None
    st.session_state.texto_extraido_limpo = None

# Chaves e URLs

DEEPSEEK_URL = "https://api.deepseek.com"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CLAUDE_URL = "https://api.anthropic.com/v1/"
MOONSHOT_URL = "https://api.moonshot.ai/v1"
GROK_URL = "https://api.x.ai/v1"


idade = st.selectbox("Idade da criança", list(range(6, 19)))

disciplinas_lista = [
    "Geografia", "Ensino Religioso", "História", "Matemática",
    "Língua Portuguesa", "Ciências da Natureza", "Inglês",
    "Filosofia", "Educação Física", "Artes", "Ciências Humanas", "Linguagens"
]
disciplinas_ordenadas = sorted(disciplinas_lista)

disciplina = st.multiselect(
    "Escolha a(s) disciplina(s)",
    disciplinas_ordenadas
)

topicos = st.text_area("Tópicos de estudo", height=150)
competencias = st.text_area("Competências e habilidades a serem desenvolvidas", height=150)

quantidade_questoes_multipla = st.number_input("Quantidade de questões de múltipla escolha (Resposta Única)", min_value=1, value=10)
quantidade_questoes_multipla_varios = st.number_input("Quantidade de questões de múltipla escolha (Resposta Múltipla)", min_value=1, value=10)
quantidade_questoes_ordenacao = st.number_input("Quantidade de questões de ordenação", min_value=1, value=10)
quantidade_questoes_vf = st.number_input("Quantidade de questões do tipo Verdadeiro ou Falso", min_value=0, value=5)
quantidade_questoes_abertas = st.number_input("Quantidade de questões abertas", min_value=0, value=3)
quantidade_questoes_dissertativas = st.number_input("Quantidade de questões dissertativas", min_value=0, value=1)
quantidade_linhas_questoes_dissertativas = st.number_input("Quantidade mínima de linhas nas questões dissertativas", min_value=0, value=10)
quantidade_questoes_interpretacao = st.number_input("Quantidade de questões de interpretação textual", min_value=0, value=5)
quantidade_questoes_sentence_completion = st.number_input("Quantidade de questões sentence completion (somente inglês)", min_value=0, value=3)

arquivo_pdf = st.file_uploader("Escolha um arquivo PDF do tipo pesquisável", type=["pdf"])

# Inicializa o session_state se não existir
if 'texto_extraido' not in st.session_state:
    st.session_state.texto_extraido = None
    st.session_state.texto_extraido_limpo = None

# Botão explícito para processar o PDF
if arquivo_pdf and st.button("Extrair Texto do PDF"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(arquivo_pdf.read())
        caminho_pdf = tmp.name

    def limpar_texto_ocr(texto):
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        linhas = [linha for linha in texto.split('\n') if len(linha.strip())> 3]
        texto = '\n'.join(linhas)
        return texto
    


    with st.spinner("Processando PDF..."):
        texto_extraido = extrair_texto_pdf(caminho_pdf)
        texto_extraido_limpo = limpar_texto_ocr(texto_extraido)
        
        # Armazena no session_state
        st.session_state.texto_extraido = texto_extraido
        st.session_state.texto_extraido_limpo = texto_extraido_limpo
    
    st.success("Texto extraído com sucesso!")

# Mostra o resultado apenas se já foi processado
if st.session_state.texto_extraido is not None:
    df = pd.DataFrame({
        "conteudo": [st.session_state.texto_extraido],
        "conteudo_limpo": [st.session_state.texto_extraido_limpo]
    })
    st.dataframe(df)


# --- Carrega provedores e modelos do arquivo JSON ---
with open("modelos.json", "r", encoding="utf-8") as f:
    model_options: dict = json.load(f)

provider = st.selectbox("Escolha o provedor de IA:", list(model_options.keys()))
models_for_provider = model_options.get(provider, [])

model = st.selectbox("Escolha o modelo de IA:", models_for_provider)

st.info(f"Provedor: **{provider}** | Modelo: **{model}**")

temperatura = st.slider(
    "Temperatura (Quanto maior o valor, mais criativo é o modelo)",
    min_value=0.0,
    max_value=1.0,
    value=0.0,  # Valor padrão
    step=0.1,   # Incremento (pode ser 0.01 para mais precisão)
)

pwd = st.text_input("API Key", type="password")

if st.session_state.texto_extraido_limpo is not None:
    if st.button("Enviar"):
        # Configura cliente com base no provedor
        if provider == "OpenAI":
         client = OpenAI(api_key=pwd, timeout=300.0, max_retries=0)
        elif provider == "Gemini":
         client = OpenAI(api_key=pwd, base_url=GEMINI_URL, timeout=300.0, max_retries=0)
        elif provider == "Claude":
         client = OpenAI(api_key=pwd, base_url=CLAUDE_URL, timeout=300.0, max_retries=0)
        elif provider == "DeepSeek":
         client = OpenAI(api_key=pwd, base_url=DEEPSEEK_URL, timeout=300.0, max_retries=0)
        elif provider == "Moonshot":
         client = OpenAI(api_key=pwd, base_url=MOONSHOT_URL, timeout=300.0, max_retries=0)
        elif provider == "GROK":
         client = OpenAI(api_key=pwd, base_url=GROK_URL, timeout=300.0, max_retries=0) 
    
        
        # 1. Carrega o conteúdo "cru" do txt
        with open("prompt.txt", "r", encoding="utf-8") as f:
            template_prompt = f.read()
    
        
        # 3. Injeta a variável no texto lido
        prompt_usuario = template_prompt.format(
            disciplina=disciplina,
            idade=idade,
            quantidade_questoes_multipla=quantidade_questoes_multipla,
            quantidade_questoes_multipla_varios=quantidade_questoes_multipla_varios,
            quantidade_questoes_vf=quantidade_questoes_vf,
            quantidade_questoes_ordenacao=quantidade_questoes_ordenacao,
            quantidade_questoes_abertas=quantidade_questoes_abertas,
            quantidade_questoes_sentence_completion=quantidade_questoes_sentence_completion,
            quantidade_questoes_interpretacao=quantidade_questoes_interpretacao,
            quantidade_questoes_dissertativas=quantidade_questoes_dissertativas,
            quantidade_linhas_questoes_dissertativas=quantidade_linhas_questoes_dissertativas,
            topicos=topicos,
            competencias=competencias,
            texto_extraido_limpo=st.session_state.texto_extraido_limpo
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"Você é um assistente pedagógico especializado em criar questões para crianças de {idade} anos."},
                    {"role": "user", "content": prompt_usuario}
                ],
                temperature=temperatura,
                max_tokens = 20000
            )

            # Extrai o conteúdo da resposta
            conteudo_resposta = response.choices[0].message.content
            # Exibe sucesso e conteúdo
            st.success("Questões geradas com sucesso!")
            st.write("Modelo utilizado:", model)
            st.subheader("Resposta da API:")
            st.write(conteudo_resposta)
            nome_arquivo = f"questoes_{'_'.join(disciplina)}_{model}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
            # Botão para baixar como.txt
            st.download_button(
                label="📥 Baixar questões em arquivo .txt",
                data=conteudo_resposta,
                file_name=nome_arquivo,
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Erro na requisição: {e}")










