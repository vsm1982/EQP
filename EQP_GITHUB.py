import streamlit as st
import pymupdf as fitz
import pytesseract
from PIL import Image
import pandas as pd
import tempfile
import io
import re
from openai import OpenAI
from datetime import datetime
import os
from anthropic import Anthropic



# Configuração do caminho do Tesseract no Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Função para extrair imagens das páginas do PDF
def extrair_imagens_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    imagens = []
    for pagina in doc:
        pix = pagina.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        imagens.append(img)
    return imagens

# Função para aplicar OCR em uma lista de imagens
def aplicar_ocr_em_imagens(imagens):
    texto_total = ""
    for img in imagens:
        texto = pytesseract.image_to_string(img, lang='por')
        texto_total += texto + "\n"
    return texto_total


    

 

# Interface Streamlit
st.title("Gerador de questões de prova com IA")

st.write("Carregue um arquivo PDF com conteúdo para gerar questões para uma criança.")

# Inicializa o session_state se não existir
if 'texto_extraido' not in st.session_state:
    st.session_state.texto_extraido = None
    st.session_state.texto_extraido_limpo = None

# Chaves e URLs
OPENAI_API_KEY = "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"
DEEPSEEK_API_KEY = "sk-5b3d5b6b0594415c911d5d5195d2e362"
GEMINI_API_KEY = "AIzaSyDG4Jr_24C893rxSdeIeVKrN5re3pKqOow"
CLAUDE_API_KEY = "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"
MOONSHOT_API_KEY = "sk-zOBlAOEskC6e8RQunBoPhoFuOm9LdipENn29QlHAnaPjC8lZ"
GROK_API_KEY = "xai-VmTXn8hm0ooRx11uMqpJwd7Qm2y5f2YivKRcMwWpkYnfkih8xPAD2jHVAcYVwhy6oslIEWpgxO8CBP0V"
DEEPSEEK_URL = "https://api.deepseek.com"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CLAUDE_URL = "https://api.anthropic.com/v1/"
MOONSHOT_URL = "https://api.moonshot.ai/v1"
GROK_URL = "https://api.x.ai/v1"


idade = st.selectbox("Idade da criança", list(range(6, 19)))
disciplina = st.multiselect("Escolha a(s) disciplina(s)", ["Geografia", "Ensino Religioso", "História", "Matemática", "Língua Portuguesa", "Ciências", "Inglês", "Filosofia", "Educação Física", "Artes"])
topicos = st.text_area("Tópicos de estudo", height=150)
competencias = st.text_area("Competências e habilidades a serem desenvolvidas", height=150)

quantidade_questoes_multipla = st.number_input("Quantidade de questões de múltipla escolha", min_value=1, value=10)
quantidade_questoes_vf = st.number_input("Quantidade de questões do tipo Verdadeiro ou Falso", min_value=0, value=5)
quantidade_questoes_abertas = st.number_input("Quantidade de questões abertas", min_value=0, value=3)
quantidade_questoes_sentence_completion = st.number_input("Quantidade de questões sentence completion (somente inglês)", min_value=0, value=3)
quantidade_questoes_dissertativas = st.number_input("Quantidade de questões dissertativas (com exceção de inglês e matemática)", min_value=0, value=1)
quantidade_linhas_questoes_dissertativas = st.number_input("Quantidade mínima de linhas nas questões dissertativas (com exceção de inglês e matemática)", min_value=0, value=20)
quantidade_questoes_interpretacao = st.number_input("Quantidade de questões de interpretação textual", min_value=0, value=5)


arquivo_pdf = st.file_uploader("Escolha um arquivo PDF", type=["pdf"])

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
        imagens = extrair_imagens_pdf(caminho_pdf)
        texto_extraido = aplicar_ocr_em_imagens(imagens)
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


# --- Fallback local (se a API falhar, você não perde a UI) ---
FALLBACK_MODEL_OPTIONS = {
    "OpenAI":   ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-5", "gpt-5-mini", "gpt-5-nano"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "Gemini":   ["gemini-2.5-flash"],
    "Claude":   ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
    "Moonshot": ["kimi-k2-0905-preview", "kimi-k2-thinking"],
    "GROK": ["grok-4.20-beta-0309-reasoning", "grok-4.20-beta-latest-non-reasoning"]
}

