import streamlit as st
import base64
from clients.mongo_client import mongo_init
from clients.minio_client import MinioClientService
# Example list of PDFs with metadata
from streamlit_pdf_viewer import pdf_viewer

def listResume():
    st.title("📚 Resume Library")

    collection = mongo_init()
    minio = MinioClientService()
    if "resumes" not in st.session_state:
        st.session_state.resumes = list(collection.find())
    
    resumes = st.session_state.resumes
    
    
    for index, pdf_info in enumerate(resumes):
        # Load PDF

        # Metadata display
        max_experience = max(pdf_info['roles_experience'],key=lambda x:x['years_experience'])
        st.subheader(f"📄 {max_experience["role"]} : {max_experience["years_experience"]}  years of experience")
        st.write(f"**Author:** {pdf_info.get('full_name')}")
        st.write(f"**Overview:** {pdf_info['summary']}")

        pdf = minio.download_file(pdf_info["minio_file_name"])
        pdf_data = pdf.read()
        
        pdf_viewer(
            pdf_data,
            
            height=350
        )

        # Download button
        st.download_button(
            label="📥 Download PDF",
            data=pdf_data,
            file_name=f"{pdf_info["full_name"]}_{pdf_info['_id']}.pdf",
            mime='application/pdf',
            key=f"download_button_{index}"  # Ensure unique keys
        )

        st.markdown("---")
