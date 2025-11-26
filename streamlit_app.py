import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import pdfplumber
import docx

# Carrega variáveis do .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="📄 Chat com Arquivos", layout="centered")
st.title("📄 Chat com Arquivos")
st.write("Faça upload de documentos e converse com o conteúdo deles.")

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------

def ler_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def ler_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def ler_arquivo(file):
    if file.name.endswith(".pdf"):
        return ler_pdf(file)
    elif file.name.endswith(".docx"):
        return ler_docx(file)
    else:
        return file.read().decode("utf-8")

# -----------------------------
# UPLOAD DE ARQUIVOS
# -----------------------------
uploaded_files = st.file_uploader(
    "Envie 1 ou mais arquivos",
    type=["txt", "pdf", "md", "docx"],
    accept_multiple_files=True
)

# Guarda o conteúdo de todos
if "contexto_docs" not in st.session_state:
    st.session_state.contexto_docs = ""

if uploaded_files:
    textos = []
    for f in uploaded_files:
        textos.append(f"### Arquivo: {f.name}\n" + ler_arquivo(f))

    st.session_state.contexto_docs = "\n\n".join(textos)
    st.success("📚 Arquivos carregados com sucesso! Já pode conversar.")

# -----------------------------
# HISTÓRICO DO CHAT
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Exibe mensagens antigas
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada do usuário
mensagem_usuario = st.chat_input("Digite sua mensagem...")

# -----------------------------
# GERA A RESPOSTA DA IA
# -----------------------------
if mensagem_usuario:

    if not st.session_state.contexto_docs.strip():
        st.warning("Envie pelo menos 1 arquivo antes de conversar.")
        st.stop()

    st.chat_message("user").markdown(mensagem_usuario)
    st.session_state.chat_history.append({"role": "user", "content": mensagem_usuario})

    mensagens = [
        {
            "role": "system",
            "content": f"""
Você é um assistente especializado em responder SOMENTE com base nos arquivos enviados pelo usuário.

NUNCA invente nada.  
Se não houver resposta no conteúdo dos documentos, diga:  
"Não encontrei essa informação nos arquivos enviados."

### DOCUMENTOS CARREGADOS
{st.session_state.contexto_docs}
"""
        }
    ] + st.session_state.chat_history

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=mensagens,
        temperature=0.0
    )

    resposta = response.choices[0].message.content

    st.chat_message("assistant").markdown(resposta)
    st.session_state.chat_history.append({"role": "assistant", "content": resposta})