# --- Config de provedores "OpenAI-compatíveis" ---
# DeepSeek e Moonshot são OpenAI-compatíveis (basta base_url + api_key). [1](https://platform.claude.com/docs/en/api/openai-sdk)[3](https://api-docs.deepseek.com/)
# Gemini tem endpoint OpenAI-compatível no base_url indicado. [2](https://platform.claude.com/docs/en/api/models)
OPENAI_COMPAT = {
    "OpenAI":   {"api_key": OPENAI_API_KEY,   "base_url": None},
    "DeepSeek": {"api_key": DEEPSEEK_API_KEY, "base_url": DEEPSEEK_URL},
    "Gemini":   {"api_key": GEMINI_API_KEY,   "base_url": GEMINI_URL},
    "Moonshot": {"api_key": MOONSHOT_API_KEY, "base_url": MOONSHOT_URL},
    "GROK": {"api_key": GROK_API_KEY, "base_url": GROK_URL}
}

def _openai_client(api_key: str, base_url: str | None) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

def _list_models_openai_compat(provider: str) -> list[str]:
    cfg = OPENAI_COMPAT[provider]
    if not cfg["api_key"]:
        return []
    client = _openai_client(cfg["api_key"], cfg["base_url"])
    page = client.models.list()
    return sorted([m.id for m in page.data])

def _list_models_anthropic() -> list[str]:
    # Claude tem Models API própria (GET /v1/models). [4](https://platform.moonshot.ai/docs/api/chat.en-US)
    if not CLAUDE_API_KEY:
        return []
    client = Anthropic(api_key=CLAUDE_API_KEY)
    page = client.models.list()
    return sorted([m.id for m in page.data])

@st.cache_data(ttl=60 * 10, show_spinner=False)  # cache 10 minutos
def fetch_models_all() -> tuple[dict[str, list[str]], dict[str, str]]:
    """
    Retorna:
      - model_options (dict provedor -> lista de modelos)
      - errors (dict provedor -> mensagem de erro)
    """
    model_options: dict[str, list[str]] = {}
    errors: dict[str, str] = {}

    # OpenAI compat
    for prov in OPENAI_COMPAT.keys():
        try:
            ids = _list_models_openai_compat(prov)
            model_options[prov] = ids
        except Exception as e:
            errors[prov] = f"{type(e).__name__}: {e}"
            model_options[prov] = []

   # Claude (Anthropic)
    try:
        model_options["Claude"] = _list_models_anthropic()
    except Exception as e:
        errors["Claude"] = f"{type(e).__name__}: {e}"
        model_options["Claude"] = []

    # fallback se vazios
    for prov, ids in model_options.items():
        if not ids:
            model_options[prov] = FALLBACK_MODEL_OPTIONS.get(prov, [])

    return model_options, errors

# ---------------- UI ----------------
st.title("Seleção dinâmica de modelos (tempo real)")

with st.sidebar:
    if st.button("🔄 Atualizar lista agora"):
        fetch_models_all.clear()   # limpa o cache
        st.rerun()

model_options, errors = fetch_models_all()

if errors:
    with st.expander("⚠️ Provedores com erro (usando fallback)"):
        for prov, err in errors.items():
            st.write(f"**{prov}**: {err}")

provider = st.selectbox("Escolha o provedor:", list(model_options.keys()))
models_for_provider = model_options.get(provider, [])

# Proteção extra: se mesmo assim vazio, aplica fallback geral
if not models_for_provider:
    models_for_provider = FALLBACK_MODEL_OPTIONS.get(provider, [])

model = st.selectbox("Escolha o modelo:", models_for_provider)

st.info(f"Provedor: **{provider}** | Modelo: **{model}**")

temperatura = st.slider(
    "Temperatura (Quanto maior o valor, mais criativo é o modelo)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,  # Valor padrão
    step=0.1,   # Incremento (pode ser 0.01 para mais precisão)
)

pwd = st.text_input("API Key", type="password")

