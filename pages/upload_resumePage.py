import streamlit as st
import json
import os
import tempfile
from typing import List, Dict, Any, Optional
import time

from utils import extract_resume_text
from clients.mongo_client import mongo_candidat_init, check_mongo_duplicate
import logging
from llms.ollamaClient import OllamaClient
from llms.groqClient import GroqClient
from services.llm_service import resume_to_json
from clients.minio_client import MinioClientService
from services.dictionaire_service import add_skill_if_new_and_replace_similar_ones, get_skills_mongo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .upload-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        text-align: center;
        margin: 2rem 0;
    }
    
    .processing-card {
        background: #ffffff;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
    }
    
    .success-card {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-card {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stats-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .feature-badge {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        display: inline-block;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_services():
    """Initialize and cache service connections"""
    try:
        ollama_client = OllamaClient()
        groq_client = GroqClient()
        minio_client = MinioClientService()
        collection = mongo_candidat_init()
        existing_skills = get_skills_mongo()
        
        logger.info("All services initialized successfully")
        return ollama_client, groq_client, minio_client, collection, existing_skills
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        st.error(f"Failed to initialize services: {e}")
        st.stop()

def save_uploaded_file_secure(uploaded_file) -> str:
    """Securely save uploaded file using temporary directory"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            return tmp_file.name
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise

def validate_extracted_data(extracted_data: Dict[str, Any]) -> bool:
    """Validate extracted resume data"""
    required_fields = ['email', 'full_name']
    
    for field in required_fields:
        if field not in extracted_data or not extracted_data[field]:
            return False
    
    return True

def display_extraction_preview(extracted_data: Dict[str, Any]) -> None:
    """Display a preview of extracted data"""
    if "error" in extracted_data:
        st.error("❌ Extraction failed")
        with st.expander("View raw output"):
            st.text(extracted_data.get("raw_output", "No output available"))
        return
    
    with st.expander("📋 Preview Extracted Data", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Personal Info**")
            st.write(f"**Name:** {extracted_data.get('full_name', 'N/A')}")
            st.write(f"**Email:** {extracted_data.get('email', 'N/A')}")
            st.write(f"**Phone:** {extracted_data.get('phone', 'N/A')}")
            st.write(f"**Location:** {extracted_data.get('location', 'N/A')}")
        
        with col2:
            st.markdown("**💼 Professional Info**")
            st.write(f"**Current Role:** {extracted_data.get('current_role', 'N/A')}")
            
            if 'current_role_experience' in extracted_data:
                current_exp = extracted_data['current_role_experience']
                st.write(f"**Experience:** {current_exp.get('years_experience', 'N/A')} years")
            
            # Skills preview
            if 'skills' in extracted_data and extracted_data['skills']:
                st.markdown("**🛠️ Top Skills:**")
                skills = extracted_data['skills'][:5]  # Show first 5 skills
                skills_html = ""
                for skill in skills:
                    skills_html += f'<span class="feature-badge">{skill}</span> '
                st.markdown(skills_html, unsafe_allow_html=True)

def process_single_file(uploaded_file, llm_client, collection, minio_client, existing_skills) -> Dict[str, Any]:
    """Process a single uploaded resume file"""
    result = {
        "success": False,
        "message": "",
        "data": None,
        "filename": uploaded_file.name
    }
    
    file_path = None
    
    try:
        # Save file securely
        file_path = save_uploaded_file_secure(uploaded_file)
        
        # Extract text from resume
        with st.spinner("📄 Extracting text from PDF..."):
            resume_text = extract_resume_text(file_path)
            
        if not resume_text.strip():
            result["message"] = "❌ No text could be extracted from the PDF"
            return result
        
        # Extract structured data using LLM
        with st.spinner("🤖 Analyzing resume with AI..."):
            cleaned_json = resume_to_json(resume_text, llm_client)
            
        # Parse JSON response
        try:
            extracted_data = json.loads(cleaned_json)
            
            # Add current role experience
            if 'roles_experience' in extracted_data and extracted_data['roles_experience']:
                extracted_data["current_role_experience"] = max(
                    extracted_data['roles_experience'], 
                    key=lambda r: r.get('years_experience', 0)
                )
            
        except json.JSONDecodeError as e:
            result["message"] = f"❌ Invalid JSON response from AI model: {str(e)}"
            result["data"] = {"error": "Invalid JSON", "raw_output": cleaned_json}
            return result
        
        # Validate extracted data
        if not validate_extracted_data(extracted_data):
            result["message"] = "❌ Missing required fields (name or email)"
            return result
        
        # Check for duplicates
        if check_mongo_duplicate(email=extracted_data["email"], full_name=extracted_data["full_name"]):
            result["message"] = f"⚠️ Duplicate found: {extracted_data['email']} or {extracted_data['full_name']} already exists"
            result["data"] = extracted_data
            return result
        
        # Process skills
        with st.spinner("🔍 Processing skills and matching..."):
            logger.debug(f"Extracted data BEFORE similarity replace: {extracted_data}")
            add_skill_if_new_and_replace_similar_ones(extracted_data, existing_skills_set=existing_skills)
            logger.debug(f"Extracted data AFTER similarity replace: {extracted_data}")
        
        # Upload to MinIO and save to MongoDB
        with st.spinner("💾 Saving to database..."):
            minio_filename = minio_client.upload_file(uploaded_file)
            extracted_data["minio_file_name"] = minio_filename
            extracted_data["upload_timestamp"] = time.time()
            
            collection.insert_one(extracted_data)
        
        result["success"] = True
        result["message"] = "✅ Resume processed and saved successfully!"
        result["data"] = extracted_data
        
        logger.info(f"Successfully processed {uploaded_file.name}")
        
    except Exception as e:
        logger.exception(f"Error processing {uploaded_file.name}: {e}")
        result["message"] = f"❌ Error processing file: {str(e)}"
        
    finally:
        # Clean up temporary file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary file {file_path}: {e}")
    
    return result

def display_upload_instructions():
    """Display upload instructions and tips"""
    st.markdown("""
    <div class="upload-zone">
        <h3>📁 Upload Resume Files</h3>
        <p>Drag and drop PDF files here or click to browse</p>
        <div style="margin-top: 1rem;">
            <span class="feature-badge">PDF Format</span>
            <span class="feature-badge">Multiple Files</span>
            <span class="feature-badge">AI Processing</span>
            <span class="feature-badge">Auto-extraction</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_processing_stats(processed_count: int, total_count: int, success_count: int):
    """Display processing statistics"""
    if total_count > 0:
        progress = processed_count / total_count
        st.progress(progress, text=f"Processing: {processed_count}/{total_count} files")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", total_count)
        with col2:
            st.metric("Processed", processed_count)
        with col3:
            st.metric("Successful", success_count)

def UploadPage():
    """Main upload page function"""
    # Page configuration
    st.set_page_config(
        page_title="Resume Extractor & Analyzer",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize services
    ollama_client, groq_client, minio_client, collection, existing_skills = initialize_services()
    
    # Initialize session state
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = []
    
    # Header
    st.markdown('<h1 class="upload-header">📄 Resume Extractor & Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Resume Processing with Advanced Data Extraction</p>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # LLM selection
        llm_choice = st.radio(
            "Choose AI Model:",
            ("Groq API llama3.3_70B", "llama3.2 3B(local)"),
            help="Select the AI model for resume analysis"
        )
        
        # Set LLM client
        llm_client = groq_client if llm_choice == "Groq API llama3.3_70B" else ollama_client
        st.session_state.llm_client = llm_client
        
        st.divider()
        
        # Processing options
        st.markdown("### 🔧 Processing Options")
        show_preview = st.checkbox("Show data preview", value=True, help="Display extracted data preview")
        
        st.divider()
        
        # Statistics
        if st.session_state.processing_results:
            st.markdown("### 📊 Session Stats")
            total_files = len(st.session_state.processing_results)
            successful_files = len([r for r in st.session_state.processing_results if r["success"]])
            
            st.metric("Files Processed", total_files)
            st.metric("Successful", successful_files)
            st.metric("Success Rate", f"{(successful_files/total_files)*100:.1f}%" if total_files > 0 else "0%")
        
        # Clear session button
        if st.button("🗑️ Clear Session", use_container_width=True):
            st.session_state.processed_files = set()
            st.session_state.processing_results = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Upload instructions
        display_upload_instructions()
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF resume files for processing"
        )
        
        # Process files
        if uploaded_files:
            process_uploaded_files(uploaded_files, llm_client, collection, minio_client, existing_skills, show_preview)
    
    with col2:
        # Display processing results summary
        if st.session_state.processing_results:
            st.markdown("### 📋 Processing Summary")
            
            for result in st.session_state.processing_results[-5:]:  # Show last 5 results
                if result["success"]:
                    st.markdown(f"""
                    <div class="success-card">
                        <strong>✅ {result['filename']}</strong><br>
                        {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if "Duplicate" in result["message"]:
                        st.markdown(f"""
                        <div class="warning-card">
                            <strong>⚠️ {result['filename']}</strong><br>
                            {result['message']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="error-card">
                            <strong>❌ {result['filename']}</strong><br>
                            {result['message']}
                        </div>
                        """, unsafe_allow_html=True)

def process_uploaded_files(uploaded_files: List, llm_client, collection, minio_client, existing_skills, show_preview: bool):
    """Process multiple uploaded files"""
    new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
    
    if not new_files:
        st.info("All selected files have already been processed in this session.")
        return
    
    # Display processing stats
    total_files = len(new_files)
    processed_count = 0
    success_count = 0
    
    # Process each file
    for uploaded_file in new_files:
        st.session_state.processed_files.add(uploaded_file.name)
        
        # Processing card
        st.markdown(f"""
        <div class="processing-card">
            <h4>🔄 Processing: {uploaded_file.name}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Process the file
        result = process_single_file(uploaded_file, llm_client, collection, minio_client, existing_skills)
        
        # Store result
        st.session_state.processing_results.append(result)
        
        # Display result
        if result["success"]:
            st.success(result["message"])
            success_count += 1
            
            if show_preview and result["data"]:
                display_extraction_preview(result["data"])
                
        else:
            if "Duplicate" in result["message"]:
                st.warning(result["message"])
                if show_preview and result["data"]:
                    display_extraction_preview(result["data"])
            else:
                st.error(result["message"])
        
        processed_count += 1
        
        # Update progress
        display_processing_stats(processed_count, total_files, success_count)
        
        st.divider()
    
    # Final summary
    if processed_count > 0:
        st.markdown(f"""
        <div class="stats-container">
            <h4>📈 Batch Processing Complete</h4>
            <p><strong>Total:</strong> {total_files} files | <strong>Successful:</strong> {success_count} | <strong>Failed:</strong> {processed_count - success_count}</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    UploadPage()