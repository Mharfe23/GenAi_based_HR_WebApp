import streamlit as st
import json
import os

from utils import extract_resume_text
from clients.mongo_client import mongo_init
import logging

logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# Streamlit UI
st.set_page_config(page_title="Resume Extractor (Groq LLaMA 3.3)", layout="wide")
st.title("📄 Resume Extractor using Groq LLaMA 3.3 and MongoDB")

uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)
collection = mongo_init()

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"Processing: {uploaded_file.name}")

        try:
            save_path = f"./temp_{uploaded_file.name}"
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            resume_text = extract_resume_text(save_path)
        except Exception as e:
            st.error(str(e))
            logger.error("Error in extracting resume txt"+str(e))
        st.write("✅ **Extracted Resume Text:**")
        st.text_area("Resume Text", resume_text[:3000], height=300)

        with st.spinner("Extracting structured JSON using Groq LLaMA 3.3..."):
            try:
                cleaned_json = resume_to_json_with_groq(resume_text)
                logger.info(f"\n{cleaned_json}\n")
                                
                try:
                    extracted_data = json.loads(cleaned_json)
                    try:
                        collection.insert_one(extracted_data)
                        st.success("🎉 Candidate profile saved to MongoDB!")
                        logger.info("Added to mongo db")
                    except Exception as e:
                        st.error("Error adding to mongo "+ str(e))
                        logger.exception("Error: "+str(e))

                except json.JSONDecodeError:
                    extracted_data = {
                        "error": "Groq model returned invalid JSON.",
                        "raw_output": cleaned_json
                    }

                st.write("🛠️ **Extracted Structured Data:**")
                st.json(extracted_data)
                st.divider()

            except Exception as e:
                st.error(f"Error: {str(e)}")

        
            
