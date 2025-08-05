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

from typing import List, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="HR Resume Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_clients():
    """Initialize and cache client connections"""
    try:
        ollama_client = OllamaClient()
        groq_client = GroqClient()
        mongo_collection = mongo_candidat_init()
        minio_service = MinioClientService()
        dict_skills = get_skills_mongo()
        
        logger.info("All clients initialized successfully")
        return ollama_client, groq_client, mongo_collection, minio_service, dict_skills
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        st.error(f"Failed to initialize services: {e}")
        st.stop()

def display_resumes(resumes: List[Dict[str, Any]], minio_service: MinioClientService) -> None:
    """Display resume results with enhanced formatting"""
    if not resumes:
        st.warning("🔍 No resumes found matching your criteria.")
        return
    
    st.success(f"✅ Found {len(resumes)} matching candidate(s)")
    
    # Create columns for better layout
    for i, resume in enumerate(resumes):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Candidate header
                st.markdown(f"### 👤 {resume.get('full_name', 'Unknown')} #{resume['_id']}")
                
                # Summary
                if resume.get('summary'):
                    st.markdown("**Summary:**")
                    st.write(resume['summary'])
                
                # Experience (if available)
                if resume.get('experience_years'):
                    st.markdown(f"**Experience:** {resume['experience_years']} years")
            
            with col2:
                # Download button
                try:
                    pdf = minio_service.download_file(resume["minio_file_name"])
                    pdf_data = pdf.read()
                    
                    st.download_button(
                        label="📥 Download CV",
                        data=pdf_data,
                        file_name=f"{resume.get('full_name', 'candidate')}_{resume['_id']}.pdf",
                        mime='application/pdf',
                        key=f"download_{resume['_id']}",
                        use_container_width=True
                    )
                except Exception as e:
                    logger.error(f"Failed to prepare download for {resume['_id']}: {e}")
                    st.error("❌ Download unavailable")
            
            st.divider()

def display_query_info(query: str) -> None:
    """Display the generated MongoDB query in an expandable section"""
    with st.expander("🔍 View Generated Query", expanded=False):
        try:
            # Try to parse and format as JSON if it's a valid JSON string
            if query.strip().startswith('{'):
                formatted_query = json.dumps(json.loads(query), indent=2)
                st.code(formatted_query, language='json')
            else:
                st.code(query, language='text')
        except json.JSONDecodeError:
            st.code(query, language='text')

def clear_chat_history():
    """Clear chat history"""
    st.session_state.messages = []
    st.rerun()

def ChatPage():
    """Main chat page function"""
    # Initialize clients
    ollama_client, groq_client, mongo_collection, minio_service, dict_skills = initialize_clients()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar configuration
    with st.sidebar:
        
        st.title("⚙️ Configuration")
        
        # LLM selection
        llm_choice = st.radio(
            "Choose LLM Client:",
            ("Groq API llama3.3_70B", "llama3.2 3B(local)"),
            help="Select the language model for query processing"
        )
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            clear_chat_history()
        
        # Statistics
        if st.session_state.messages:
            st.markdown("---")
            st.markdown("📊 **Chat Statistics**")
            user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            st.metric("Questions Asked", user_messages)
    
    # Main page header
    st.title("🤖 HR Resume Assistant")
    st.markdown("Ask questions about candidates and get relevant resume matches!")
    
    # Select LLM client
    llm_client = groq_client if llm_choice == "Groq API llama3.3_70B" else ollama_client
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                # Assistant message
                st.write("**Generated Query:**")
                display_query_info(message["content"])
                
                if "resumes" in message:
                    logger.debug(f"Displaying {len(message['resumes'])} saved resumes")
                    display_resumes(message["resumes"], minio_service)

    # Chat input
    if question := st.chat_input("Ask about candidates (e.g., 'i want a developer with 5+ years of experience')"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(question)
        
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Process and display assistant response
        with st.chat_message("assistant"):
            try:
                with st.spinner("🔄 Processing your query..."):
                    # Generate MongoDB query
                    query = text_to_mongo_query(question, llm_client, dict_skills)
                    
                    st.write("**Generated Query:**")
                    display_query_info(query)
                    
                    # Execute query and get resumes
                    resumes = query_to_resume(query, mongo_collection)
                    resumes_list = list(resumes)
                    
                    # Display results
                    display_resumes(resumes_list, minio_service)
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": query,
                        "resumes": resumes_list
                    })
                    
                    logger.info(f"Query processed successfully. Found {len(resumes_list)} results.")
                    
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                st.error(f"❌ An error occurred while processing your query: {str(e)}")