if st.session_state.texto_extraido_limpo is not None:
    if st.button("Enviar"):
        # Configura cliente com base no provedor
        if provider == "OpenAI":
         client = OpenAI(api_key=pwd)
        elif provider == "Gemini":
         client = OpenAI(api_key=pwd, base_url=GEMINI_URL)
        elif provider == "Claude":
         client = OpenAI(api_key=pwd, base_url=CLAUDE_URL)
        elif provider == "DeepSeek":
         client = OpenAI(api_key=pwd, base_url=DEEPSEEK_URL)
        elif provider == "Moonshot":
         client = OpenAI(api_key=pwd, base_url=MOONSHOT_URL)
        elif provider == "GROK":
         client = OpenAI(api_key=pwd, base_url=GROK_URL)
    # Requisição
        prompt_usuario = f"""
        # 1. Objetivo e Orientações Gerais:
        - Você está recebendo um conteúdo pedagógico escolar da(s) disciplina(s) {disciplina}, que inclui explicações e questões existentes sobre os conteúdos. Tudo o que será solicitado a seguir deve ser elaborado de acordo com tal conteúdo.
        - O texto foi extraído de um livro físico por meio de OCR, portanto, pode conter erros de reconhecimento. Considere apenas o que for inteligível e faça as correções que forem possíveis.
        - O público alvo são crianças de {idade} anos.
        - O objetivo é elaborar questões pedagógicas que ajudem na fixação do conteúdo.
        # 2. Lista de Instruções
        ## 2.1 Questões de múltipla escolha:
        - Elabore {quantidade_questoes_multipla} questões do tipo múltipla escolha, com 5 alternativas em cada questão, sendo apenas uma correta.
        ## 2.2 Questões do tipo verdadeiro/falso:
        - Elabore {quantidade_questoes_vf} alternativas do tipo 'Verdadeiro' ou 'Falso'.
        ## 2.3 Questões abertas: 
        Elabore {quantidade_questoes_abertas} questões subjetivas abertas.
        ## 2.4 Questões do tipo sentence completion: 
        - Somente para a disciplina **Inglês**, elabore {quantidade_questoes_sentence_completion} questões do tipo sentence completion.
        ## 2.5 Questões do tipo interpretação textual:
        Elabore {quantidade_questoes_interpretacao} questões de interpretação textual, que devem ser do tipo aberta.
        - Importante: considerando que a criança não terá acesso ao material de estudo na hora da prova, todas as questões de interpretação textual devem incluir o trecho de texto que permita a realização da interpretação. O tamanho do trecho deve variar conforme a questão proposta, dentro das habilidades esperadas para a faixa etária de {idade} anos.
        ## 2.6 Questões dissertativas: 
        - Com exceção das disciplinas **Matemática** e **Inglês**, elabore {quantidade_questoes_dissertativas} questões dissertativas, que devem ser respondidas com um mínimo de {quantidade_linhas_questoes_dissertativas} linhas, abordando os tópicos mais relevantes do conteúdo fornecido (informar que a pergunta precisa ser respondida com o mínimo de linhas informado). Para as disciplinas **Matemática** e **Inglês** esse item deve ser ignorado.
        # 3. Orientações Adicionais
        - Use linguagem adequada à faixa etária de {idade} anos, e no caso dos itens 2.1 e 2.2, garanta que as alternativas incorretas/falsas sejam plausíveis, mas claramente erradas.
        - Considere também os tópicos de aprendizagem: {topicos} e as seguintes competências e habilidades a serem desenvolvidas: {competencias}.
        - Com exceção da disciplina **Inglês**, as questões devem ser elaboradas em português brasileiro, respeitando as normas gramaticias e ortográficoas vigentes.
        # 4. Casos Especiais
        ##  4.1 Disciplina **Matemática**
        - Quando a disciplina escolhida for **Matemática**, caso seja adequada ao conteúdo fornecido, podem ser incluídas questões que envolvam raciocínio lógico e problemas matemáticos.
        ## 4.2 Disciplina **Inglês**
        - As questões de sentence completion devem ter foco em vocabulário e/ou gramática.
        - Todo o output (questões, alternativas, gabarito) deve ser produzido em **LÍNGUA INGLESA**.
        - Cada questão de sentence completion deve conter de 5 a 10 subitens, todos sobre o mesmo tema. **Não misture temáticas diferentes em uma mesma questão. Se a questão é sobre tempos verbais, todas as subquestões devem tratar de tempos verbais. Se a questão é sobre vocabulário, todas as subquestões devem tratar de vocabulário.**
        - O inglês é a segunda língua da criança. Desta forma, não use vocabulário fora do material fornecido, nem estruturas avançadas demais para a idade.
        ## 4.3 Questões existentes no conteúdo fornecido:
        - **NUNCA repita as questões originais** presentes no material. Crie variações que avaliem os mesmos conceitos, mas com formulação diferente e contextos alternativos, sempre respeitanto o conteúdo fornecido. 
        ### 4.3.1 **ESTRATÉGIAS DE VARIAÇÃO OBRIGATÓRIAS:**
        - Identifique o conceito central de cada questão original e crie uma nova pergunta que avalie o mesmo conceito
        - Altere fundamentalmente a estrutura: transforme questões diretas em situações-problema
        - Mude o contexto de aplicação mantendo a habilidade cognitiva requerida
        - Inverta a perspectiva (ex: em vez de "o que causa X", pergunte "qual efeito Y produz")
        - Você pode criar contextos, exemplos e situações novas, desde que coerentes com os conceitos do conteúdo fornecido.
        ### 4.3.2 **VALIDAÇÃO DE ORIGINALIDADE:**
        - Antes de finalizar cada questão, verifique mentalmente se ela não é uma reformulação superficial de questões existentes
        - Garanta que pelo menos 3 elementos sejam diferentes em relação às questões originais: contexto, estrutura linguística e exemplos utilizados
        - Priorize questões que exijam aplicação do conhecimento em vez de reprodução direta
        # 5. Orientações finais:
        - Dê prioridade aos conceitos mais fundamentais do conteúdo fornecido
        - Para cada conceito importante, crie pelo menos uma questão de cada tipo solicitado
        - Após cada questão, informe entre parênteses a qual tópico ela se refere.
        - Distribua os níveis de dificuldade de forma pedagogicamente apropriada: 
        * 50% de questões de nível **"Médio"**
        * 25% questões de nível **"Fácil"** para consolidar conceitos básicos
        * 25% de questões de nível **"Difícil"** para desafiar os alunos mais avançados
        # 6. Formato de Saída Esperado:
        ## 6.1 **Organize a prova da seguinte forma:**
        - Apresente as questões embaralhadas, não agrupando por tipo. A única exceção a esse regra são as questões dissertativas (2.6), que sempre devem ser apresentadas agrupadas ao final da prova.
        - Use numeração contínua em toda a prova (1, 2, 3... não reinicie a numeração)
        - Após cada questão, indique seu nível de dificuldade entre parênteses: (Fácil), (Médio) ou (Difícil)
        ## 6.1 **Gabarito:**
        - Apresente em seção separada no final, nunca junto às questões.
        - No gabarito, use apenas letras (A, B, C, D, E) para múltipla escolha e V/F para verdadeiro/falso.
        - Para as questões abertas, inclua apenas a resposta esperada.
        - Para as questões dissertativas, inclua a resposta esperada resumida e indique quais tópicos deveriam ser abordados.
        - Para as questões de sentence completion, inclua apenas a palavra correta para cada subitem.
        - Não repita o texto das questões no gabarito
        # 7. Conteúdo pedagógico fornecido:
        {st.session_state.texto_extraido_limpo}"""

        try:
            
            response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"Você é um assistente pedagógico especializado em criar questões para crianças de {idade} anos."},
                        {"role": "user", "content": prompt_usuario}
                    ],
                    temperature=temperatura

        )

            # Extrai o conteúdo da resposta
            conteudo_resposta = response.choices[0].message.content

            # Exibe sucesso e conteúdo
            st.success("Questões geradas com sucesso!")
            st.write("Modelo utilizado:", model)
            st.subheader("Resposta da API:")
            st.write(conteudo_resposta)

            nome_arquivo = f"questoes_{disciplina}_{model}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"

            # Botão para baixar como.txt
            st.download_button(
                label="📥 Baixar questões em arquivo .txt",
                data=conteudo_resposta,
                file_name=nome_arquivo,
                mime="text/plain"
        )

        except Exception as e:
            st.error(f"Erro na requisição: {e}")









