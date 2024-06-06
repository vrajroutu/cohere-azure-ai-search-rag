import streamlit as st  
import cohere  
from azure.search.documents import SearchClient  
from azure.search.documents.indexes import SearchIndexClient  
from azure.search.documents.models import VectorizableTextQuery  
from azure.core.credentials import AzureKeyCredential  
from utils.studio_style import apply_studio_style  
from utils.multilingual import create_or_update_index, index_documents, extract_text_from_pdf  
from dotenv import load_dotenv  
import os  
import tempfile  
from azure.search.documents.indexes.models import AIStudioModelCatalogName  
  
# Load environment variables from .env file  
load_dotenv()  
  
# Define keys and endpoints from environment variables  
AZURE_AI_STUDIO_COHERE_EMBED_KEY = os.getenv("AZURE_AI_STUDIO_COHERE_EMBED_KEY")  
AZURE_AI_STUDIO_COHERE_EMBED_ENDPOINT = os.getenv("AZURE_AI_STUDIO_COHERE_EMBED_ENDPOINT")  
AZURE_AI_STUDIO_COHERE_MULTIEMBED_KEY = os.getenv("AZURE_AI_STUDIO_COHERE_MULTIEMBED_KEY")  
AZURE_AI_STUDIO_COHERE_MULTIEMBED_ENDPOINT = os.getenv("AZURE_AI_STUDIO_COHERE_MULTIEMBED_ENDPOINT") 
AZURE_AI_STUDIO_COHERE_COMMAND_KEY = os.getenv("AZURE_AI_STUDIO_COHERE_COMMAND_KEY")  
AZURE_AI_STUDIO_COHERE_COMMAND_ENDPOINT = os.getenv("AZURE_AI_STUDIO_COHERE_COMMAND_ENDPOINT")  
SEARCH_SERVICE_API_KEY = os.getenv("SEARCH_SERVICE_API_KEY")  
SEARCH_SERVICE_ENDPOINT = os.getenv("SEARCH_SERVICE_ENDPOINT")  
MULTIBINARY_INDEX_NAME = os.getenv("MULTIBINARY_INDEX_NAME")  
MULTIINT8_INDEX_NAME = os.getenv("MULTIINT8_INDEX_NAME")  
  
# Initialize Cohere client  
co_chat = cohere.Client(  
    base_url=f"{AZURE_AI_STUDIO_COHERE_COMMAND_ENDPOINT}/v1",  
    api_key=AZURE_AI_STUDIO_COHERE_COMMAND_KEY  
)  
  
# Function to generate embeddings  
def generate_embeddings(texts, input_type="search_document", embedding_type="ubinary"):  
    model = "embed-multilingual-v3.0"  
    texts = [texts] if isinstance(texts, str) else texts  
    response = cohere.Client(  
        base_url=f"{AZURE_AI_STUDIO_COHERE_EMBED_ENDPOINT}/v1",  
        api_key=AZURE_AI_STUDIO_COHERE_EMBED_KEY  
    ).embed(  
        texts=texts,  
        model=model,  
        input_type=input_type,  
        embedding_types=[embedding_type],  
    )  
    return [embedding for embedding in getattr(response.embeddings, embedding_type)]  
  
# Function to perform vector search  
def perform_vector_search(query, search_client, embedding_type="ubinary"):  
    query_embeddings = generate_embeddings(query, input_type="search_query", embedding_type=embedding_type)  
    vector_query = VectorizableTextQuery(  
        text=query, k_nearest_neighbors=3, fields="embedding"  
    )  
    results = search_client.search(  
        search_text=None,  
        vector_queries=[vector_query],  
    )  
    return results  
  
# Initialize Azure Search Client  
azure_search_credential = AzureKeyCredential(SEARCH_SERVICE_API_KEY)  
ubinary_search_client = SearchClient(  
    endpoint=SEARCH_SERVICE_ENDPOINT,  
    credential=azure_search_credential,  
    index_name=MULTIBINARY_INDEX_NAME,  
)  
  
