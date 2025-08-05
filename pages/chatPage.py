import streamlit as st
from llms.groqClient import GroqClient
from llms.ollamaClient import OllamaClient
from services.llm_service import query_to_resume,text_to_mongo_query
from clients.mongo_client import mongo_candidat_init, get_skills_mongo
from clients.minio_client import MinioClientService
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)



def ChatPage():
    ollama_client = OllamaClient()
    groq_client = GroqClient()
    mongo_collection = mongo_candidat_init()
    minio_service = MinioClientService()
    dict_skills = get_skills_mongo()

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
            # if message["role"] == "assistant" and "resumes" in message:
            #     display_resumes(message["resumes"], minio_service)

    if question := st.chat_input("Enter your question"):
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state.messages.append({
            "role":"user",
            "content":question
            })
  
        with st.chat_message("assistant"):
            query = text_to_mongo_query(question, llm_client, dict_skills)
            st.write(query)
            resumes = query_to_resume(query,mongo_collection)
            st.session_state.messages.append(
                {"role":"assistant",
                 "content":query,
                 "resumes":resumes
                 }
                )
            
            display_resumes(resumes,minio_service)
           
    

def display_resumes(resumes, minio_service):
    index = 0
    found = False
    for resume in resumes:
        st.subheader(f"📄 Candidate {resume.get('full_name','') or ''} #{resume['_id']}")
        st.write(resume["summary"])
        pdf = minio_service.download_file(resume["minio_file_name"])
        pdf_data = pdf.read()
        st.download_button(
            label="📥 Download CV (PDF)",
            data=pdf_data,
            file_name=f"{resume['full_name']}_{resume['_id']}.pdf",
            mime='application/pdf',
            key=f"download_{index}"
        )
        index += 1
        logger.info(resume)
        found = True

    if not found:
        logger.warning("Aucun résultat trouvé.")


            
            