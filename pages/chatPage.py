import streamlit as st
from llms.groqClient import GroqClient
from llms.ollamaClient import OllamaClient
from services.resume_query_service import query_to_resume,text_to_mongo_query
from clients.mongo_client import mongo_init
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)



def ChatPage():
    ollama_client = OllamaClient()
    groq_client = GroqClient()
    mongo_collection = mongo_init()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.logo("./static/DXC_Logo.png",size="large")
    st.image("./static/DXC_Logo.png",width=120)
    st.title("HR Resume Assistant")

    llm_choice = st.radio("Choose LLM Client:",("Groq API llama3.3_70B","llama3.2 3B(local)"))

    match llm_choice:
        case "Groq API llama3.3_70B":
            llm_client = groq_client
        case "llama3.2 3B(local)":
            llm_client = ollama_client


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if question := st.chat_input("Enter your question"):
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state.messages.append({"role":"user","content":question})
  
        with st.chat_message("assistant"):
            query = text_to_mongo_query(question,llm_client)
            st.write(query)
            st.session_state.messages.append({"role":"assistant","content":query})
            resumes = query_to_resume(query,mongo_collection)
            found = False
            for resume in resumes:
                st.write(resume)
                logger.info(resume)
                found = True
            if not found:
                logger.warning("Aucun résultat trouvé.")
                st.write("Aucun resultat trouvé")

            st.write(resumes)
            st.session_state.messages.append({"role":"assistant","content":str(resumes)})
            