# Streamlit UI  
st.set_page_config(page_title="కోహియర్ ఏఐ సహాయకుడు", page_icon="🤖", layout="wide")  
  
# Add logo  
LOGO_URL = "./assets/cohererag.png"  # Replace with your logo URL  
LOGO2_URL = "./assets/coherelogo.png"  
st.logo(LOGO_URL, link="https://www.linkedin.com/in/vrajkishoreroutu/", icon_image=LOGO_URL)  
st.sidebar.image(LOGO2_URL, use_column_width=True)  
  
# Sidebar  
st.sidebar.title("సెట్టింగ్‌లు")  
  
# Add clear chat button  
if st.sidebar.button("కొత్త చాట్"):  
    st.session_state.messages = []  
    st.session_state.chat_history = []  
    st.session_state.example_clicked = False  
  
# Add a slider to control the temperature  
temperature = st.sidebar.slider(  
    "Temperature",  
    min_value=0.0,  
    max_value=1.0,  
    value=0.5,  
    step=0.1,  
    help="Controls randomness. Lowering the temperature means that the model will produce more repetitive and deterministic responses. Increasing the temperature will result in more unexpected or creative responses. Try adjusting temperature or Top P but not both.."  
)  
  
# Add a slider to control the temperature  
tokens = st.sidebar.slider(  
    "Max response",  
    min_value=0,  
    max_value=4096,  
    value=1000,  
    step=1,  
    help="Set a limit on the number of tokens per model response. The API supports a maximum of MaxTokensPlaceholderDoNotTranslate tokens shared between the prompt (including system message, examples, message history, and user query) and the model's response. One token is roughly 4 characters for typical English text.."  
)  
  
# File uploader  
uploaded_files = st.sidebar.file_uploader("Choose a file", accept_multiple_files=True)  
  
st.title("కోహియర్ ఏఐ సహాయకుడు")  
st.header('Sube y haz preguntas', divider='rainbow')  
  
# Example questions  
example_questions = [  
    "ノックノックジョークを始めてください 🤡",
    "운동을 위해 로드 바이크 🚴‍♂️ 나 마운틴 바이크 🚵‍♀️ 중 무엇을 사야 할까요?",
    "Was ist derzeit die beliebteste True-Crime-Serie im Streaming? 📺🔍",
    "Résumez les points principaux de la dernière recherche sur l'IA 🤖📝",
    "¿A dónde debería viajar si tengo alergias al polen? 🌼❌✈️",
]  
  
# Initialize chat history and example question state  
if "messages" not in st.session_state:  
    st.session_state.messages = []  
if "chat_history" not in st.session_state:  
    st.session_state.chat_history = []  
if "example_clicked" not in st.session_state:  
    st.session_state.example_clicked = False  
if "generated" not in st.session_state:  
    st.session_state.generated = []  
if "past" not in st.session_state:  
    st.session_state.past = []  
if "files_processed" not in st.session_state:  
    st.session_state.files_processed = False  
if "uploaded_file_names" not in st.session_state:  
    st.session_state.uploaded_file_names = []  
  
# Function to handle user input and generate response  
def handle_user_input(user_input):  
    st.session_state.messages.append({"role": "user", "content": user_input})  
    with st.chat_message("user", avatar=":material/person:"):  
        st.markdown(user_input)  
  
    # Perform vector search using binary embeddings  
    results_binary = perform_vector_search(user_input, ubinary_search_client, embedding_type="ubinary")  
    documents_binary = [{"text": result["text"]} for result in results_binary]  
  
    # Get chat response  
    chat_response_binary = co_chat.chat(  
        message=user_input,  
        documents=documents_binary,  
        max_tokens=tokens,  
        chat_history=[{"role": msg["role"].upper(), "text": msg["content"]} for msg in st.session_state.chat_history],  
        temperature=temperature  # Adjust the temperature as needed  
    )  
  
    response = chat_response_binary.text  
    with st.chat_message("assistant", avatar=":material/robot:"):  
        st.markdown(response)  
  
    st.session_state.messages.append({"role": "assistant", "content": response})  
  
