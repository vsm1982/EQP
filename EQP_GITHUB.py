import streamlit as st
import pymupdf as fitz
import pandas as pd
import tempfile
import re
from openai import OpenAI
from datetime import datetime
import os
import json




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
disciplina = st.multiselect("Escolha a(s) disciplina(s)", ["Geografia", "Ensino Religioso", "História", "Matemática", "Língua Portuguesa", "Ciências", "Inglês", "Filosofia", "Educação Física", "Artes"])
topicos = st.text_area("Tópicos de estudo", height=150)
competencias = st.text_area("Competências e habilidades a serem desenvolvidas", height=150)

quantidade_questoes_multipla = st.number_input("Quantidade de questões de múltipla escolha", min_value=1, value=10)
quantidade_questoes_vf = st.number_input("Quantidade de questões do tipo Verdadeiro ou Falso", min_value=0, value=5)
quantidade_questoes_abertas = st.number_input("Quantidade de questões abertas", min_value=0, value=3)
quantidade_questoes_sentence_completion = st.number_input("Quantidade de questões sentence completion (somente inglês)", min_value=0, value=3)
quantidade_questoes_dissertativas = st.number_input("Quantidade de questões dissertativas (com exceção de inglês e matemática)", min_value=0, value=1)
quantidade_linhas_questoes_dissertativas = st.number_input("Quantidade mínima de linhas nas questões dissertativas (com exceção de inglês e matemática)", min_value=0, value=10)
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

provider = st.selectbox("Escolha o provedor:", list(model_options.keys()))
models_for_provider = model_options.get(provider, [])

model = st.selectbox("Escolha o modelo:", models_for_provider)

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
        - Considere também os tópicos de aprendizagem: {topicos} e as seguintes competências e habilidades a serem desenvolvidas: {competencias}. **MUITO IMPORTANTE: LIMITE A ELABORAÇÃO DAS QUESTÕES AOS TÓPICOS E COMPETÊNCIAS INFORMADOS, AINDA QUE O MATERIAL FORNECIDO POSSUA OUTRAS INFORMAÇÕES/CONTEÚDOS**
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










