import streamlit as st
import fitz  # PyMuPDF
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import tempfile
import io

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================

st.set_page_config(page_title="Gerador de Questões com IA", layout="wide")
st.title("📘 Gerador de questões de prova com IA")

st.write(
    "Carregue um arquivo PDF (escaneado ou digital) para extrair o conteúdo "
    "e gerar questões pedagógicas adequadas à faixa etária."
)

# =========================================================
# OCR (EasyOCR — compatível com Streamlit Cloud)
# =========================================================

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(
        ['pt'],   # Português
        gpu=False
    )


def extrair_imagens_pdf(pdf_path: str) -> list[Image.Image]:
    doc = fitz.open(pdf_path)
    imagens = []

    for pagina in doc:
        pix = pagina.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        imagens.append(img)

    return imagens


def aplicar_ocr_em_imagens(imagens: list[Image.Image]) -> str:
    reader = carregar_ocr()
    texto_total = ""

    for img in imagens:
        img_np = np.array(img)
        resultados = reader.readtext(img_np, detail=0, paragraph=True)
        texto_total += "\n".join(resultados) + "\n\n"

    return texto_total.strip()


# =========================================================
# SESSION STATE
# =========================================================

if "texto_extraido" not in st.session_state:
    st.session_state.texto_extraido = None

# =========================================================
# INTERFACE — PARÂMETROS PEDAGÓGICOS
# =========================================================

idade = st.selectbox("Idade da criança", list(range(6, 19)))

disciplina = st.multiselect(
    "Disciplina(s)",
    [
        "Geografia", "História", "Matemática",
        "Língua Portuguesa", "Ciências",
        "Inglês", "Filosofia", "Artes"
    ]
)

topicos = st.text_area("Tópicos de estudo", height=120)
competencias = st.text_area("Competências e habilidades", height=120)

quantidade_multipla = st.number_input(
    "Questões de múltipla escolha",
    min_value=1, value=10
)

quantidade_vf = st.number_input(
    "Questões Verdadeiro/Falso",
    min_value=0, value=5
)

quantidade_abertas = st.number_input(
    "Questões abertas",
    min_value=0, value=3
)

# =========================================================
# UPLOAD E OCR DO PDF
# =========================================================

arquivo_pdf = st.file_uploader("📄 Envie um arquivo PDF", type=["pdf"])

if arquivo_pdf and st.button("📑 Extrair texto do PDF"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(arquivo_pdf.read())
        caminho_pdf = tmp.name

    with st.spinner("Extraindo texto via OCR..."):
        imagens = extrair_imagens_pdf(caminho_pdf)
        texto = aplicar_ocr_em_imagens(imagens)
        st.session_state.texto_extraido = texto

    st.success("✅ Texto extraído com sucesso!")

# =========================================================
# EXIBIÇÃO DO TEXTO EXTRAÍDO
# =========================================================

if st.session_state.texto_extraido:
    st.subheader("📄 Texto extraído do PDF")
    st.text_area(
        "Conteúdo OCR",
        st.session_state.texto_extraido,
        height=300
    )

    df = pd.DataFrame({
        "conteudo_ocr": [st.session_state.texto_extraido]
    })

    st.download_button(
        "⬇️ Baixar texto extraído (CSV)",
        df.to_csv(index=False),
        file_name="texto_extraido.csv",
        mime="text/csv"
    )