# Function to handle example question click  
def handle_example_click(question):  
    st.session_state.example_clicked = True  
    handle_user_input(question)  
  
# Display example questions if none has been clicked  
if not st.session_state.example_clicked:  
    col1, col2, col3 = st.columns(3)  
    columns = [col1, col2, col3]  
  
    for i, question in enumerate(example_questions):  
        with columns[i % 3]:  
            if st.button(question):  
                handle_example_click(question)  
  
# Display chat history  
 
for message in st.session_state.messages:  
    with st.chat_message(message["role"], avatar=":material/person:" if message["role"] == "user" else ":material/robot:"):  
        st.markdown(message["content"])  
  
  
# Chat input at the bottom center  
prompt = st.chat_input("ఏముంది?")  
if prompt:  
    handle_user_input(prompt)  
  
# Check if new files are uploaded  
new_uploaded_file_names = [uploaded_file.name for uploaded_file in uploaded_files] if uploaded_files else []  
if new_uploaded_file_names != st.session_state.uploaded_file_names:  
    st.session_state.files_processed = False  
    st.session_state.uploaded_file_names = new_uploaded_file_names  
  
# Process uploaded files and index them  
if uploaded_files and not st.session_state.files_processed:  
    with st.spinner('Processing files...'):  
        try:  
            # Initialize Azure Search Index Client  
            search_index_client = SearchIndexClient(  
                endpoint=SEARCH_SERVICE_ENDPOINT,  
                credential=azure_search_credential  
            )  
  
            # Extract text from each PDF and store it in a list  
            documents = []  
            for uploaded_file in uploaded_files:  
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:  
                    tmp_file.write(uploaded_file.read())  
                    tmp_file_path = tmp_file.name  
                documents.append(extract_text_from_pdf(tmp_file_path))  
  
            # Create the "ubinary" index and generate embeddings  
            create_or_update_index(  
                search_index_client,  
                MULTIBINARY_INDEX_NAME,  
                "Collection(Edm.Byte)",  
                scoring_uri=AZURE_AI_STUDIO_COHERE_MULTIEMBED_ENDPOINT,  
                authentication_key=AZURE_AI_STUDIO_COHERE_MULTIEMBED_KEY,  
                model_name=AIStudioModelCatalogName.COHERE_EMBED_V3_MULTILINGUAL,  
            )  
            ubinary_embeddings = generate_embeddings(  
                documents,  
                input_type="search_document",  
                embedding_type="ubinary"  
            )  
            ubinary_search_client = SearchClient(  
                endpoint=SEARCH_SERVICE_ENDPOINT,  
                credential=azure_search_credential,  
                index_name=MULTIBINARY_INDEX_NAME,  
            )  
            index_documents(ubinary_search_client, documents, ubinary_embeddings)  
  
            # Create the "int8" index and generate embeddings  
            create_or_update_index(  
                search_index_client,  
                MULTIINT8_INDEX_NAME,  
                "Collection(Edm.SByte)",  
                scoring_uri=AZURE_AI_STUDIO_COHERE_EMBED_ENDPOINT,  
                authentication_key=AZURE_AI_STUDIO_COHERE_EMBED_KEY,  
                model_name=AIStudioModelCatalogName.COHERE_EMBED_V3_MULTILINGUAL,  
            )  
            int8_embeddings = generate_embeddings(  
                documents,  
                input_type="search_document",  
                embedding_type="int8"  
            )  
            int8_search_client = SearchClient(  
                endpoint=SEARCH_SERVICE_ENDPOINT,  
                credential=azure_search_credential,  
                index_name=MULTIINT8_INDEX_NAME,  
            )  
            index_documents(int8_search_client, documents, int8_embeddings)  
  
            st.success('Files processed and indexed successfully!')  
            st.session_state.files_processed = True  # Set the flag to True after successful processing  
        except Exception as e:  
            st.error(f'Failed to process files: {e}')  
            st.session_state.files_processed = False  # Ensure the flag is reset in case of failure  

