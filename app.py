import io
import os
import pypdf
import streamlit as st
from openai import AzureOpenAI

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO (CSS)
# ==========================================
st.set_page_config(
    page_title="ChatBot RAG - Microsoft Foundry",
    page_icon="🤖",
    layout="centered",
)

# Injeção de CSS customizado para criar bordas elegantes e design profissional
st.markdown(
    """
    <style>
    /* Estilização geral do container principal */
    .main-container {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Ajuste na barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }

    /* Títulos e cabeçalhos */
    h1 {
        color: #1f2937;
        font-family: 'Helvetica Neue', sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# BARRA LATERAL (CREDENCIAS E RAG)
# ==========================================
with st.sidebar:
  st.header("⚙️ Configurações da API")
  st.markdown(
      "Credenciais carregadas para o Microsoft Foundry. Você pode alterá-las"
      " se necessário."
  )

  # Campos dinâmicos com os valores pré-preenchidos
  minha_chave = st.text_input(
      "Chave da API (minha_chave)",
      value=(
          "1gsyJYiGIr1rIjIm6heIq96VWJI5gMgXeXCaYCHx5WeeWGm3AMYvJQQJ99CJACHYHv6XJ3w3AAAAACOGUF3S"
      ),
      type="password",
      help="Chave secreta da API",
  )
  meu_endpoint = st.text_input(
      "Endpoint (meu_endpoint)",
      value="https://marcelomaffeis-7430-resource.services.ai.azure.com/openai/v1",
      help="URL do endpoint do Azure AI Studio",
  )
  meu_modelo = st.text_input(
      "Nome do Modelo (meu_modelo)",
      value="gpt-4.1-mini",
      help="Nome do Deployment configurado no Azure AI Studio",
  )

  st.markdown("---")
  st.header("📂 Base de Conhecimento (RAG)")
  st.markdown(
      "Envie um documento PDF ou TXT para que o bot utilize o conteúdo como"
      " contexto."
  )

  uploaded_file = st.file_uploader(
      "Escolha um arquivo", type=["pdf", "txt"], label_visibility="collapsed"
  )


  # Função para extrair texto dos arquivos
  def extract_text_from_file(file):
    text = ""
    if file is not None:
      file_extension = file.name.split(".")[-1].lower()
      if file_extension == "pdf":
        try:
          reader = pypdf.PdfReader(file)
          for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
              text += extracted + "\n"
        except Exception as e:
          st.error(f"Erro ao ler o PDF: {e}")
      elif file_extension == "txt":
        try:
          text = file.getvalue().decode("utf-8")
        except Exception as e:
          st.error(f"Erro ao ler o TXT: {e}")
    return text


  # Processamento e armazenamento do texto no session_state
  if uploaded_file:
    if (
        "uploaded_file_name" not in st.session_state
        or st.session_state.uploaded_file_name != uploaded_file.name
    ):
      with st.spinner("Processando documento..."):
        st.session_state.file_text = extract_text_from_file(uploaded_file)
        st.session_state.uploaded_file_name = uploaded_file.name
      st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
    else:
      st.info(f"Arquivo ativo: **{uploaded_file.name}**")
  else:
    st.session_state.file_text = ""
    st.session_state.uploaded_file_name = None

  st.markdown("---")
  st.markdown(
      "<small>Desenvolvido para fins acadêmicos - Microsoft"
      " Foundry</small>",
      unsafe_allow_html=True,
  )

# ==========================================
# INICIALIZAÇÃO DO CLIENTE DA API
# ==========================================
client = None
if minha_chave and meu_endpoint:
  try:
    client = AzureOpenAI(
        api_key=minha_chave, api_version="2024-02-01", azure_endpoint=meu_endpoint
    )
  except Exception as e:
    st.error(f"Erro ao inicializar o cliente da API: {e}")

# ==========================================
# INTERFACE PRINCIPAL DO CHAT
# ==========================================
st.title("🤖 ChatBot com RAG (Microsoft Foundry)")
st.write(
    "Faça perguntas gerais ou baseadas no documento enviado na barra lateral."
)

# Verificação se as credenciais foram informadas
if not minha_chave or not meu_endpoint:
  st.warning(
      "⚠️ Por favor, certifique-se de preencher a **Chave da API** e o"
      " **Endpoint** na barra lateral."
  )
else:
  # Container com borda customizada para a área do chat
  with st.container():
    # Inicialização do histórico de mensagens
    if "messages" not in st.session_state:
      st.session_state.messages = []

    # Exibição do histórico de conversas
    for message in st.session_state.messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Entrada do usuário
    if prompt := st.chat_input("Digite sua mensagem aqui..."):
      # Adiciona a mensagem do usuário ao histórico
      st.session_state.messages.append({"role": "user", "content": prompt})
      with st.chat_message("user"):
        st.markdown(prompt)

      # Construção do Contexto RAG
      system_prompt = (
          "Você é um assistente virtual inteligente e prestativo. Responda"
          " profissionalmente às perguntas do usuário."
      )

      if st.session_state.get("file_text"):
        system_prompt += (
            "\n\nUtilize primariamente o seguinte contexto extraído do"
            f" documento enviado pelo usuário para formular sua"
            f" resposta:\n--- CONTEXTO DO DOCUMENTO ---\n{st.session_state.file_text}\n---"
            " FIM DO CONTEXTO ---\nSe a resposta não estiver explícita no"
            " contexto fornecido, utilize seu conhecimento geral, mas avise"
            " que a resposta não veio diretamente do documento."
        )

      # Preparação das mensagens para a API
      messages_payload = [{"role": "system", "content": system_prompt}]
      for m in st.session_state.messages:
        messages_payload.append({"role": m["role"], "content": m["content"]})

      # Chamada à API do Microsoft Foundry (Azure OpenAI)
      with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando...")

        try:
          response = client.chat.completions.create(
              model=meu_modelo, messages=messages_payload, temperature=0.7
          )
          assistant_response = response.choices[0].message.content
          message_placeholder.markdown(assistant_response)
        except Exception as e:
          assistant_response = f"Ocorreu um erro ao comunicar com a API: {e}"
          message_placeholder.error(assistant_response)

      # Salva a resposta do assistente no histórico
      st.session_state.messages.append(
          {"role": "assistant", "content": assistant_response}
      )
        
