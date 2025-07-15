import streamlit as st
import json
import os

from llm_client import extract_with_groq
from utils import clean_json , extract_resume_text
from mongo_client import mongo_init

# Streamlit UI
st.set_page_config(page_title="Resume Extractor (Groq LLaMA 3.3)", layout="wide")
st.title("📄 Resume Extractor using Groq LLaMA 3.3 and MongoDB")

uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)
collection = mongo_init()

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"Processing: {uploaded_file.name}")

        save_path = f"./temp_{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        resume_text = extract_resume_text(save_path)
        st.write("✅ **Extracted Resume Text:**")
        st.text_area("Resume Text", resume_text[:3000], height=300)

        with st.spinner("Extracting structured JSON using Groq LLaMA 3.3..."):
            try:
                extracted_json_raw = extract_with_groq(resume_text)
                print(f"\n{extracted_json_raw}\n")
                
                cleaned_json = clean_json(extracted_json_raw)
                
                try:
                    extracted_data = json.loads(cleaned_json)
                    # Store in MongoDB
                    try:
                        collection.insert_one(extracted_data)
                        st.success("🎉 Candidate profile saved to MongoDB!")
                        print("Added to mongo db")
                    except Exception as e:
                        st.error("Error adding to mongo"+ str(e))
                        print("Error"+str(e))

                except json.JSONDecodeError:
                    extracted_data = {
                        "error": "Groq model returned invalid JSON.",
                        "raw_output": extracted_json_raw
                    }

                st.write("🛠️ **Extracted Structured Data:**")
                st.json(extracted_data)
                st.divider()

            except Exception as e:
                st.error(f"Error: {str(e)}")

            finally:
                os.remove(save_path)
