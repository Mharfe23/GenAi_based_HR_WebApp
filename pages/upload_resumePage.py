import streamlit as st
import json
import os

from utils import extract_resume_text
from clients.mongo_client import mongo_candidat_init, check_mongo_duplicate
import logging
from llms.ollamaClient import OllamaClient
from llms.groqClient import GroqClient
from services.llm_service import resume_to_json
from clients.minio_client import MinioClientService
from services.dictionaire_service import add_skill_if_new_and_replace_similar_ones, get_skills_mongo
logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def save_uploaded_file(uploaded_file):
    save_path = f"./temp_{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path


# Streamlit UI
def UploadPage():
    st.set_page_config(page_title="Resume Extractor (Groq LLaMA 3.3)", layout="wide")
    st.title("📄 Resume Extractor using Groq LLaMA 3.3 and MongoDB")


    ollama_client = OllamaClient()
    groq_client = GroqClient()
    minio_client = MinioClientService()
    existing_skills = get_skills_mongo()

    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

    llm_choice = st.radio("Choose LLM Client:",("Groq API llama3.3_70B","llama3.2 3B(local)"))
    match llm_choice:
        case "Groq API llama3.3_70B":
            st.session_state.llm_client = groq_client
        case "llama3.2 3B(local)":
            st.session_state.llm_client = ollama_client

    llm_client = st.session_state.llm_client
    collection = mongo_candidat_init()

    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name in st.session_state.processed_files:
                continue  # Skip already processed
            st.session_state.processed_files.add(uploaded_file.name)
            
            st.subheader(f"Processing: {uploaded_file.name}")

            try:
                file_path = save_uploaded_file(uploaded_file)
                resume_text = extract_resume_text(file_path)

            except Exception as e:
                st.error(str(e))
                logger.error("Error in extracting resume txt"+str(e))
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

            logger.info("**Extracted Resume Text:**")

            with st.spinner(f"Extracting structured JSON using {llm_client}..."):
                try:

                    cleaned_json = resume_to_json(resume_text, llm_client)
                    logger.info(f"\n{cleaned_json}\n")
                              
                    try:
                        extracted_data = json.loads(cleaned_json)
                        extracted_data["current_role_experience"] = max(extracted_data['roles_experience'], key=lambda r: r['years_experience'])
                        
                        ## Check if the email/full_name in mongo is a duplicate
                        if check_mongo_duplicate(email=extracted_data["email"], full_name=extracted_data["full_name"]):
                            st.warning(f"the email {extracted_data["email"]} or the name {extracted_data["full_name"]} already exists")
                            return
                        #Modify the resume data based on predefined skills
                        logger.debug(f"Extracted data BEFORE similarity replace :{extracted_data}")
                        add_skill_if_new_and_replace_similar_ones(extracted_data, existing_skills_set=existing_skills)
                        logger.debug(f"Extracted data AFTER similarity replace :{extracted_data}")

                    except json.JSONDecodeError:
                        extracted_data = {
                            "error": "Groq model returned invalid JSON.",
                            "raw_output": cleaned_json
                        }
                    try:
                        minio_filename = minio_client.upload_file(uploaded_file)
                        extracted_data["minio_file_name"] = minio_filename
                        collection.insert_one(extracted_data)
                        
                        st.success("🎉 Candidate profile saved to MongoDB!")
                        logger.info("Added to mongo db")
                    except Exception as e:
                        st.error("Error adding to mongo "+ str(e))
                        logger.exception("Error: "+str(e))


                    # st.write("🛠️ **Extracted Structured Data:**")
                    # st.json(extracted_data)
                    st.divider()

                except Exception as e:
                    st.error(f"Error: {str(e)}")

            

                
